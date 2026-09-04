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
- Each nonblank line in `<routes>` is a Markdown list item containing one path.
- Route paths are always relative to the router declaring them, with or without a leading `@` — a
  router never needs to know where the graph root lives to declare its own routes.
- Every route target must exist.

A route target that isn't a router portal name is a leaf. Leaves need no frontmatter. A leaf may
optionally declare `type: reference` with an `owners:` list; if it does, every declared owner must
exist. A reference does not need to route back to its owner, and does not need to be routed to by
anything in order to be valid — the check only runs for references a router actually points at.
References use the same limited frontmatter format as routers (single-line fields and indented
lists). Malformed or unsupported reference frontmatter is reported as an error; it does not
disable owner validation silently. Ordinary leaves do not have their metadata validated.

## Ownership

Ownership is explicit, direct, and non-transitive.

For every router-to-router edge `A -> B`, `B.owners` must name `A`. A router may name multiple
owners, but every named owner must exist, must be a router, and must directly route to the owned
router. An ancestor does not own its descendants merely because a route path exists through an
intermediate router.

The validator checks declarations in both directions. It never infers missing owners.

Owner paths resolve differently from route paths, because an owner points outward toward an
ancestor that may live anywhere in the graph: a leading `@` anchors to the graph root's directory,
regardless of how deeply the declaring file is nested; a plain path is relative to the file
declaring the owner, same as a route.

## Validation behavior

Validation is graph-wide and diagnostic:

- discover every router reachable from the selected root;
- continue after failures;
- print every error with its file;
- exit non-zero if any error exists.

Concept and tag ownership are deliberately outside this first contract. Owners are router paths.
