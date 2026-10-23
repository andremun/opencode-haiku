# Haiku package

`opencode_haiku-<version>.recipe` is a HaikuPorter recipe. It turns the release archive
into `opencode_haiku-<version>-1-x86_64.hpkg`. The package is published only with the
GitHub releases of this repository. It is not submitted to HaikuPorts (README, "Disclaimer").

Steps for a release (user steps in the Haiku VM, not tested yet):

1. `make dist` on Linux. It writes the archive and `dist/SHA256SUMS`.
2. Put the archive SHA-256 into `CHECKSUM_SHA256` of the recipe.
3. In the Haiku VM: `haikuporter --no-source-packages -S opencode_haiku` from a ports tree
   that holds this recipe under `dev-util/opencode_haiku/`.
4. `pkgman install` the result, then run `opencode --version` and the acceptance checks
   of `docs/ACCEPTANCE.md`.
