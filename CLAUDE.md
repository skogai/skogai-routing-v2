# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

`skogai-routing-v2` is a **Claude Code plugin**, not an application. It is currently a
freshly-scaffolded skeleton: every user-facing file (`SKILL.md`, `skills/example/SKILL.md`,
`agents/example.md`, `output-styles/skogai-routing-v2.md`) still contains `TODO` placeholder
frontmatter and body text. The plugin bundles a **channel** — an MCP server that pushes external
events into a Claude session and accepts replies back out.

Treat the `TODO`s as the work: filling them in is what turns the scaffold into a functioning plugin.

## Commands

There is no build, lint, or test setup in this repo — no test runner, no linter config, no CI.
Do not invent commands; the only defined script is the MCP server entry point.

```sh
bun install                 # install @modelcontextprotocol/sdk
bun run start               # bun install --no-summary && bun server.ts (stdio MCP server)
```

The server speaks MCP over **stdio**, so `bun run start` on its own will just block waiting for
JSON-RPC on stdin. To exercise it, either connect it through a client or pipe a handcrafted
JSON-RPC frame in. To exercise the hook handler directly:

```sh
echo '{}' | bun hooks-handlers/on-session-start.ts
```

`bun` is the assumed runtime throughout (`.mcp.json`, `hooks/hooks.json`, and the shebangs all
invoke it). `node` and `python3` are also present; `hooks-handlers/on-session-start.ts` notes that
swapping `bun` for one of them in `hooks/hooks.json` is a supported fallback for users without bun —
but the handler itself uses `Bun.stdin`, so a swap requires rewriting the stdin read too.

## Architecture

`.claude-plugin/plugin.json` is the manifest that wires everything together. Nothing else is
auto-discovered by convention alone — read the manifest first to know what is actually registered:

- `"skills": ["./"]` — the **repo root itself** is a skill directory, so the top-level `SKILL.md` is
  the plugin's primary skill. `skills/example/SKILL.md` is a second, nested skill.
- `"channels": [{ "server": "skogai-routing-v2", ... }]` — binds the channel UI to the MCP server of
  that name declared in `.mcp.json`, which launches `server.ts` via
  `bun run --cwd ${CLAUDE_PLUGIN_ROOT} start`.

`${CLAUDE_PLUGIN_ROOT}` is substituted by Claude Code at load time and is how both `.mcp.json` and
`hooks/hooks.json` reference files inside the plugin. Always use it for intra-plugin paths rather
than relative paths — the plugin is loaded from an arbitrary install location, not the cwd.

### The channel contract (`server.ts`)

This is the only non-trivial code in the repo, and its two halves are asymmetric:

- **Outbound (Claude → external service):** the `reply` tool. The `instructions` string on the
  `Server` states the rule that makes the channel work — Claude's transcript output *never* reaches
  the channel, so anything the sender should see must be sent through `reply`. Its handler is a stub
  that returns `"sent"` without delivering anything.
- **Inbound (external service → Claude):** a `notifications/claude/channel` notification, sketched in
  a trailing comment block but not implemented. `params.content` becomes the event body;
  each `params.meta` key becomes an attribute on the `<channel source="...">` tag Claude sees, and
  meta keys must be identifier-safe (letters/digits/underscores) or they are silently dropped.

The `capabilities.experimental['claude/channel'] = {}` key is load-bearing: its presence is what
registers the channel notification listener on Claude's side. Removing it breaks inbound events even
though the server still starts fine.

Reference docs: https://code.claude.com/docs/en/channels-reference

### Hooks

`hooks/hooks.json` registers one `SessionStart` hook running `hooks-handlers/on-session-start.ts`.
The handler contract is stdin/stdout JSON: read the event object from stdin, write a JSON result to
stdout. The current handler parses the event and returns `{}` (a no-op) — `event` is bound but unused.

### Other pieces

- `output-styles/skogai-routing-v2.md` has `force-for-plugin: true`, meaning its prompt is appended
  to the system prompt **automatically whenever this plugin is enabled** — not only when a user picks
  it in `/config`. Edits here affect every session with the plugin on.
- `.lsp.json` registers a language server, still pointed at a placeholder `example-language-server`
  binary for a `.example` extension. It will fail to launch until replaced or removed.

## Conventions

- Skill and agent `description` frontmatter is matched against the user's request, so it must say
  *when* to use the thing and include likely trigger phrases — the placeholder text explains this and
  should be replaced, not merely trimmed.
- TypeScript sources use ESM (`"type": "module"`), no semicolons, single quotes, and 2-space indent.
