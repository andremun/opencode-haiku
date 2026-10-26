# Changelog

## Port versions

| Version | Date | Change |
|---|---|---|
| `2.0.29-haiku.5` | 2026-10-15 | Ghostty VT renderer patch for Haiku. Packaged TUI terminal pane no longer crashes. |
| `2.0.29-haiku.4` and earlier | 2026-10-15 | Full TUI and browser workflow, native clipboard, HTTP waits, terminal backends |
| `2.0.29-haiku.1` | 2026-10-14 | Headless CLI on Haiku |

## Repository

- 2026-10-26: Review fixes. VM commands in `docs/KVM-VM.md` and `docs/DEVELOP.md` call the shared tools from `$HAIKU_K40C_ROOT`. The VM disk is in `~/haiku-vm`. The `series` files list only patches. `test_build_paths.py` also checks build Python files, guest and acceptance scripts and the `series` files. The secret scan reads `tests/acceptance/vm/` and staged renames. The TAP branch of the cloud summary parser has a control. Host controls H-01 to H-04 have an evidence folder.
- 2026-10-24: Build fix (PR 3). `build_bundle.sh`, `build_native.sh` and `build_parser.sh` read their 8 patches from `patches/` again (commit `26a9e97` had moved them). New `tests/unit/test_build_paths.py`.
- 2026-10-23: Review rules: `REVIEW.md`, the `/pr-review` skill (`.claude/skills/pr-review/`) and a "Review guidelines" section in `AGENTS.md` for Codex. `examples/README.md`. Stale H-02 row in `docs/STATUS.md` fixed.
- 2026-10-23: Alignment Phase 2 (code). New layout (`src/`, `build/`, `packaging/`, `patches/`, `tests/`). `VERSION`, `make check`, `make fetch`, `make dist`, HaikuPorter recipe, CI. Headless port and VM tool copies removed. Two test defects fixed.
- 2026-10-23: Alignment Phase 1 (documentation). Product README, ACCEPTANCE, KNOWN-LIMITATIONS, BUILD and DEVELOP guides (split from the T7610 setup guide), design folder with the packaging design, ADRs. Dated reports moved to `docs/history/`. Flat results grouped into dated folders. One-byte `.exit` files, empty files and duplicate logs removed. The Kepler compiler study moved to `llm-server`, the community comparison to `haiku-k40c-llm`, the ESC-001 evidence to `haiku-k40c`. LICENSE (MIT) added.
- 2026-10-21: Interactive TUI, second client and browser with a cloud model. Task E on ten free models. Coding uploads use per-run names.
- 2026-10-20: Final card window of the Kepler study (now in `llm-server`).
- 2026-10-19: Runner fixes with offline controls.
- 2026-10-18: Phases 1 to 3 of the continuation plan. Cloud task. Key handling. Audit disposition.
- 2026-10-16: Haiku.5 on the persistent KVM VM. Production-matching CPU build.
- 2026-10-15: Persistent KVM VM. T7610 results.
