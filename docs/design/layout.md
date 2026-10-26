# Layout and code rules

This file states what the code of this repository must look like after Phase 2 of the
alignment plan (`haiku-k40c-llm/docs/refactor-spec.md`). Phase 2 is done when the
repository matches this file and the checks in Section 4 pass.

## 1. Directory tree

```text
opencode-haiku/
|-- README.md  AGENTS.md  LICENSE  CHANGELOG.md  VERSION  Makefile
|-- src/              # shipped: opencode launcher, install.sh, selftest, haiku-*.cjs shims,
|                     #          haiku-clipboard.cpp, haiku-futex.c
|-- build/            # build_bundle.sh, build_native.sh, build_parser.sh, package.py, guest build jobs
|-- packaging/        # HaikuPorter recipe
|-- patches/<upstream>/<name>.patch + series
|-- reference/INPUTS.json
|-- tests/
|   |-- unit/         # host tests: test_review_runners.py, test_t7610_runners.py, *-test.cjs, *.test.ts, C fixtures
|   `-- acceptance/   # guest workflows: api-workflow.mjs, persistent-terminal-api.mjs, coding-workflow.mjs,
|                     #   cloud-coding-task.mjs, probes; vm/ job scripts from tools/kvm-run/
|-- tools/secrets/
|-- examples/
|-- results/  docs/
```

## 2. File moves and removals

| From | To |
|---|---|
| `tools/tui-port/` shipped files (`opencode`, `install.sh`, `selftest.cjs`, `haiku-loader.cjs`, `haiku-ffi.cjs`, `haiku-watch.cjs`, `haiku-http.cjs`, `haiku-clipboard.cjs`, `haiku-clipboard.cpp`, `haiku-futex.c`) | `src/` |
| `tools/tui-port/build_*.sh`, `package.py`, `*_guest.sh` build jobs | `build/` |
| `tools/tui-port/` tests and fixtures | `tests/unit/` |
| `tools/tui-port/` workflows and probes | `tests/acceptance/` |
| `tools/tui-port/opencode.json` | removed (same as `examples/haiku-local-chat.json`) |
| `tools/opencode-port/` (headless `haiku.1`) | removed. Probes still used by acceptance move to `tests/acceptance/`. |
| `tools/kvm-run/` VM jobs | `tests/acceptance/vm/` |
| `tools/kvm-run/build-cpu-profile.sh`, `llama.sh`, `inf.sh`, `benchmark-cpu.sh`, `model.sh` and `reference/llama-cpu/` | `haiku-k40c-llm` (owner of the Haiku llama.cpp build) |
| `tools/app_vm.py`, `tools/transfer_server.py`, `tools/job.sh`, `tools/stage_t7610.py` | removed. Pin `haiku-k40c` `tools/haiku/` (ADR 004). |
| `reference/*.patch` | `patches/<upstream>/` |
| `reference/*-INPUTS.json`, manifests | `reference/INPUTS.json` |
| `results/opencode-tui-package.json`, `results/native-build-inputs.json` | `dist/MANIFEST.json` (not tracked, release asset) |

## 3. Code rules

- JavaScript: `'use strict'`, one concern per module, no build step for shipped shims, Prettier format.
- Python: PEP 8, one statement per line, module docstring, MIT header, ASCII only.
- Shell: POSIX `sh` with `set -eu`, `shellcheck` clean.
- C and C++: `-Wall -Wextra -Werror`.
- `make check`: unit tests, linters, secret scan, link check. No VM, no network, no GPU.
- `make test-vm`: acceptance checks in the persistent cardless VM (user step).
- CI: `.github/workflows/check.yml` runs `make check` on Ubuntu with Node 24.

## 4. Acceptance checks

1. `make check` passes locally and in CI. `tests/unit/test_t7610_runners.py` no longer fails on the empty test summary (H-02), or the failure has a documented cause.
2. `make dist` from a clean clone after `make fetch` and `make native` gives an archive and a manifest.
3. The archive installs in the persistent VM and passes the self-test and the checks of [ACCEPTANCE.md](../ACCEPTANCE.md).
4. The HaikuPorter recipe builds an `.hpkg` that `pkgman` installs.
5. `git grep -l '/home/unimelb.edu.au'` lists only `docs/history/` and `results/`.

## 5. As built (23 October 2026)

| Item | Result |
|---|---|
| Folders | Done: `src/`, `build/` (with `build/guest/`), `packaging/`, `patches/<upstream>/` with `series` files, `tests/unit/`, `tests/acceptance/` (with `vm/`). Guest scripts use the new paths under `$SRC`. |
| `tools/stage_t7610.py` | Kept, as `tests/acceptance/vm/stage_t7610.py` (`make stage`). It stages the archive and source for the VM. |
| Headless port | Removed (`tools/opencode-port/`, decision D8). No acceptance check used its probes. |
| VM tools | Removed. Tests that cover the shared job runner and transfer server load them from `$HAIKU_K40C_ROOT` and skip when that checkout is absent. |
| llama.cpp scripts | Moved to `haiku-k40c-llm` `results/20261018-community-comparison/scripts/` as records. `services.sh` still starts a guest llama.cpp server for the acceptance runs. |
| `VERSION` | Done. `build/build_bundle.sh` and `build/package.py` read it. |
| `reference/INPUTS.json` and `make fetch` | Done for the downloadable inputs. The older input records stay as provenance. In the cloud session, four of nine inputs downloaded and matched their hashes (Bun, Koffi, node-pty, node-addon-api). The proxy blocked the others. |
| `make native`, `make hpkg` | Not added. The native parts still follow docs/BUILD.md 10.2 to 10.4 in the VM. |
| `make dist` | Added: bundle, archive, `dist/MANIFEST.json`, `dist/SHA256SUMS`. Not run here (needs the caches and native parts). |
| Recipe | `packaging/opencode_haiku-2.0.29~haiku5.recipe`. Not built yet. |
| Defects | (1) The cloud task read the independent test summary only in the `spec` reporter format. Node can print TAP lines. Fixed. (2) A test of the job runner wrote into the repository `share/` folder. Fixed. |
| `make check` | Passes: lint (syntax of Python, shell, JavaScript), 3 + 19 host tests, install test, secret scan. |
| JavaScript format | Not changed. Prettier is not applied, to keep the diff of shipped shims small. |
| CI | `.github/workflows/check.yml` runs `make check` with Node 24. The tests that need `haiku-k40c` skip. |

