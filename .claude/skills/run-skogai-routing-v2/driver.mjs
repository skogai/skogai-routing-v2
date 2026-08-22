#!/usr/bin/env bun
// MCP stdio driver for the skogai-routing-v2 channel server.
// Spawns `bun server.ts`, performs the initialize handshake, then either
// lists tools or calls one. Talks newline-delimited JSON-RPC 2.0, per
// https://code.claude.com/docs/en/channels-reference.
//
// Usage:
//   bun driver.mjs                              # handshake + tools/list + demo reply call
//   bun driver.mjs --tool reply --args '{"text":"hi"}'
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..')

const argv = process.argv.slice(2)
let toolName = null
let toolArgs = {}
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--tool') toolName = argv[++i]
  if (argv[i] === '--args') toolArgs = JSON.parse(argv[++i])
}

const child = spawn('bun', ['server.ts'], { cwd: repoRoot, stdio: ['pipe', 'pipe', 'pipe'] })

let buf = ''
const pending = new Map()
let nextId = 1

child.stdout.on('data', chunk => {
  buf += chunk.toString()
  let idx
  while ((idx = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, idx)
    buf = buf.slice(idx + 1)
    if (!line.trim()) continue
    let msg
    try {
      msg = JSON.parse(line)
    } catch {
      console.error('[unparsed]', line)
      continue
    }
    if (msg.id !== undefined && pending.has(msg.id)) {
      pending.get(msg.id)(msg)
      pending.delete(msg.id)
    }
  }
})
child.stderr.on('data', chunk => process.stderr.write(chunk))
child.on('exit', code => {
  if (code !== 0 && code !== null) console.error('[server exited]', code)
})

function send(method, params) {
  const id = nextId++
  child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n')
  return new Promise(resolve => pending.set(id, resolve))
}
function notify(method, params) {
  child.stdin.write(JSON.stringify({ jsonrpc: '2.0', method, params }) + '\n')
}

await new Promise(r => setTimeout(r, 300))

const init = await send('initialize', {
  protocolVersion: '2024-11-05',
  capabilities: {},
  clientInfo: { name: 'run-skogai-routing-v2-driver', version: '0.0.1' },
})
if (init.error) throw new Error(`initialize failed: ${JSON.stringify(init.error)}`)
console.log('SERVER INFO:', JSON.stringify(init.result.serverInfo))
console.log('CHANNEL CAPABILITY:', JSON.stringify(init.result.capabilities.experimental))

notify('notifications/initialized', {})

const tools = await send('tools/list', {})
console.log('TOOLS:', JSON.stringify(tools.result.tools))

if (toolName) {
  const call = await send('tools/call', { name: toolName, arguments: toolArgs })
  console.log('CALL RESULT:', JSON.stringify(call.result ?? call.error))
} else {
  const call = await send('tools/call', { name: 'reply', arguments: { text: 'hello from driver' } })
  console.log('DEMO reply CALL RESULT:', JSON.stringify(call.result))
}

child.stdin.end()
child.kill()
