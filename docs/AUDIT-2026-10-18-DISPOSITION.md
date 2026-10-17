# Disposition of the 18 October 2026 audit report

Source: `opencode-haiku-audit-report.md` (static read of a ZIP snapshot; no code was run
by its author). Each finding was checked against this repository on 18 October 2026.
Fixes are covered by `tools/test_t7610_runners.py` (13 host-only tests, run with `NODE`
set to a Node 20+ binary when `node` is not on PATH).

| Finding | Verdict | Action |
|---|---|---|
| H1 transfer server accepts `.` and `..` | Valid but weaker than stated: `os.replace` onto an existing directory fails, so nothing is overwritten; the request errors. Leading-dot names were accepted. | Fixed: names must start with `[A-Za-z0-9_]`; test added |
| H2 two pins for `libghostty-vt.a` | Valid: `build_pty_guest.sh` accepted only the original hash, `kvm-run/native.sh` only the rebuild | Fixed: both accept either recorded hash (provenance in `reference/PTY-PORT-INPUTS.json`) |
| H3 probes lack spawn `error` handler; exit file `null` | Valid (historical probes) | Fixed in the three `*_model_probe.mjs` (exit 127 with error text; `code??1`) |
| H4 runner log never uploaded | Valid | Fixed in `run_api_guest.sh` (upload, non-fatal) |
| M1 stale `.4` launcher default | Valid | Fixed (`.5`) |
| M2 personal fallback path | Valid | Fixed: `NODE` env or PATH, otherwise a clear error |
| M3 Zig `pwrite` shim uses `iovecs[0]`; `.BUSY` mapped to `AccessDenied` | Partly valid: a first-buffer write is a legal short write for looping callers; only an empty first buffer is a risk. Affects the Zig *build* of the renderer, not the runtime. `.BUSY` mapping is imprecise | Not changed; noted |
| M4 `set -e` skips the `echo rc=` line | Valid but low: the job agent still reports the failing exit code | Not changed |
| M5 watcher keyed by inode; recursive not special-cased | **Incorrect**: the snapshot is keyed by name, and `recursive` already throws `ENOSYS` (`haiku-watch.cjs:10`) | None |
| M6 `.find()` unguarded in `browser_diagnostic.cjs` | Valid (temporary diagnostic) | Fixed (`?.`) |
| M7 missing archive crashes `stage_t7610.py` | Valid | Fixed; test added |
| M8 clipboard `options` unguarded | Callers always pass options; defaulting would not make `options.signal` valid | Not changed |
| M9 `app_vm.py` monitor/screen | **Mostly incorrect**: no monitor thread exists; the `width-1` division needs a 1-pixel screen | None |
| M10 example fixture `tools:false` vs measured `tools:true` | True drift, but intentional: the shared-backend chat example offers no tools to the 1.7B model; the coding fixture needs them | Not changed; noted here |
| Part 1 free-tier analysis | See [FREE-MODELS-AND-CLOUD-TASK.md](FREE-MODELS-AND-CLOUD-TASK.md); the version/header "gates" come from third-party write-ups and were not verified | Partly measured, partly open |
