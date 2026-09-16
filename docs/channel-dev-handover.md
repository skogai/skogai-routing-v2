# Channel dev handover

Status as of 2026-09-16, commit `f96d359`. What the wake-on-message channel
is, what broke while getting it working, what fixed each thing, and what to
do next time.

## What's implemented

`server.ts` is a stdio MCP server plus a local HTTP listener:

- **Outbound (Claude → external):** the `reply` MCP tool appends to
  `./channel.log` (gitignored, plain text, one line per reply).
- **Inbound (external → Claude):** `POST http://127.0.0.1:8765/message`
  with `{"content": "...", "meta": {...}}` triggers a
  `notifications/claude/channel` MCP notification, which Claude Code
  renders as a `<channel source="skogai-routing-v2" ...>` tag in the
  session transcript.
- `scripts/dev.sh` (`bun run dev`) launches a correctly-configured dev
  session in one command (see below for why that matters).
- `skogchan` (`~/.local/bin/skogchan`, outside this repo, unrelated to the
  pre-existing `skogcli`/`skogcli2` tools) wraps repeated `curl` sends:
  `skogchan register/send/list`.

Verified end-to-end at least once: a real Claude Code session received a
`<channel>` message and its `reply` landed in `channel.log`.

## What broke, in the order discovered

1. **Wrong branch.** The implementation was on a side branch, not `master`.
   Fixed by cherry-picking onto `master`.
2. **Channels are research-preview and gated by an allowlist.** A normal
   session — plugin installed and enabled, no errors anywhere — silently
   drops every inbound event. `mcp.notification()` still resolves
   successfully; nothing signals the drop. Needs
   `--dangerously-load-development-channels <entry>` to bypass. This was
   the single biggest time sink (multiple hours across several sessions).
3. **Orphaned server process holds the port.** Claude Code doesn't always
   kill the `server.ts` subprocess when a session exits. The next
   session's own `Bun.serve()` then throws `EADDRINUSE`, which — before
   the fix — crashed the whole process uncaught, silently killing the
   `reply` tool and stdio MCP connection too. Fixed in `server.ts`: the
   `Bun.serve()` call is now wrapped in try/catch and logs a clear
   diagnostic instead of crashing; `SIGTERM`/`SIGINT` handlers release the
   port on exit so the *next* session doesn't inherit the problem.
4. **The plugin cache lies about freshness.** Testing via
   `plugin:skogai-routing-v2@skogai-routing-v2` (the marketplace-installed
   copy under `~/.claude/plugins/cache/...`) means testing whatever got
   copied in at install time. Claude Code only refreshes that cache copy
   when `plugin.json`'s `version` field changes — a `git push` alone does
   nothing. This is why fix #3 didn't show up in a live session until it
   was manually copied into the cache once, and why that manual copy
   wasn't a real fix — every future edit would go stale again the same
   way.
5. **The actual fix for #4: don't use the marketplace path at all during
   development.** `claude --plugin-dir <repo>` loads the checkout in
   place, no cache, no install step, edits are live. Its channel bypass
   entry is `server:skogai-routing-v2` (the `.mcp.json` server name), not
   `plugin:name@marketplace` — a `--plugin-dir` plugin has no marketplace.
   A `.envrc` hack that manually exported `CLAUDE_PLUGIN_ROOT` (to work
   around loading `.mcp.json` as a bare project config) was reverted once
   `--plugin-dir` made it unnecessary.

## Current state

- `bun run dev` is the one correct way to start a session against this
  checkout for channel testing. It runs `scripts/dev.sh`, which resolves
  its own location to the repo root and execs
  `claude --plugin-dir <repo> --dangerously-load-development-channels server:skogai-routing-v2`.
- `server.ts` survives a stale-port conflict (logs and keeps the `reply`
  tool working) instead of crashing.
- `CLAUDE.md` and `.claude/skills/run-skogai-routing-v2/SKILL.md` document
  all of the above, including the `/mcp` connection check and the
  `/reload-plugins` limitation (it does not reconnect plugin MCP servers —
  a `server.ts` edit needs a session restart, not just a reload).
- Everything above is committed and pushed to `origin/master`
  (`f96d359`).

## Next time, start here

```sh
bun run dev
```

Then in that session: run `/mcp`, confirm `skogai-routing-v2` shows
`connected` — if it doesn't, that's the first and fastest diagnostic, before
touching the HTTP side at all. Only then:

```sh
curl -s localhost:8765/message -d '{"content":"hello"}'
```

## What's still a placeholder / not done

- `reply` only writes to `channel.log` — there's no real external service
  wired in yet (Telegram, Discord, a chat UI, etc.).
- `agents/example.md`, `skills/example/SKILL.md`,
  `output-styles/skogai-routing-v2.md`, and `.lsp.json` are still scaffold
  TODOs, unrelated to the channel work above.
