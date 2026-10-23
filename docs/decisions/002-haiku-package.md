# 002. Ship a Haiku package

Date: 2026-10-23. Status: accepted (alignment plan decision D9).

## Context

Upstream OpenCode ships through npm as `@opencode/cli`. Its package allows only
`darwin`, `linux` and `win32`, and it installs Bun-built binaries. Bun does not run on
Haiku. The port runs on Node 24 with Haiku-native addons.

## Decision

The primary form is a Haiku package (`opencode_haiku-<version>-1-x86_64.hpkg`) built by a
HaikuPorter recipe. `pkgman` installs and updates it. The recipe takes the release tar.gz
as its source, because the JavaScript bundle can only be built on Linux. The tar.gz stays
a release asset and a manual install. npm is not used.

## Consequences

Phase 2 adds `VERSION`, `make dist` and `packaging/`. `docs/design/packaging.md` gives the
design. The package is published only with the GitHub releases of this repository. It is not
submitted to HaikuPorts or any other Haiku project (README, "Disclaimer").
