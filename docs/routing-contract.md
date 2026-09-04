# SkogAI Routing v2 Contract

## Purpose

A router is a choice portal. It names the context that may be loaded next; it does not load an
entire subtree or imply ownership beyond the routes it declares.

## Router shape

Routers are Markdown files with YAML frontmatter and exactly one attribute-free `<routes>` block.

```markdown
---
permalink: project/skogai
type: router
owners:
  - @SKOGAI.md
---

<routes>

- @docs/routing-contract.md - the routing contract

</routes>
```

Rules:

- `type` must be `router`.
- `permalink` is required and must be non-empty.
- `owners` is a non-empty list of router paths for every router except the graph root.
- The graph root is the `SKOGAI.md` passed to the validator and must not declare an owner.
- Router portal filenames use uppercase letters, digits, `_`, and `-`, with a `.md` suffix.
- Portal-shaped filenames are reserved for routers; `type: reference` documents should use
  lowercase filenames.
- Each nonblank line in `<routes>` is a Markdown list item containing one path.
- `@` marks a project-relative path. Plain paths are relative to the router containing the route.
- Every route target must exist.

## Ownership

Ownership is explicit, direct, and non-transitive.

For every router-to-router edge `A -> B`, `B.owners` must name `A`. A router may name multiple
owners, but every named owner must exist, must be a router, and must directly route to the owned
router. An ancestor does not own its descendants merely because a route path exists through an
intermediate router.

The validator checks declarations in both directions. It never infers missing owners.

## Validation behavior

Validation is graph-wide and diagnostic:

- discover every router reachable from the selected root;
- continue after failures;
- print every error with its file;
- exit non-zero if any error exists.

Concept and tag ownership are deliberately outside this first contract. Owners are router paths.
