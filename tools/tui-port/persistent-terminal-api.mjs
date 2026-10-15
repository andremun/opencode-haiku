// Persistent terminal (Rust daemon) acceptance through the bundled OpenCode server. No LLM needed.
// Usage: node persistent-terminal-api.mjs ROOT OPENCODE_LAUNCHER  (prints one JSON event per line)
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { randomBytes } from 'node:crypto';
import assert from 'node:assert/strict';
const root = resolve(process.argv[2] ?? '/boot/home/opencode-acceptance');
const launcher = resolve(process.argv[3] ?? '/boot/home/opencode-haiku-2.0.29-haiku.4/opencode');
const fixture = resolve(root, 'terminal-fixture');
mkdirSync(fixture, { recursive: true });
writeFileSync(resolve(fixture, 'opencode.json'), JSON.stringify({ update: 'disable', share: 'disabled', snapshots: false, shell: '/bin/sh', permissions: [{ action: '*', resource: '*', effect: 'deny' }] }));
const env = Object.fromEntries(Object.entries(process.env).filter(([name]) => /^(PATH|HOME|XDG_(DATA|CONFIG|CACHE|STATE)_HOME|LANG|LC_[A-Z_]+|SSL_CERT_FILE|SSL_CERT_DIR|LIBRARY_PATH)$/.test(name)));
env.OPENCODE_DISABLE_MODELS_FETCH = '1';
for (const name of ['DATA', 'CONFIG', 'CACHE', 'STATE']) env['XDG_' + name + '_HOME'] = resolve(root, 'terminal-state', name.toLowerCase());
const events = [];
const record = (event, data) => { events.push({ event, data }); console.log(JSON.stringify({ event, data })); };
const password = randomBytes(24).toString('base64url');
const server = spawn(launcher, ['serve', '--stdio', '--port', '0'], { cwd: fixture, env: { ...env, OPENCODE_PASSWORD: password }, stdio: ['pipe', 'pipe', 'pipe'] });
let stderr = '';
server.stderr.on('data', (chunk) => { stderr += chunk; });
const watchdog = setTimeout(() => { record('timeout', stderr.slice(-2000)); server.kill('SIGKILL'); process.exit(124); }, 300000);
const url = await new Promise((done, fail) => {
  let output = '';
  server.stdout.on('data', (chunk) => { output += chunk; if (output.includes('\n')) { try { done(JSON.parse(output.split('\n')[0]).url); } catch (error) { fail(error); } } });
  server.on('exit', (code) => fail(new Error('server exited ' + code + ' ' + stderr.slice(-1500))));
});
const auth = { Authorization: 'Basic ' + Buffer.from('opencode:' + password).toString('base64') };
async function api(path, { method = 'GET', body, headers = {} } = {}) {
  const response = await fetch(url + path, { method, headers: { ...auth, ...headers, ...(body === undefined ? {} : { 'Content-Type': 'application/json' }) }, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(45000) });
  const text = await response.text();
  if (!response.ok) throw new Error(`${method} ${path}: HTTP ${response.status}: ${text}`);
  return text ? JSON.parse(text) : undefined;
}
async function attach(id, cursor, until, timeoutMs = 30000, framed = true, takeover = false) {
  const ticket = (await api(`/api/experimental/persistent-pty/${id}/connect-token`, { method: 'POST', headers: { 'x-opencode-ticket': '1' } })).data;
  const connect = new URL(url.replace(/^http/, 'ws') + `/api/experimental/persistent-pty/${id}/connect`);
  connect.searchParams.set('ticket', ticket.ticket ?? ticket); connect.searchParams.set('cursor', String(cursor)); if (framed) connect.searchParams.set('input_protocol', '1'); if (takeover) connect.searchParams.set('takeover', 'true');
  const socket = new WebSocket(connect); socket.binaryType = 'arraybuffer';
  const state = { text: '', control: [], socket };
  state.done = new Promise((resolveDone, reject) => {
    const timer = setTimeout(() => reject(new Error('terminal timeout; output so far: ' + JSON.stringify(state.text) + ' control: ' + JSON.stringify(state.control.map((message) => message.type)) + ' closed=' + !!state.closed)), timeoutMs);
    const check = () => { if (until(state)) { clearTimeout(timer); resolveDone(state); } };
    socket.addEventListener('error', () => { clearTimeout(timer); reject(new Error('websocket error')); });
    socket.addEventListener('close', (event) => { state.closed = true; state.closeCode = event.code; check(); });
    socket.addEventListener('message', (event) => {
      if (typeof event.data === 'string') { try { state.control.push(JSON.parse(event.data)); } catch { state.text += event.data; } }
      else state.text += Buffer.from(event.data).toString('utf8');
      check();
    });
  });
  return state;
}
let failure;
try {
  const info = await api('/api/info');
  record('server-info', { version: info.version, capabilities: info.capabilities });
  assert.equal(info.capabilities?.persistentPty, true, 'persistent PTY capability must be advertised');
  const session = (await api('/api/session', { method: 'POST', body: { title: 'Persistent terminal probe', location: { directory: fixture } } })).data;
  const script = "stty size; printf 'PERSIST_READY \\303\\251\\342\\202\\254\\n'; read line; stty size; printf 'PERSIST_RESULT %s\\n' \"$line\"; sleep 8; exit 5";
  const terminal = (await api(`/api/experimental/session/${session.id}/terminal`, { method: 'POST', body: { command: '/bin/sh', args: ['-c', script], cwd: fixture, title: 'Haiku persistent terminal', env: {}, size: { cols: 80, rows: 24 } } })).data;
  record('terminal-created', { id: terminal.id, size: terminal.size, status: terminal.status });
  let sent = false;
  const first = await attach(terminal.id, 0, (state) => {
    if (!sent && state.text.includes('PERSIST_READY')) {
      sent = true;
      const attached = state.control.find((message) => message.type === 'attached');
      api(`/api/experimental/persistent-pty/${terminal.id}`, { method: 'PUT', body: { attachmentID: attached?.attachmentID, size: { cols: 100, rows: 42 } } }).then(() => state.socket.send(Buffer.concat([Buffer.from([1, 0, 100, 0, 42]), Buffer.from('HELLO\n')]))).catch((error) => { failure = error; state.socket.close(); });
    }
    return state.text.includes('PERSIST_RESULT HELLO');
  });
  await first.done;
  record('first-attachment', { text: first.text, control: first.control.map((message) => message.type) });
  assert.match(first.text, /24 80/, 'initial size');
  assert.match(first.text, /42 100/, 'resized size delivered to the child');
  assert.match(first.text, /PERSIST_READY é€/, 'UTF-8 output');
  assert.match(first.text, /PERSIST_RESULT HELLO/, 'input echoed through the daemon');
  first.socket.close();
  // Reconnect while the child is still alive: replay must restore earlier output.
  const live = (await api(`/api/experimental/persistent-pty/${terminal.id}`)).data;
  record('live-info', { status: live.status, size: live.size, output: live.output, foreground: live.foregroundProcess });
  assert.equal(live.status, 'running');
  let exitedCode, exitedMessage;
  const second = await attach(terminal.id, 0, (state) => { const exited = state.control.find((message) => message.type === 'exited'); if (exited) { exitedMessage = exited; exitedCode = exited.code ?? exited.exitCode ?? exited.status; } return !!exited; }, 40000, true, true);
  await new Promise((done) => setTimeout(done, 1500));
  const snapshot = (await api(`/api/experimental/persistent-pty/${terminal.id}/snapshot`)).data;
  record('snapshot', { text: snapshot.text, cursor: snapshot.cursor });
  assert.match(snapshot.text, /PERSIST_RESULT HELLO/, 'snapshot shows authoritative screen');
  const listed = (await api(`/api/experimental/session/${session.id}/terminal`)).data;
  record('listed', listed.map((entry) => ({ id: entry.id, status: entry.status })));
  const read = (await api(`/api/experimental/session/${session.id}/terminal/read`)).data;
  record('read', read ? { rows: read.screen.rows, cols: read.screen.cols, tail: read.screen.text.split('\n').filter(Boolean).slice(-3) } : null);
  await second.done;
  record('reconnect-replay', { replayedText: second.text, control: second.control.map((message) => ({ type: message.type, code: message.code, truncated: message.replay?.truncated })) });
  assert.match(second.text, /PERSIST_RESULT HELLO/, 'reconnect replay restores earlier output');
  record('exit-event', exitedMessage);
  assert.equal(exitedCode, 5, 'child exit status reported');
  second.socket.close();
  await new Promise((done) => setTimeout(done, 1500));
  const gone = await fetch(url + `/api/experimental/persistent-pty/${terminal.id}`, { headers: auth }).then((response) => response.status);
  record('after-exit-lookup', { httpStatus: gone });
  await fetch(url + `/api/experimental/persistent-pty/${terminal.id}`, { method: 'DELETE', headers: auth });
  const remaining = (await api(`/api/experimental/session/${session.id}/terminal`)).data;
  assert.equal(remaining.length, 0, 'terminal removed');
  record('cleanup', 'no terminals remain');
  await api('/api/experimental/persistent-pty/shutdown', { method: 'POST' });
  record('daemon-shutdown', 'ok');
  record('result', 'PASS');
} catch (error) {
  failure = error;
}
if (failure) record('error', { message: String(failure.message ?? failure), stderr: stderr.slice(-3000) });
server.stdin.end();
await new Promise((done) => { const timer = setTimeout(() => { server.kill('SIGKILL'); done(); }, 8000); server.on('close', () => { clearTimeout(timer); done(); }); });
clearTimeout(watchdog);
process.exit(failure ? 1 : 0);
