---
name: run-skogai-routing-v2
description: Build, run, and drive the skogai-routing-v2 plugin's channel MCP server and SessionStart hook. Use when asked to start/run/test the server, list or call its tools, verify the channel contract, or run the session-start hook.
---

This repo *is* the plugin (no separate app dir). Its only runtime piece is
`server.ts`, a stdio MCP server — there's no HTTP port and no GUI, so it's
driven by speaking newline-delimited JSON-RPC 2.0 over its stdin/stdout, per
the [channels reference](https://code.claude.com/docs/en/channels-reference).
Drive it via `.claude/skills/run-skogai-routing-v2/driver.mjs`, which does the
`initialize` handshake and then calls tools. All paths below are relative to
the repo root.

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
- **`reply` and inbound channel events are both stubs.** `reply`'s handler
  returns the literal string `"sent"` without delivering anything anywhere
  (see the `TODO` in `server.ts`), and there is no inbound
  `notifications/claude/channel` push implemented yet — so the driver has
  nothing further to exercise for the "external service" side of the
  contract, only the tool-call side.
- **`bun run start` re-runs `bun install` every time** (it's `bun install
  --no-summary && bun server.ts`), which is a couple hundred ms of overhead
  on every launch even when nothing changed — harmless, just don't be
  surprised by the extra output on stderr-adjacent installs.
