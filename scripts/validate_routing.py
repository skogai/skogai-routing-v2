#!/usr/bin/env python3
"""Validate a SkogAI routing v2 graph without third-party dependencies."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PORTAL_NAME = re.compile(r"^[A-Z][A-Z0-9_-]*\.md$")
ROUTES_BLOCK = re.compile(r"(?ms)^<routes>\s*$\n(.*?)^</routes>\s*$")
LIST_ROUTE = re.compile(r"^\s*-\s+(@?[^\s]+)(?:\s+-\s+.*)?\s*$")


@dataclass
class Router:
    path: Path
    permalink: str
    owners: list[str]
    routes: list[str]


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("missing YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("unterminated YAML frontmatter") from exc

    data: dict[str, object] = {}
    active_list: str | None = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s+-\s+(.+?)\s*$", raw)
        if item and active_list:
            value = data.setdefault(active_list, [])
            assert isinstance(value, list)
            value.append(item.group(1))
            continue
        field = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$", raw)
        if not field:
            raise ValueError(f"unsupported frontmatter line: {raw!r}")
        key, value = field.groups()
        if value:
            data[key] = value
            active_list = None
        else:
            data[key] = []
            active_list = key
    return data, "\n".join(lines[end + 1 :])


def parse_router(path: Path) -> Router:
    data, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    if data.get("type") != "router":
        raise ValueError("frontmatter type must be 'router'")
    permalink = data.get("permalink")
    if not isinstance(permalink, str) or not permalink.strip():
        raise ValueError("permalink must be a non-empty string")
    owners = data.get("owners", [])
    if not isinstance(owners, list) or not all(isinstance(owner, str) for owner in owners):
        raise ValueError("owners must be a list of paths")
    blocks = list(ROUTES_BLOCK.finditer(body))
    if len(blocks) != 1:
        raise ValueError("body must contain exactly one attribute-free <routes> block")
    routes: list[str] = []
    for line in blocks[0].group(1).splitlines():
        if not line.strip():
            continue
        match = LIST_ROUTE.match(line)
        if not match:
            raise ValueError(f"invalid route entry: {line!r}")
        routes.append(match.group(1))
    return Router(path=path, permalink=permalink, owners=owners, routes=routes)


def resolve_route(source: Path, value: str) -> Path:
    """Route targets are always relative to the router declaring them — a router
    never needs to know where the graph root lives, `@` included."""
    target = value[1:] if value.startswith("@") else value
    return (source.parent / target).resolve()


def resolve_owner(source: Path, value: str, project_root: Path) -> Path:
    """Owners point outward/upward to an ancestor, which may live anywhere in the
    graph, so `@` here still anchors to the graph root; plain paths are relative
    to the file declaring the owner."""
    if value.startswith("@"):
        return (project_root / value[1:]).resolve()
    return (source.parent / value).resolve()


def check_reference_owners(path: Path, project_root: Path) -> list[str]:
    """A leaf may declare `type: reference` with `owners:`. All that's required is
    that each declared owner exists — it need not route back, and the reference
    itself need not be routed to in order to be valid."""
    try:
        data, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return []
    if data.get("type") != "reference":
        return []
    owners = data.get("owners", [])
    if not isinstance(owners, list) or not all(isinstance(owner, str) for owner in owners):
        return [f"{path}: owners must be a list of paths"]
    errors = []
    for owner in owners:
        if not resolve_owner(path, owner, project_root).exists():
            errors.append(f"{path}: reference owner does not exist: {owner}")
    return errors


def validate(root_file: Path) -> list[str]:
    root_file = root_file.resolve()
    project_root = root_file.parent
    errors: list[str] = []
    routers: dict[Path, Router] = {}
    checked_references: set[Path] = set()
    queue = [root_file]

    while queue:
        path = queue.pop(0)
        if path in routers:
            continue
        if not path.is_file():
            errors.append(f"{path}: router does not exist")
            continue
        try:
            router = parse_router(path)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{path}: {exc}")
            continue
        routers[path] = router
        if not PORTAL_NAME.fullmatch(path.name):
            errors.append(f"{path}: router filename must be an uppercase portal name")
        for route in router.routes:
            target = resolve_route(path, route)
            if not target.exists():
                errors.append(f"{path}: route target does not exist: {route}")
            elif not target.is_file():
                continue
            elif PORTAL_NAME.fullmatch(target.name):
                queue.append(target)
            elif target not in checked_references:
                checked_references.add(target)
                errors.extend(check_reference_owners(target, project_root))

    root = routers.get(root_file)
    if root and root.owners:
        errors.append(f"{root_file}: graph root must not declare owners")

    for path, router in routers.items():
        if path != root_file and not router.owners:
            errors.append(f"{path}: non-root router must declare at least one owner")
        direct_router_targets = {
            resolve_route(path, route)
            for route in router.routes
            if resolve_route(path, route) in routers
        }
        for target in direct_router_targets:
            child = routers[target]
            owner_paths = {resolve_owner(target, owner, project_root) for owner in child.owners}
            if path not in owner_paths:
                errors.append(f"{target}: route from {path} is missing from owners")

        for owner in router.owners:
            owner_path = resolve_owner(path, owner, project_root)
            owner_router = routers.get(owner_path)
            if owner_router is None:
                errors.append(f"{path}: owner is not a reachable router: {owner}")
                continue
            owner_targets = {resolve_route(owner_path, route) for route in owner_router.routes}
            if path not in owner_targets:
                errors.append(f"{path}: owner does not directly route to this router: {owner}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path, help="root SKOGAI.md file(s)")
    args = parser.parse_args()
    failed = False
    for root in args.roots:
        errors = validate(root)
        if errors:
            failed = True
            print(f"FAIL {root}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {root}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

