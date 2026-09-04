---
permalink: fixtures/valid/unrouted-reference
type: reference
owners:
  - DOES-NOT-EXIST.md
---

# Unrouted reference

Never appears in any router's <routes> block, so the validator never visits it and its
(deliberately broken) owner is never checked.
