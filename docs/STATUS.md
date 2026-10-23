# Status

Updated: 23 October 2026.

## Current release candidate

| Item | Value |
|---|---|
| Version | `2.0.29-haiku.5` |
| Recorded archive | `opencode-haiku-tui-2.0.29-haiku.5.tar.gz`, 53,682,981 bytes, SHA-256 `b9970cd8...f2` (`results/opencode-tui-package.json`) |
| T7610 rebuild | SHA-256 `9cbd07c5...`, not byte-identical: different SDK, Koffi and renderer inputs (`history/20261016-t7610-kvm-haiku5-results.md`) |
| Acceptance | Every check in [ACCEPTANCE.md](ACCEPTANCE.md) passed at least once. One host control fails in the cloud session (H-02). |
| Release | None published. No `.hpkg` yet. |

The field `acceptance` in `results/opencode-tui-package.json` still says "pending". The
packaging script wrote it before the acceptance runs. Phase 2 replaces that file with a
release manifest ([design/packaging.md](design/packaging.md)).

## Open items

| ID | Item | Next step |
|---|---|---|
| P-01 | `make fetch` and `make dist` exist. Four native parts are still built in the guest and copied by hand. | Script the guest builds (`make native`). |
| P-02 | Haiku package (`.hpkg`, decision D9). The recipe is in `packaging/`. | Build it in the VM after the first release archive. |
| P-03 | Choose the release archive: the recorded build or the T7610 rebuild | Rebuild with `make dist`, then run the acceptance checks |
| P-05 | Second-client TUI reconnect after a backend restart, more than 2 vCPUs, repeated runs | Test runs in the KVM VM |
| P-07 | Sandbox question: is Haiku a suitable sandbox for an agent that tests scientific software (GNU Octave, scientific Python, R)? Haiku has little user separation, so the VM is the main boundary. | Check which of these packages exist for Haiku. Compare VM-level limits with limits inside Haiku. Research only. |

## Alignment plan

The four-repository plan is in `haiku-k40c-llm/docs/refactor-spec.md`. Phase 1
(documentation) and Phase 2 (code) are done here. Steps for the VM: move the VM disk to
`~/haiku-vm` (or set `HAIKU_PERSISTENT_VM_DIR`), and give the guest a new source copy (`make stage`). Older status text: `history/20261021-status.md`.
