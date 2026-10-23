# Rules for agent sessions in this repository

1. Read `docs/STATUS.md` first. Project state lives there, not in this file.
2. This repository is a standalone product. Building and running OpenCode on Haiku must not need the sibling repositories. A model endpoint is a separate service.
3. Use only a cardless VM. Never access, reset or pass through a physical GPU. Do not alter host drivers or running LLM services. Never use host sudo.
4. A CPU or cardless result is not GPU evidence.
5. Keep source archives, dependency caches, models, API keys and virtual disks outside Git (`docs/SECRETS.md`).
6. Put each run in a new folder `results/YYYYMMDD-topic/`. Add it to `results/README.md`. Update `docs/ACCEPTANCE.md` when a release check runs.
7. Update `docs/STATUS.md` and `CHANGELOG.md`. Put dated reports in `docs/history/`. Do not add parallel status notes.
8. Read the `AGENTS.md` of a sibling repository before you change it.
9. Write prose in ASD-STE100 style: short sentences, active voice, no semicolons.
10. Do not start subagents. Do not push without an instruction from the user.
