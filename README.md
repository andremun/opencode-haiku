# OpenCode on Haiku

Native OpenCode headless CLI, full OpenTUI interface and browser GUI on x86_64
Haiku with Node 24. A separate OpenAI-compatible model endpoint is required;
native Haiku llama.cpp CPU inference has been demonstrated with Qwen3 1.7B.
This repository is independent of the sibling driver and LLM repositories.

**Current port: 2.0.29-haiku.5.** Its packaged TUI terminal pane and WebPositive
terminal panel pass native functional checks, including resize, reconnect,
UTF-8, child exit and cleanup. Native clipboard paste also works. See
[Haiku.5 acceptance](docs/HAIKU5-ACCEPTANCE.md) and [current status](docs/STATUS.md), [T7610 KVM Haiku.5 results](docs/T7610-KVM-HAIKU5-RESULTS-20261016.md).

- [Complete installation and source build](docs/T7610-HAIKU-SETUP.md)
- [Install a prepared runtime](docs/INSTALL.md)
- [Manual T7610 next run and CPU comparisons](docs/T7610-NEXT-RUN.md)
- [Earlier real-model TUI/GUI acceptance](docs/TUI-ACCEPTANCE.md)
- [Reviewed T7610 results](docs/T7610-COMMIT-REVIEW.md)

With pinned source/toolchain/native inputs prepared, build on Linux:

```sh
sh tools/tui-port/build_bundle.sh
```

The ignored archive is written to `share/`; its checksum and native input
provenance are in `results/opencode-tui-package.json`. A Git clone includes code,
patches, instructions and evidence, but not archives, models, SDKs, caches or VM
disks. Use one shared backend per Haiku SQLite profile and attach GUI/TUI clients.

Haiku.5 functional checks ran in the cardless TCG VM. AVX/F16C and batch-size
performance tools are prepared for a manual T7610 run; no resulting speedup is
claimed. A prior model made the requested edit but omitted its shell test;
reliable autonomous coding remains unproven. Recursive watching, clipboard
images/primary selection and native Electron are unsupported. Browser tab styling
and emulated input/initialisation delays remain limitations. These CPU results
are not evidence of K40c compute support. No host sudo or GPU access is used.
