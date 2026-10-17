// Real multi-file coding task for a cloud model through the port (or any OpenCode launcher).
// The fixture is synthetic (examples/cloud-task/start); never point this at private code,
// because free models may use prompts to improve the model (see docs/CLOUD-CODING-TASK.md).
// Usage: OPENCODE_TEST_PORT_ROOT=/path/to/opencode OPENCODE_CLOUD_MODEL=opencode/glm-5.3-flash-free \
//        node cloud-coding-task.mjs OUTPUT_DIR
// Authentication is the caller's: set OPENCODE_CLOUD_DATA_HOME to an XDG data directory in which
// the user has already run `opencode auth login`. This script never reads or prints its contents.
import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { cpSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const startDir = resolve(here, '../../examples/cloud-task/start');
const root = resolve(process.argv[2] ?? '.');
const launcher = process.env.OPENCODE_TEST_PORT_ROOT;
const model = process.env.OPENCODE_CLOUD_MODEL;
if (!launcher || !model || !model.includes('/')) throw new Error('Set OPENCODE_TEST_PORT_ROOT and OPENCODE_CLOUD_MODEL (provider/model, for example opencode/glm-5.3-flash-free)');
const steps = Number(process.env.OPENCODE_TEST_STEPS ?? 20);
if (!Number.isInteger(steps) || steps < 4 || steps > 32) throw new Error('OPENCODE_TEST_STEPS must be an integer from 4 to 32');
const runID = 'cloud-' + Date.now();
const fixture = resolve(root, runID, 'fixture');
mkdirSync(fixture, { recursive: true });
cpSync(startDir, fixture, { recursive: true });
writeFileSync(resolve(fixture, 'opencode.json'), JSON.stringify({
  model, update: 'disable', share: 'disabled', snapshots: false, formatter: false, lsp: false,
  // Scoped allow-list, not a blanket deny: read anywhere, edit only src/, run `node --test` (with any suffix such as a pipe to tail).
  permissions: [
    { action: '*', resource: '*', effect: 'deny' },
    { action: 'read', resource: '*', effect: 'allow' },
    { action: 'edit', resource: 'src/*', effect: 'allow' },
    { action: 'shell', resource: 'node --test*', effect: 'allow' },
    // Piped commands are checked part by part, so allow the usual output trimmers too.
    { action: 'shell', resource: 'tail *', effect: 'allow' },
    { action: 'shell', resource: 'head *', effect: 'allow' },
  ],
  agents: { probe: { mode: 'primary', model, steps, system: 'You are a careful coding assistant. Work only in the current project directory.' } },
}));
const testsHash = () => {
  const hash = createHash('sha256');
  for (const name of readdirSync(resolve(fixture, 'test')).sort()) hash.update(name).update(readFileSync(resolve(fixture, 'test', name)));
  return hash.digest('hex');
};
const before = testsHash();
const prompt = 'The tests in this project fail. Run `node --test` to see them, then implement parseCSV in src/csv.mjs and summarize in src/report.mjs so that every test passes. Do not edit anything under test/. Run `node --test` again after your changes and, when all tests pass, reply with the single word DONE.';
const env = Object.fromEntries(Object.entries(process.env).filter(([name]) => /^(PATH|HOME|LANG|LC_[A-Z_]+|SSL_CERT_FILE|SSL_CERT_DIR)$/.test(name)));
// The agent's shell must find `node --test`: put the runner's own Node first on PATH.
env.PATH = dirname(process.execPath) + ':' + (env.PATH ?? '');
// The cloud model catalogue must be fetched; set OPENCODE_CLOUD_OFFLINE=1 only for host controls.
if (process.env.OPENCODE_CLOUD_OFFLINE === '1') env.OPENCODE_DISABLE_MODELS_FETCH = '1';
for (const name of ['DATA', 'CONFIG', 'CACHE', 'STATE']) env['XDG_' + name + '_HOME'] = resolve(root, runID, 'state', name.toLowerCase());
// Explicit opt-in: the key is passed to the child only, and redacted from every saved log.
const apiKey = process.env.OPENCODE_CLOUD_PASS_API_KEY === '1' ? process.env.OPENCODE_API_KEY : undefined;
if (apiKey) env.OPENCODE_API_KEY = apiKey;
const redact = (text) => (apiKey ? text.split(apiKey).join('[REDACTED]') : text);
if (process.env.OPENCODE_CLOUD_DATA_HOME) env.XDG_DATA_HOME = resolve(process.env.OPENCODE_CLOUD_DATA_HOME);
const log = resolve(root, runID, 'agent.log');
writeFileSync(log, '');
const started = Date.now();
const child = spawn(resolve(launcher), ['run', '--agent', 'probe', '--standalone', '--model', model, '--title', 'CSV report task', '--format', 'json', prompt], { cwd: fixture, env, stdio: ['ignore', 'pipe', 'pipe'] });
let output = '';
for (const stream of [child.stdout, child.stderr]) stream.on('data', (chunk) => { output += chunk; writeFileSync(log, redact(output)); });
let expired = false;
const timer = setTimeout(() => { expired = true; child.kill('SIGTERM'); setTimeout(() => child.kill('SIGKILL'), 5000).unref(); }, Number(process.env.OPENCODE_TEST_TIMEOUT_MS ?? 1200000));
let launchError;
const code = await new Promise((done) => { child.once('error', (error) => { launchError = String(error); done(127); }); child.once('close', done); });
clearTimeout(timer);
const events = output.split('\n').flatMap((line) => { try { return [JSON.parse(line)]; } catch { return []; } });
const shellRuns = events.filter((e) => e.type === 'tool_use' && e.part?.tool === 'shell' && e.part.state?.status === 'completed' && /node --test/.test(e.part.state.input?.command ?? ''));
const toolCalls = events.filter((e) => e.type === 'tool_use').map((e) => e.part?.tool);
const unchanged = testsHash() === before;
const independent = unchanged ? spawnSync(process.execPath, ['--test'], { cwd: fixture, encoding: 'utf8', timeout: 60000 }) : undefined;
const summary = Object.fromEntries((independent?.stdout ?? '').split('\n').flatMap((line) => { const m = line.match(/^ℹ (tests|pass|fail) (\d+)/); return m ? [[m[1], Number(m[2])]] : []; }));
const outcome = {
  model, runID, fixture, exit: expired ? 124 : (code ?? 1), expired, launch_error: launchError, seconds: Math.round((Date.now() - started) / 1000), steps,
  tests_unchanged: unchanged, agent_ran_tests: shellRuns.length, tool_calls: toolCalls, independent_tests: summary,
  semantic_pass: unchanged && shellRuns.length > 0 && independent?.status === 0,
  independent_test_pass: independent?.status === 0,
  error_text: redact((output.match(/FreeTierError[^"\n]*|UpgradeRequired[^"\n]*|"statusCode":\s*\d+[^\n]{0,160}/) ?? [])[0] ?? ''),
};
writeFileSync(resolve(root, runID, 'outcome.json'), JSON.stringify(outcome, null, 2) + '\n');
console.log(JSON.stringify(outcome, null, 2));
process.exitCode = outcome.semantic_pass ? 0 : 1;
