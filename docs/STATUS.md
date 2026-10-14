# Status

Updated 14 October 2026. Independent working repository:
`/home/unimelb.edu.au/mariom1/Documents/packages/opencode-haiku`.

OpenCode source package 2.0.29 is pinned at
`34d8ded0c58dd66808c1d60e081e8c66da12a896`, port build `2.0.29-haiku.1`.
Bun 1.4.2 builds the bundle; native Haiku runs Node 24.21.0-1.

## Verified

- Native filesystem/subprocess, SQLite WAL/BigInts, module hooks and HTTPS.
- Lazy PTY loading fixes the baseline native-library launch failure.
- Native help/version, packaged launcher and archive checksum.
- Real file read/write, ripgrep fallback file search, shell assertions and
  stored session recovery across private server restart.
- Native CLI receives exactly OK from a separately hosted CPU-only Qwen3 0.6B
  model; Linux control matches.
- Real model-driven native read/shell calls and permission enforcement.
- Root lint and all 36 typecheck tasks pass (Turbo loose environment required
  to forward isolated XDG state to unrelated Astro checks).

## Unsuccessful and pending

- Free-model service returns HTTP 403 from both port and official Linux release.
- Initial 0.0.0 archive build label caused HTTP 426; corrected using upstream
  build-version settings. No client identity spoofing or paid fallback used.
- Initial one-step probe exhausted its budget before the first model call;
  corrected, with all unsuccessful logs retained.
- Tiny model failed the add-function edit/test task (semantic exit 2). Its
  invalid edits were rejected, and its attempted test overwrite was denied.
- Successful model-led mutation and resumed LLM conversation need validation
  with a more capable model. General coding usefulness is not established.
- OpenTUI/native PTY and filesystem watching remain unsupported.
- Source/build wrapper assembled from successful commands has not yet had a
  further clean rebuild; tested archive and launcher passed in a fresh guest.
- Independent copied VM booted successfully from the new repository; moved
  bundle --version and all recorded input hashes also pass.

## Resources

Original VM, transfer service, CPU test server and relay are stopped.
The copied cardless VM boot was verified and clean shutdown was requested.
No physical GPU or running host model service was changed. See
[the report](OPENCODE-HAIKU-PORT.md) and `reference/REPOSITORY-SPLIT.json`.
