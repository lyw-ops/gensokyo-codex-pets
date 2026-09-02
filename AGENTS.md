# Repository instructions

## Scope

Phase 1 is Hakurei Reimu only. Do not add another character implementation until the maintainers explicitly move the roadmap beyond Phase 1.

Milestone 0 is documentation-first. Do not generate final or placeholder Reimu art until the face system, proportions, palette, prop vocabulary, and atlas target have been reviewed.

## Source and asset rules

- Prefer current official sources for Codex behavior and format claims.
- Label shipped-app inspection as local implementation evidence and community findings as community/reverse-engineered evidence.
- Never present an old v1/v2 convention as current without rechecking it.
- Do not download or commit commercial sprites, official game materials, or third-party fan art.
- Do not trace or closely reproduce reference art. Use references to identify broad character traits and readability constraints only.
- Keep the fan-work notice visible in user-facing packaging.

## Architecture

Keep these layers independent:

1. visual assets under `pets/<pet>/design` and `pets/<pet>/sprites`;
2. Codex format/build/install compatibility in deterministic scripts or tools;
3. workload observation and `WorkloadLevel` classification in a runtime adapter.

Do not hardcode task-count thresholds throughout animation code. Use a configurable `calm | normal | busy | overloaded` abstraction.

Do not claim workload-reactive behavior unless it is driven by a documented, tested Codex interface. The current pet manifest is static and exposes no custom task-count hook.

## Current pet target

For local desktop v2 work, use the contract in `docs/codex-pet-format.md`: 1536×2288, 8×11 cells, 192×208 per cell, and `spriteVersionNumber: 2`. Treat 1536×1872 as v1 or the currently documented web-upload target, not as the final local v2 atlas.

Before committing sprite work:

- validate dimensions, transparency, occupied and unused cells, row order, and metadata;
- review animations at intended display size and with reduced motion;
- verify Reimu's identity, silhouette, palette, handedness, and props across every frame;
- record the source and permission status of every reference used.

## Handoff and GitHub synchronization

`HANDOFF.md` is the canonical cross-session project handoff. Read it immediately after this file at the start of every repository task.

For every repository-changing task:

- fetch or pull and inspect remote state before editing;
- update `HANDOFF.md` in the same commit as the implementation;
- record the real current milestone, completed work, decisions, next actions, validation, and blockers;
- run `./scripts/check-repository.sh` and any change-specific checks;
- review the diff, commit the change, and push the active branch to GitHub before reporting completion, unless the maintainer explicitly says not to push;
- verify the remote contains the commit and the local working tree is clean.

Never force-push. Never overwrite or discard another contributor's work to make synchronization easier. If push or validation fails, leave an explicit unsynchronized handoff with the branch, commit, blocker, and exact recovery step; do not claim the update is complete or available on GitHub.
