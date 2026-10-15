# Status

Updated 15 October 2026 (Australia/Melbourne). Independent OpenCode Haiku port.

## Latest T7610 result and review

Commit `0344fbb` records a full source rebuild on a cardless T7610 KVM VM:
Haiku hrev60207, two exposed E5-2620 v2 vCPUs, 8 GiB, host CPU model and
baseline CPU-only llama.cpp. See [run report](T7610-KVM-RESULTS-20261015.md),
[VM instructions](KVM-VM.md) and [commit review](T7610-COMMIT-REVIEW.md).

- Native llama tests, model controls, TUI prompt/exit/restore, WebPositive pairing
  and bidirectional shared-session updates are recorded as successful.
- File/shell/session, browser PTY API and persistent daemon API checks pass.
- Model-driven editing changed subtraction to addition; it did not run the
  required shell test. The final file passed the manually run immutable test.
- The packaged Haiku.4 TUI terminal pane **crashes** because its renderer lacks
  Ghostty VT. The committed experimental renderer patch works in a manual test,
  but is not applied by build_native.sh or included in the packaged archive.
- Browser terminal panel rendering and TUI clipboard paste were not exercised
  on the T7610. Earlier development clipboard/TUI evidence remains separate.
- The three-request direct inference wall total was shorter than on the earlier
  TCG platform, but hardware/cache differences prevent a KVM-only speed claim.
  Sequence 1 followed smoke inference (five cached tokens on its first request);
  sequence 2 began with zero cached tokens. Later prompts reuse shared prefixes.
- The T7610 first OpenCode exchange took 15m51s versus an earlier TCG 15m41s;
  no OpenCode speed improvement is established by those two observations.
- The T7610 full 54-test daemon claim requires a better capture: the saved retry
  log shows only nine passing service tests; the old pipeline masked Cargo's
  status. Earlier development has complete 54-test evidence on its own parser.

The review corrects hidden native/API failures, host guest-exit propagation,
atomic job/result publication, warm-up contamination, readiness/duplicate-start
checks and service credential preservation. Six host-only regression groups
pass, including injected failures and a local HTTP test server. These are
implementation controls, not a rerun of the Haiku VM or a rebuilt archive.
See results/t7610-review-runner-tests.log.

## Remaining work

1. Integrate the Ghostty renderer patch, rebuild/package and validate TUI
   terminal I/O, reconnect, resize, exit and cleanup through the actual archive.
2. Visually test the browser terminal panel and native TUI clipboard paste.
3. Rerun native Cargo tests and Clippy with full logs and reliable statuses;
   rerun the revised guest agent/service scripts and fresh-server benchmarks.
4. Measure batch-size and supported AVX variants separately if performance work
   continues. Guest CPU does not support AVX2/FMA/BMI2.

## Sources, installation and historical evidence

OpenCode is pinned at 34d8ded0c58dd66808c1d60e081e8c66da12a896, OpenTUI
0.5.17, Bun 1.4.2 (Linux build), patched Zig 0.16.0 and Koffi 3.3.3; native
Node is 24.21.0-1. Daemon 0.2.0 is pinned at
878aa26ab1916f8d41a0ccb90d55a372d01abf69, Ghostty parser at
ab0b9da9e88fcb4b0533a1854e84628f663930af. Manifests retain original and rebuilt
artifact hashes; results/opencode-tui-package.json describes the T7610 archive.

[T7610-HAIKU-SETUP.md](T7610-HAIKU-SETUP.md) contains the complete installation
and mixed Linux/Haiku source build; standalone llama patches and an example
configuration are committed. Runtime archives/models/SDKs/caches/disks are
ignored and must be transferred or regenerated. No sibling LLM repo is needed.
Historical reports: TUI-ACCEPTANCE.md, CONTINUATION-OUTCOME.md and
OPENCODE-HAIKU-PORT.md. Previous TCG coding timeouts were resource limits,
not observed incorrect patches or coding-quality acceptance failures.

## Boundaries and handoff

The recorded T7610 handoff shut down its VM and transfer service cleanly.
This review did not start/alter a VM or model service. No host sudo, physical
GPU, driver change or push was performed. All results are CPU/cardless and do
not establish K40c compute support. Native Electron, recursive watching and
clipboard images/primary selection remain unsupported. General coding
usefulness and reliability are not established by one successful edit.
