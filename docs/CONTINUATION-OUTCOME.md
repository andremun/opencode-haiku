# Continuation outcome

15 October 2026. Cardless Haiku hrev60207, native Node 24.21.0-1,
llama.cpp CPU, Qwen3 1.7B Q4_K_M. No host sudo or GPU work.

## Fresh inference comparison

The same three requests were sent sequentially to an isolated Linux CPU control
on localhost:18085 and native Haiku localhost:18081. Each request had one user
message, temperature 0, seed 1234, maximum 64 tokens and thinking disabled.
The same checksum-verified weights and previously built llama.cpp source baseline
were used. No existing host model service was changed.

| Fresh prompt | Linux | Haiku | Response |
|---|---:|---:|---|
| Reply with the single word OK | 7.70 s | 9.01 s | `OK` |
| Python add(a,b), code only | 18.22 s | 125.59 s | Identical fenced function returning `a + b` |
| 7 plus 5, number only | 9.63 s | 79.42 s | `12` |

All request bodies and response messages match. These are small functional
controls, not a general equivalence proof or a cold-start speed benchmark.
Server caches differed, notably on the first request. The earlier GUI follow-up
returning OK does not reproduce in a fresh conversation. Conversation effects
are plausible, but the original response's cause is not established.

Evidence: `results/inference-compare-{linux,haiku}.json`.
Command: `node tools/tui-port/inference-compare.cjs ENDPOINT OUTPUT.json`.

## Native clipboard and installation

Build `2.0.29-haiku.3` adds a text clipboard backend to the real OpenTUI factory.
A small C++ helper uses BClipboard and preserves UTF-8 and newlines exactly.
It accepts data through stdin, rather than interpolating text into shell commands.
The Node backend bounds reads, supports cancellation/deadlines and releases
children before disposal. Primary selection and images remain unsupported.

Native backend regression passes: exact UTF-8/newline round trip, read size limit,
unsupported selection/MIME, pre-abort, clear and disposal. The test restores the
previous text clipboard. `results/clipboard-test.log` records the result.

The initial archive lost the executable mode when the binary was downloaded;
its fresh installation failed the clipboard check. Package generation now sets
0755 explicitly. A second fresh installation passes version, FFI getpid, watcher
change and clipboard-read self-tests. The actual OpenTUI factory also passes
native read/write (`results/clipboard-integrated.log`). See `results/clipboard-install{,2}.log`.

The installer verifies an explicit SHA-256, requires native Haiku Node >=24,
refuses an existing destination, and cleans a partial failed installation.
Host tests check checksum rejection, success, preservation and failure cleanup.
The archive and each native binary are pinned in `results/opencode-tui-package.json`.
The final TUI restores the saved session; native Command-V (Alt-V in the QEMU
console) pastes the clipboard text into its prompt without submission. See
`results/tui-native-clipboard.png`.

## VM performance

There is no host `/dev/kvm`. Using KVM therefore requires host configuration
outside this task's no-sudo scope. The guest's memory survey shows roughly
3.99 GB free of 4.29 GB and no needed-memory pressure. That survey preceded the larger concurrent coding/API workload. The guest
serial subsequently reported critical low-resource pages and delayed console/
transfer completion. The affected tests do not establish semantic failures.
A graceful guest shutdown was requested before increasing RAM to 8 GiB and
reducing native prompt batches (128 logical / 32 physical), CPU polling and
prompt-cache allowance. CPU count remains two; no throughput gain is presumed.

## Persistent terminal dependency

The [official daemon](https://github.com/anomalyco/opencode-pty/tree/443945a666cad3b0c00da0c1c9f2bcd5bc00e28a)
was inspected at `443945a666cad3b0c00da0c1c9f2bcd5bc00e28a` (version 0.3.1).
It requires Rust 1.90 / edition 2024 and a pinned Ghostty terminal parser at
`ab0b9da9e88fcb4b0533a1854e84628f663930af`. Its `build.rs` cross-target match
has no Haiku branch. Its release platform matrix has no Haiku binary.
OpenCode's pinned dependency is 0.2.0; adopting 0.3.1 would also require an ABI/
protocol compatibility audit, not just changing the available-platform flag.

The [HaikuPorts Rust recipe](https://github.com/haikuports/haikuports/blob/master/dev-lang/rust/rust-1.79.0.recipe)
currently names 1.79 and marks x86_64 unsupported. The guest has neither rustc
nor cargo installed; its repository lists rust_bin but no Zig package. However, a subsequent native `pkgman search -D rust_bin` confirms
Rust 1.94.1-1 for x86_64. The older source recipe does not describe the available
binary. This removes the presumed compiler-version blocker; native installation
and upstream parser/daemon compatibility are being probed. `reference/CONTINUATION-INPUTS.json`
pins the retrieved source bytes; `results/pty-toolchain-survey.log` records the
native inventory.

Haiku's installed headers expose openpty/forkpty. That establishes an OS API,
not a working OpenCode persistent-terminal service. A correct port must preserve
bounded replay, authoritative terminal parsing, resize, child exit versus EOF,
owner handoff and teardown. A pipe-backed shell replacement would not deliver
those semantics. The remaining work is the upstream parser/daemon compatibility port; a new
compiler bootstrap is not presumed necessary.
Ordinary shell tools do not require that daemon.

## Real coding workflow

A disposable native fixture starts with an incorrect add.mjs and an immutable
test.mjs. Its private XDG profile permits reading *.mjs, editing add.mjs and
running only `node test.mjs`. Native Qwen3 1.7B is selected, tools enabled,
four agent steps, 4096 context, 256 response tokens and a 45-minute bound.
The model received a 1426-token prompt. Final results are recorded separately;
semantic success is distinct from transport or tool implementation success.

Reproduce with `node tools/tui-port/coding-workflow.mjs /boot/home/opencode-acceptance`.
Do not run against a live state profile owned by another backend.

## Long CLI waits

The first coding attempt failed after five minutes with `Transport: fetch failed`,
before any tool result. Upstream's CLI passes Bun `timeout:false` to fetch while
waiting for a session. Node ignores that Bun-specific property. The Haiku loader
now maps this explicit option to Undici headers/body timeout 0; ordinary requests
keep defaults and AbortSignal cancellation remains active. Pinned Undici 7.29.0
is bundled from the upstream lockfile. Both host and native negative controls
show that the default times out, the explicit unlimited request succeeds, and an
aborted unlimited request still rejects. Native final archive installation and
self-test pass with the new transport. The coding request was retried with a fresh
private profile; its result is separate from the first failed transport attempt.

Reproduction: `sh tools/tui-port/build_http_tests.sh`, followed by native
`node http-test/http-test.cjs`. Record current archive hash before installing.

## Recovered sequential controls

After recovery to 8 GiB, the native PTY primitive test passes controlling tty,
input/output, UTF-8, resize, EOF and exit status. The final OpenCode archive's
actual file write/read, portable file search and shell API pass. Its Node test
prints API_SHELL_PASS and exits 0; the saved session and source persist after a
clean backend restart. These are native implementation controls without an LLM,
recorded in results/final-api-probe.log and .exit. The pre-recovery partial API
log contained only NUL bytes and is not accepted as a result.

The post-recovery coding attempt also reached the explicit 45-minute bound
before finishing prefill and making a tool call. Source stayed unchanged.
Its outcome is in results/native-coding-outcome.json (exit 124, expired=true).
This is a bounded environment result, separate from coding semantics and the
passing native tool implementation controls. The model process was then
selected for cleanup by its recorded PID and expected binary command.
