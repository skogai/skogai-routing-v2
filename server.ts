#!/usr/bin/env bun
/**
 * skogai-routing-v2 channel server — stdio MCP server implementing the channel contract.
 * See https://code.claude.com/docs/en/channels-reference.
 */
import { appendFileSync } from 'node:fs'
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js'

// Replies land here so an external watcher (tail -f) can see them.
const LOG_PATH = './channel.log'
// Local-only HTTP port other processes POST inbound messages to.
const PORT = Number(process.env.SKOGAI_CHANNEL_PORT ?? 8765)

const mcp = new Server(
  { name: 'skogai-routing-v2', version: '0.1.0' },
  {
    capabilities: {
      tools: {},
      // Required: presence of this key registers the channel notification
      // listener on Claude's side.
      experimental: { 'claude/channel': {} },
    },
    instructions:
      "Events from skogai-routing-v2 arrive as <channel source=\"skogai-routing-v2\" ...>. Anything " +
      "you want the sender to see must go through the reply tool — your " +
      "transcript output never reaches the channel.",
  },
)

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'reply',
      description: 'Send a message back to the skogai-routing-v2 channel.',
      inputSchema: {
        type: 'object',
        properties: { text: { type: 'string' } },
        required: ['text'],
      },
    },
  ],
}))

mcp.setRequestHandler(CallToolRequestSchema, async req => {
  const args = (req.params.arguments ?? {}) as Record<string, unknown>
  if (req.params.name === 'reply') {
    const text = String(args.text ?? '')
    appendFileSync(LOG_PATH, `[${new Date().toISOString()}] ${text}\n`)
    return { content: [{ type: 'text', text: 'sent' }] }
  }
  return { content: [{ type: 'text', text: 'unknown tool' }], isError: true }
})

await mcp.connect(new StdioServerTransport())

// Inbound side: any local process — another MCP server, a script, curl —
// can POST { content, meta? } to wake this channel's session.
Bun.serve({
  port: PORT,
  hostname: '127.0.0.1',
  async fetch(req) {
    const url = new URL(req.url)
    if (url.pathname !== '/message') return new Response('not found', { status: 404 })
    if (req.method !== 'POST') return new Response('POST only', { status: 405 })

    let body: unknown
    try {
      body = await req.json()
    } catch {
      return new Response('invalid JSON', { status: 400 })
    }

    const { content, meta } = (body ?? {}) as { content?: unknown; meta?: unknown }
    if (typeof content !== 'string' || content.length === 0) {
      return new Response('"content" (string) is required', { status: 400 })
    }

    // Meta keys must be identifiers (letters/digits/underscores) to survive
    // as <channel> attributes — non-conforming keys are silently dropped by
    // Claude, not by us.
    await mcp.notification({
      method: 'notifications/claude/channel',
      params: { content, meta: (meta ?? {}) as Record<string, string> },
    })

    return Response.json({ ok: true })
  },
})

console.error(`[skogai-routing-v2] inbound: POST http://127.0.0.1:${PORT}/message`)
console.error(`[skogai-routing-v2] replies logged to ${LOG_PATH}`)
