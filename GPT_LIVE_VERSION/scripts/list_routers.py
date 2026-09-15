#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""List Markdown files whose frontmatter declares type: router."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._lib import FrontmatterParseError, is_router, parse_frontmatter  # noqa: E402

SKIP_DIRS = {".git", "node_modules"}


def find_routers(root: Path):
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        try:
            if is_router(parse_frontmatter(path.read_text())):
                yield relative
        except (FrontmatterParseError, OSError, UnicodeDecodeError):
            continue


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    lines = [str(path) for path in find_routers(root)]
    print("\n".join(lines))
    if args.output:
        Path(args.output).write_text("\n".join(lines) + ("\n" if lines else ""))


if __name__ == "__main__":
    main()
