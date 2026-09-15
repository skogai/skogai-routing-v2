---
title: 01016555-handoffskogairoutingv1removal
type: note
permalink: skogai-routing/01016555-handoffskogairoutingv1removal
---

# Handoff: skogai-routing v1 removal / ownership-model pivot

Generated: 2026-08-22T11:34:33Z
Repo: skogai-routing (git@github.com:skogai/skogai-routing.git)
Working copy this session: /home/skogix/.local/src/skogai-routing/.claude/worktrees/lazy-stargazing-canyon
Branch: worktree-lazy-stargazing-canyon (pushed to origin, tracking set up)

## What happened this session

User is starting a big rework: replacing the current "v1 router"
(`skogai-routing` skill: `type: router` frontmatter + `<routes>` XML block,
validated by `validate_router.py`/`list_routers.py`) with a new
ownership/routing model still in planning. User asked to remove everything
in the repo connected to v1 while the new model is designed.

Confirmed scope with user via AskUserQuestion, then removed on this branch:

- `skills/skogai-routing/` (whole skill: SKILL.md, schemas, scripts, refs, examples)
- `agents/route-guide.md`
- `.claude-plugin/` (plugin.json, marketplace.json) — deleted entirely, not gutted-to-shell
- `pyproject.toml`, `uv.lock`, `tests/` — deleted entirely (Python tooling existed only to test the v1 scripts)
- Root `SKOGAI.md`, `AGENTS.md`, `CLAUDE.md` — each was pure v1-router shape
  (frontmatter + one `<routes>` entry pointing at `SKOGAI.md`), so deleted
  rather than emptied
- Stale `.gitignore` entries referencing the deleted `skills/skogai-routing/scripts/__pycache__` and `tests/__pycache__` paths

Left untouched: `.old/` — a *different*, already-superseded pre-v1 routing
framework (broader doc types: workflow/reference/template/lesson). It is not
v1 router and was explicitly out of scope.

Result: 37 files deleted, 3064 lines removed. Committed as `8214445` on
`worktree-lazy-stargazing-canyon`, pushed to origin. No PR opened yet — that's
the user's call.

## Important unresolved issue: branch divergence

This worktree's branch forked from commit `7f4835d` ("plugins"). There is a
**sibling** commit line (`5444a0f` merge → `3fb5fce` "docs: capture raw
ownership/routing model dictation for handover" → `f510fc8` "Add
skogai-architecture skill with records tooling") that this branch never
received. That means:

- `docs/concepts/ownership-routing-model.md` (the actual planning doc for the
  new model — see below) does **not exist** in this branch's history.
- It only exists as an on-disk file in the user's separate checkout at
  `/home/skogix/dev/skogai-routing/remodeling` (local branch `remodeling`,
  currently sitting at `7f4835d` — one commit behind `3fb5fce` — meaning the
  doc file there is uncommitted/untracked, not safely on any branch).
- The `skogai-architecture` skill added in `f510fc8` is also not present on
  this branch.

**Before continuing the rework, figure out the right base branch** and either
rebase/cherry-pick this removal onto it, or bring the doc + architecture
skill onto this branch — otherwise the v1 removal and the new-model planning
doc end up permanently split across branches.

## The new model (source of truth, don't duplicate here)

Read directly: `docs/concepts/ownership-routing-model.md` (currently only
findable via the `remodeling` checkout — see divergence issue above). Summary
of what's decided vs. open, so you know what NOT to re-litigate:

- Decided: multiplicity of ownership is allowed (a file/concept can have more
  than one owner — earlier assistant misread this as single-parent tree, user
  corrected it).
- Decided: `skills/skogai-architecture-example/references/ownership.toml` is
  NOT a real/load-bearing spec artifact — don't design against its literal
  contents.
- Decided: current v1 tooling (`validate_router.py`/`list_routers.py`) does
  NOT already implement or constrain this new model — separate proposal.
- Open/undecided: whether/how this model maps onto or replaces v1's `type:
  router`/`<routes>` schema; what multiplicity means for the "chain stops one
  level deep" rule; what `skogai-architecture-example` is actually for.

## Suggested skills for next session

- **skogai-routing:skogai-routing** (or its post-removal successor, once
  written) — this repo's own meta-skill for authoring/validating router
  files; check whether it should be rewritten from scratch against the new
  model rather than resurrected as-is.
- **domain-modeling** — the ownership/routing model is fundamentally a
  domain-modeling exercise (terminology: "owner", "parent", "caps file",
  "choice portal", "leaf") before it's a schema; use this to pin down
  vocabulary and possibly produce a CONTEXT.md/ADR.
- **spec-driven-development** or **design-doc-and-task-board** — the open
  questions listed above need to be resolved and captured somewhere durable
  before implementation starts; pick whichever this repo's conventions favor.
- **git-workflow-and-versioning** — needed immediately to sort out the branch
  divergence issue before doing more work on either line.
- **documentation-and-adrs** — once the open questions are resolved, record
  the decision (router v1 removal + new model shape) as an ADR so it doesn't
  get re-litigated again.

## Environment notes

- Working in a git worktree (`.claude/worktrees/lazy-stargazing-canyon`),
  isolated from the user's other checkouts. It has its own branch and has
  been pushed; nothing here affects `/home/skogix/dev/skogai-routing/remodeling`
  or any other checkout.
- No PR opened for `worktree-lazy-stargazing-canyon` — open one once the base
  branch question above is settled, so it merges onto the right target.