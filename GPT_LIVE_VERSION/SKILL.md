---
name: skogai-routing
description: Create, read, discover, and validate SkogAI router documents such as SKOGAI.md and compatible project instruction routers. Use when a task mentions SkogAI routing, router frontmatter, routes XML blocks, route inventories, @-linked context files, or checking whether routing documents follow the v1 convention.
permalink: skogai-routing/gpt-live-version/skill
---

# SkogAI Routing

Treat a v1 router as a Markdown document containing YAML frontmatter followed by exactly one attribute-free `<routes>...</routes>` block.

Read `references/router-file-convention.md` when exact document-shape or route-entry guidance is needed.

## Validate routers

1. Resolve every explicit file or discover candidates with `scripts/list_routers.py [root]`.
1. Run `scripts/validate_router.py <file...>`.
1. Report one PASS or FAIL result per file and preserve each failure reason.
1. Do not repair invalid routers unless the user asks.

The scripts use inline `uv` dependencies and require `uv` on `PATH`.

## Discover routers

Run `scripts/list_routers.py [root]` to recursively find Markdown files whose frontmatter contains `type: router`. Discovery skips `.git`, `node_modules`, malformed frontmatter, and unreadable files. It identifies candidates; it does not prove that they are valid.

If both discovery and validation are requested, pass every discovered path to the validator.

## Create a router

1. Start from `examples/valid/SKOGAI.md`.
1. Keep `type: router` and set a stable `permalink` when one is known.
1. Add only routes justified by the project or explicitly requested by the user.
1. Validate the completed file before reporting success.

Do not invent future document types. V1 implements only `type: router` paired with `<routes>`.
