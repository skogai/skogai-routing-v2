# skogai-routing-v2

Explicit, one-hop context routing for SkogAI projects, packaged as a Claude Code plugin.

The first implementation slice defines the routing graph independently of channel transport:

- routers are uppercase Markdown choice portals;
- ownership is explicit, supports multiple direct owners, and is never inherited;
- route targets must exist;
- validation reports every discovered error before exiting.

See [the routing contract](docs/routing-contract.md).

```sh
python3 scripts/validate_routing.py SKOGAI.md
python3 -m unittest discover -s tests -v
```

