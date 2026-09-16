---
name: run-skogai-routing-v2
description: Build, run, and drive the skogai-routing-v2 plugin's channel MCP server and SessionStart hook. Use when asked to start/run/test the server, list or call its tools, verify the channel contract, or run the session-start hook.
---

This repo *is* the plugin (no separate app dir). Its only runtime piece is
`server.ts`, a stdio MCP server for the outbound (Claude → external) side,
plus a local-only HTTP listener for the inbound (external → Claude) side —
see [channels reference](https://code.claude.com/docs/en/channels-reference).
Drive the stdio/tool side via `.claude/skills/run-skogai-routing-v2/driver.mjs`,
which does the `initialize` handshake and then calls tools. Drive the inbound
HTTP side with `curl` or the `skogchan` helper (see below). All paths below
are relative to the repo root.

## Prerequisites

Just `bun` (already on PATH in this container — `bun --version` → 1.3.11).
No OS packages needed.

## Setup

```bash
bun install
# First run: resolves/downloads/extracts @modelcontextprotocol/sdk (~90 packages).
# Already installed: "Checked N installs across N packages (no changes)".
```

## Run (agent path)

```bash
bun .claude/skills/run-skogai-routing-v2/driver.mjs
```

This spawns `bun server.ts`, does the MCP `initialize` handshake, lists
tools, and calls `reply` with a demo message. Verified output:

```
SERVER INFO: {"name":"skogai-routing-v2","version":"0.1.0"}
CHANNEL CAPABILITY: {"claude/channel":{}}
TOOLS: [{"name":"reply","description":"Send a message back to the skogai-routing-v2 channel.","inputSchema":{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}}]
DEMO reply CALL RESULT: {"content":[{"type":"text","text":"sent"}]}
```

To call a specific tool with specific arguments instead of the demo call:

```bash
bun .claude/skills/run-skogai-routing-v2/driver.mjs --tool reply --args '{"text":"custom message"}'
```

Calling a tool that doesn't exist returns `isError: true` rather than
throwing — confirmed with `--tool bogus --args '{}'` → `{"content":[{"type":"text","text":"unknown tool"}],"isError":true}`.

The driver exits on its own after the call completes; no process to clean up.

### Sending inbound events (external → Claude)

This only reaches a real Claude Code session — not the `driver.mjs` harness
above — and only if that session was started right. Two separate
requirements, both mandatory:

**Load this checkout with `--plugin-dir`, not the marketplace-installed
copy.** Claude Code only re-copies a marketplace plugin into
`~/.claude/plugins/cache/...` when `plugin.json`'s `version` changes — a
`git push` doesn't update it, so testing against the installed
`skogai-routing-v2@skogai-routing-v2` plugin means testing stale code.
`--plugin-dir` loads the repo in place instead, no cache, no install step,
edits are live.

**Bypass the channel allowlist.** Channels are in research preview and
custom channels aren't on the approved allowlist, so a normal session drops
every inbound event silently (no error on either side, `mcp.notification()`
still resolves "successfully").

Both together:

```bash
claude --plugin-dir /home/skogix/.local/src/skogai-routing-v2 --dangerously-load-development-channels server:skogai-routing-v2
```

Note the bypass entry is `server:skogai-routing-v2` (the `.mcp.json` server
name), not `plugin:name@marketplace` — `--plugin-dir` plugins have no
marketplace.

Accept the warning dialog, then look for the dim banner `Channels
(experimental) messages from server:skogai-routing-v2 inject directly in
this session`. Run `/mcp` at any point to confirm `skogai-routing-v2` shows
`connected` before troubleshooting anything else — this is the single most
useful diagnostic step, and the one most likely to be skipped.

If you edit `server.ts` mid-session, `/reload-plugins` won't pick it up —
plugin MCP server reconnects only happen on the next session, not on
`/reload-plugins`. Restart the session after server.ts changes.

Once that session is confirmed connected, any local process can POST to wake it:

```bash
curl -s localhost:8765/message -d '{"content":"hello"}'
# → {"ok":true}
```

A `200 {"ok":true}` response only means the HTTP layer accepted the POST —
it does **not** mean the message reached a session. Check the terminal
running the flagged session for the `<channel>` tag to confirm delivery.

`content` (required, string) becomes the event body; `meta` (optional object)
keys become attributes on the `<channel source="skogai-routing-v2" ...>` tag
Claude sees — keys must be identifier-safe (letters/digits/underscores) or
they're silently dropped. The port defaults to 8765, overridable via
`SKOGAI_CHANNEL_PORT`.

The `skogchan` helper script (`~/.local/bin/skogchan`, separate from the
unrelated `skogcli` tool) wraps this for repeated use:

```bash
skogchan register skogai-routing-v2 8765   # once, remembers the port by name
skogchan send skogai-routing-v2 "hello"    # POSTs to it
skogchan list                              # show registered channels
```

Replies Claude sends via the `reply` tool are appended to `./channel.log`
(one line per reply, ISO timestamp prefix) rather than delivered anywhere
automatically — tail that file to watch them.

### Testing the SessionStart hook directly

The hook handler is a standalone stdin→stdout JSON program, no server needed:

```bash
echo '{"hook_event_name":"SessionStart","session_id":"test123","cwd":"'"$PWD"'"}' | bun hooks-handlers/on-session-start.ts
# → {}
```

## Run (human path)

```bash
bun run start   # bun install --no-summary && bun server.ts
```

This blocks waiting for JSON-RPC on stdin — it's meant to be launched by
Claude Code as a channel MCP server (via `.mcp.json`), not run interactively.
Confirmed it starts cleanly and blocks (no output, no crash) when piped
input on stdin; Ctrl-C or closing stdin ends it.

## Test

There is no test suite in this repo (confirmed: no test runner, no CI config).
The driver script above is the closest thing to a smoke test.

---

## Gotchas

- **The server speaks bare JSON-RPC, not full LSP framing** — no
  `Content-Length` headers, just one JSON object per line. A driver that
  tries to parse `Content-Length:`-style frames will hang forever waiting
  for a header that never comes.
- **`reply` writes to `./channel.log`, nothing more.** It appends a
  timestamped line and returns `"sent"` — there's no delivery to any actual
  external service yet, just a file an external watcher can `tail -f`.
- **Inbound events require the server to actually be running and listening**
  (`Bun.serve` starts *after* `mcp.connect`, so the startup log lines
  `[skogai-routing-v2] inbound: POST http://127.0.0.1:8765/message` and
  `... replies logged to ./channel.log` on stderr are the signal it's ready).
  The driver script only exercises the stdio/tool side — use `curl`/`skogchan`
  against the HTTP port to exercise the inbound side, as above.
- **`bun run start` re-runs `bun install` every time** (it's `bun install
  --no-summary && bun server.ts`), which is a couple hundred ms of overhead
  on every launch even when nothing changed — harmless, just don't be
  surprised by the extra output on stderr-adjacent installs.
- **A stale `server.ts` from a previous session silently blocks inbound
  events on the next one.** Claude Code doesn't always kill the subprocess
  on exit, so a leftover process can keep holding port 8765. The new
  session's own `server.ts` still connects fine over stdio (`reply` keeps
  working, `/mcp` shows `connected`) but its `Bun.serve()` call throws
  `EADDRINUSE`; the catch logs `inbound HTTP listener failed to start on
  port 8765: ...` to stderr instead of crashing. `ss -ltnp | grep 8765`
  finds the stale process; kill it and restart the session.
- **`curl` returning `200 {"ok":true}` only proves the HTTP layer accepted
  the POST — not that a session received it.** If the session wasn't
  started with `--dangerously-load-development-channels
  server:skogai-routing-v2`, Claude Code drops the event with no error
  anywhere. Check `/mcp` for `connected` status before trusting a `curl`
  success as proof of delivery.
- **Testing against the installed marketplace plugin instead of
  `--plugin-dir` silently tests stale code.** The plugin cache
  (`~/.claude/plugins/cache/skogai-routing-v2/skogai-routing-v2/<version>/`)
  is a plain file copy that Claude Code only refreshes when `plugin.json`'s
  `version` changes, not on every `git push`. A session that loads
  `plugin:skogai-routing-v2@skogai-routing-v2` can be running code several
  commits behind the repo with no warning. `--plugin-dir` avoids the cache
  entirely — always use it for local development (see above).
