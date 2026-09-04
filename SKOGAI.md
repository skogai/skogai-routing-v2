---
permalink: skogai-routing-v2/root
type: router
---

<routes>

- @docs/routing-contract.md - v2 graph and ownership contract
- scripts/validate_routing.py - graph validator
- tests/test_validate_routing.py - validator behavior
- @tests/fixtures/ - valid and invalid example graphs

</routes>

<rules>

Each rule below is enforced by `scripts/validate_routing.py` and exercised by
`tests/test_validate_routing.py` and `tests/fixtures/`.

- **Frontmatter type must be `router`.** A file whose `type` isn't `router` can't be parsed as one at
  all. (`test_reference_filename_diagnostic`)
- **Portal filenames are reserved for routers.** An uppercase `.md` "portal-shaped" filename (e.g.
  `NOTES.md`) may not carry `type: reference` — only routers may use that naming. (`test_reference_filename_diagnostic`)
- **Malformed frontmatter is reported, not crashed on.** An unsupported frontmatter line produces a
  readable error instead of a traceback. (`test_reference_filename_diagnostic`)
- **Every route target must exist.** A path listed in a `<routes>` block that doesn't resolve to a
  real file fails validation. (`test_broken_link`, `tests/fixtures/broken-link`)
- **Non-root routers must declare an owner.** Every router except the graph root needs at least one
  entry in `owners:`. (`test_ownerless_router`, `tests/fixtures/ownerless`)
- **Ownership is direct, not transitive.** A router only owns the routers it points to directly;
  claiming ownership through a grandchild, or routing to a child without a matching owner
  declaration, is rejected in both directions. (`test_transitive_owner_is_rejected`, `tests/fixtures/illegal-transitive`)
- **Reference owners must exist.** A leaf with `type: reference` and an `owners:` list is only valid
  if every listed owner file exists — it doesn't need to route back. (`test_reference_owner_missing`, `tests/fixtures/reference-owner-missing`)
- **Reference parse errors surface; unrelated errors still get checked.** A reference with broken
  frontmatter is reported rather than silently skipped, and the validator keeps reporting other
  problems (like a separate missing route) in the same run. (`test_reference_parse_errors_are_reported`)
- **Only `type: reference` leaves are validated.** Plain leaves — no frontmatter, unrelated
  frontmatter, or `type: reference` appearing outside the header — are never checked. (`test_ordinary_leaf_metadata_is_not_validated`)
- **A leading `@` in a route is relative to the declaring router, not the graph root.** A nested
  router's `@notes.md` route resolves next to that router's own file. (`test_nested_route_at_sign_is_router_local`)
- **An unrouted reference is never checked.** A reference leaf that no router points to is ignored
  even if its declared owner doesn't exist. (`test_unrouted_reference_is_not_checked`)
- **Multiple roots validate and report independently.** The validator accepts several root files in
  one invocation and prints a separate `PASS`/`FAIL` for each. (`test_all_roots_are_reported`)

</rules>
