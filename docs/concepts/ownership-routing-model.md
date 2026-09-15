---
title: ownership-routing-model
type: note
permalink: skogai-routing/docs/concepts/ownership-routing-model
---

# Ownership / routing model (raw dictation, for handover)

Captured verbatim from user in chat on 2026-08-22. Not yet reconciled with existing `skogai-routing` v1 implementation (`validate_router.py`, `list_routers.py`, `router.schema.json`) — treat as a separate concept proposal until someone deliberately maps it onto or replaces that tooling.

## Original statement

> 1. files have one or more concepts, tags, names, files, whatever as their "owner", "parent" or things it belongs to.
> 1. "concepts" or named things will "own", "have responsibility over" or "manage" other files or tags
> 1. a `caps file`, i.e. SKOGAI, AGENT, MEMORY, HISTORY, SPECS, WHATEVER.md are routing files and are meant to be in context and link, reference and inject further context by being a "choice portal"
> 1. these routing files are often the owners of a concept, idea or module in a project. ./CLAUDE.md might have a lot of files it manages, including ./project/MEMORY.md which in turn describe the smaller memory fragments, what they mean and where to find them
> 1. the chain of ownership stops at one level deep at all times. this makes each managed file either a "leaf" which ends the chain or a routing file which have its own children
>
> a. a file _must_ have a owner or parent it belongs to b. the only exception is the root router. the "git root intro agent file" - most often `{CLAUDE,AGENT,SKOGAI}.md` c. the intro agent file is managed by the project itself. i.e. `permalink: myproject/CLAUDE` would mean myproject is responsible for the root CLAUDE.md file and that is how the routing and references will be followed and used

## Explicit correction to a misreading

Assistant initially collapsed rule 1 to "one owner per file, mandatory." Wrong. A file/concept/tag can belong to **one or more** owners/parents — multiplicity is allowed, not just a single-parent tree.

## Explicit correction on a false lead

Assistant treated `skills/skogai-architecture-example/references/ownership.toml` as if it were a real, load-bearing artifact needing to be wired up (pointing at real router files, fixing its paths, etc.). User: that file does not exist as a real thing — it's example/concept material, not the spec. Don't design against its literal contents.

## Explicit correction on scope

Assistant kept invoking `validate_router.py` / `list_routers.py` (the existing `skogai-routing` v1 tooling) as though they already implement or constrain this model. They don't — they validate a narrower, different schema (single `type: router` frontmatter + one `<routes>` block, one document at a time). This ownership/chain model is a distinct proposal and should not be assumed compatible with that tooling until someone checks.

## Open, unresolved (not decided by user yet)

- Whether/how this model maps onto or replaces the current v1 `type: router` / `<routes>` schema.
- What multiplicity of ownership means for the "chain stops one level deep" rule (5) — e.g. does a file with two owners appear once in each owner's local chain, independently?
- What `skogai-architecture-example` is actually for, if not literally wired to this model via `ownership.toml`.
