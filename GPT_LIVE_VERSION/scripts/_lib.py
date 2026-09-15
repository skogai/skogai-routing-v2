"""Shared parsing helpers for SkogAI routing commands."""

import re
from collections.abc import Mapping
from typing import Any

import yaml

_FRONTMATTER = re.compile(r"\A---[ \t]*\n(?P<body>.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)
_STANDALONE_TAG = re.compile(r"<(?P<closing>/)?(?P<name>[A-Za-z][A-Za-z0-9_-]*)(?P<attrs>\s[^>]*)?>")


class FrontmatterParseError(ValueError):
    pass


class RouterBodyParseError(ValueError):
    pass


def parse_frontmatter(text: str) -> dict[str, Any] | None:
    match = _FRONTMATTER.match(text)
    if match is None:
        return None
    try:
        value = yaml.safe_load(match.group("body"))
    except yaml.YAMLError as error:
        raise FrontmatterParseError(str(error)) from error
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise FrontmatterParseError("frontmatter must be a YAML mapping")
    return dict(value)


def is_router(frontmatter: Mapping[str, Any] | None) -> bool:
    return bool(frontmatter) and frontmatter.get("type") == "router"


def parse_routes(text: str) -> list[str]:
    frontmatter = _FRONTMATTER.match(text)
    if frontmatter is None:
        raise RouterBodyParseError("frontmatter must precede the routes block")
    lines = text[frontmatter.end():].splitlines()
    tags: list[tuple[int, re.Match[str]]] = []
    fence: str | None = None
    for number, line in enumerate(lines):
        stripped = line.strip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith(("```", "~~~")):
            fence = stripped[:3]
            continue
        match = _STANDALONE_TAG.fullmatch(stripped)
        if match is not None:
            tags.append((number, match))
    if len(tags) != 2:
        raise RouterBodyParseError("body must contain one <routes>...</routes> block and no other XML blocks")
    (start, opening), (end, closing) = tags
    valid_pair = (
        opening.group("name") == "routes"
        and opening.group("closing") is None
        and opening.group("attrs") is None
        and closing.group("name") == "routes"
        and closing.group("closing") == "/"
        and closing.group("attrs") is None
        and start < end
    )
    if not valid_pair:
        raise RouterBodyParseError("routes tags must be an attribute-free opening and closing pair on separate lines")
    entries: list[str] = []
    for offset, line in enumerate(lines[start + 1:end], start=start + 2):
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("- ") or not stripped[2:].strip():
            raise RouterBodyParseError(f"routes line {offset} must be a nonempty Markdown list entry")
        entries.append(stripped[2:].strip())
    return entries
