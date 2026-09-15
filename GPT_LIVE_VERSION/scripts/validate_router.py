#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate one or more SkogAI v1 router documents."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._lib import FrontmatterParseError, RouterBodyParseError, parse_frontmatter, parse_routes  # noqa: E402

ALLOWED_FIELDS = {"type", "permalink"}


def validate_file(path: Path) -> int:
    try:
        raw = path.read_text()
    except (OSError, UnicodeDecodeError) as error:
        print(f"FAIL  {path}")
        print(f"      file: {error}")
        return 1
    try:
        frontmatter = parse_frontmatter(raw)
        if frontmatter is None:
            raise FrontmatterParseError("missing YAML frontmatter")
        if frontmatter.get("type") != "router":
            raise FrontmatterParseError("type must equal 'router'")
        unknown = sorted(set(frontmatter) - ALLOWED_FIELDS)
        if unknown:
            raise FrontmatterParseError(f"unsupported fields: {', '.join(unknown)}")
        permalink = frontmatter.get("permalink")
        if permalink is not None and (not isinstance(permalink, str) or not permalink.strip()):
            raise FrontmatterParseError("permalink must be a nonempty string")
        parse_routes(raw)
    except FrontmatterParseError as error:
        print(f"FAIL  {path}")
        print(f"      frontmatter: {error}")
        return 1
    except RouterBodyParseError as error:
        print(f"FAIL  {path}")
        print(f"      body: {error}")
        return 1
    print(f"PASS  {path}")
    return 0


def main() -> None:
    if not sys.argv[1:]:
        print("Usage: validate_router.py <file> [file...]", file=sys.stderr)
        raise SystemExit(1)
    failed = False
    for arg in sys.argv[1:]:
        failed = bool(validate_file(Path(arg))) or failed
    raise SystemExit(failed)


if __name__ == "__main__":
    main()
