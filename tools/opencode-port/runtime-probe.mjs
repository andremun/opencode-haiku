import assert from 'node:assert/strict'
import { mkdtemp, writeFile, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { spawnSync } from 'node:child_process'
const directory = await mkdtemp(join(tmpdir(), 'opencode-runtime-'))
const results = []
try {
  await writeFile(join(directory, 'input.txt'), 'Haiku runtime probe\n')
  assert.equal(await readFile(join(directory, 'input.txt'), 'utf8'), 'Haiku runtime probe\n')
  results.push('filesystem')
  const shell = spawnSync('/bin/sh', ['-c', 'printf runtime-shell-ok'], { encoding: 'utf8', timeout: 10000 })
  assert.equal(shell.status, 0)
  assert.equal(shell.stdout, 'runtime-shell-ok')
  results.push('subprocess')
  const sqlite = await import('node:sqlite')
  const db = new sqlite.DatabaseSync(join(directory, 'session.sqlite'))
  db.exec('PRAGMA journal_mode=WAL; CREATE TABLE session(id INTEGER, value TEXT);')
  db.prepare('INSERT INTO session VALUES (?, ?)').run(1, 'resume')
  const statement = db.prepare('SELECT id, value FROM session')
  statement.setReadBigInts(true)
  statement.setReturnArrays(true)
  assert.deepEqual(statement.all(), [[1n, 'resume']])
  db.close()
  results.push('sqlite-wal-and-array-results')
  const { registerHooks } = await import('node:module')
  assert.equal(typeof registerHooks, 'function')
  results.push('module-hooks')
  const response = await fetch('https://opencode.ai', { signal: AbortSignal.timeout(30000) })
  assert.equal(response.ok, true)
  await response.body.cancel()
  results.push('https')
  console.log(JSON.stringify({ passed: results, platform: process.platform, node: process.version }))
} finally {
  await rm(directory, { recursive: true, force: true })
}
