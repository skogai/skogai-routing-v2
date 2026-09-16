#!/usr/bin/env bash
# Launch a Claude Code session against this checkout for channel development.
#
# --plugin-dir loads the plugin in place (no marketplace cache copy, so
# ${CLAUDE_PLUGIN_ROOT} always resolves here and edits are live).
# --dangerously-load-development-channels bypasses the research-preview
# channel allowlist for this plugin's .mcp.json server, named
# skogai-routing-v2 there. Without it, inbound events are dropped silently.
#
# See CLAUDE.md's "Testing end-to-end" section for why both flags matter
# and what to check (`/mcp`) if the channel doesn't connect.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

exec claude \
  --plugin-dir "$repo_root" \
  --dangerously-load-development-channels server:skogai-routing-v2 \
  "$@"
