# GPT project handoff / GPT 项目交接

Last updated: **2026-09-02**

This is the canonical handoff entry for Gensokyo Codex Pets. Every GPT or human contributor should read this file and `AGENTS.md` before changing the repository, then update this file in the same commit as their work.

本文档是 Gensokyo Codex Pets 的固定交接入口。每一位 GPT 或人类维护者在修改仓库前都应先阅读本文档和 `AGENTS.md`，并在同一个提交中同步更新本文档。

## 1. Repository synchronization

- Remote: `https://github.com/lyw-ops/gensokyo-codex-pets.git`
- Primary branch: `main`
- Synchronization policy: repository updates must be committed and pushed to GitHub before the task is reported complete, unless the maintainer explicitly says not to push.
- Safety policy: pull/fetch before assuming remote state; never force-push; never discard another contributor's work.
- Source of truth: the latest successfully pushed commit on GitHub. Verify it with `git status`, `git log -1`, and `git ls-remote origin` rather than storing a self-invalidating commit hash in this document.

If a push cannot be completed, do not claim the handoff is synchronized. Record the blocker, local branch, unpushed commit, validation result, and exact next command in Section 8.

## 2. Read order for a new GPT

1. `AGENTS.md` — binding repository scope and safety rules.
2. `HANDOFF.md` — current state, decisions, and next actions.
3. `README.md` — project overview.
4. `docs/roadmap.md` — milestone sequence.
5. `docs/codex-pet-format.md` — current compatibility evidence.
6. `docs/reimu-design.md` and `pets/reimu/design/visual-spec.md` — Phase 1 design constraints.
7. `docs/reimu-action-system.md` and `pets/reimu/metadata/actions.json` — behavior system, FSM, and action catalog.
8. `docs/workload-food-system.md` — future workload abstraction and current limitations.

Recommended startup checks:

```bash
git status --short --branch
git remote -v
git fetch origin
git log --oneline --decorate -5
./scripts/check-repository.sh
```

## 3. Current project state

- Project phase: **Phase 1 — Hakurei Reimu only**.
- Current milestone: **Milestone 0 specification extended with the full Reimu behavior/action system; awaiting maintainer review of the action system and the earlier visual-direction decisions before Milestone 1 art work**.
- Repository content: documentation, design constraints, behavior/action specification (`docs/reimu-action-system.md`, `pets/reimu/metadata/actions.json`), metadata example, and validation script.
- Visual-reference status: six maintainer-provided GPT composition prototypes were reviewed locally and remain outside the repository.
- Sprite status: **no Reimu sprite art exists yet**.
- Runtime status: **no workload adapter exists yet**.
- Installation status: **no installable pet package exists yet**.
- GitHub status: `main` is the synchronized project branch; verify the latest commit against `origin/main` at the start and end of every task.

## 4. Completed work

- Connected the local repository to the requested GitHub remote on `main`.
- Verified the newly created remote and fetched its state without force or destructive commands.
- Created the project scaffold, fan-work notice, repository instructions, and roadmap.
- Replaced the obsolete four-range workload concept with the discrete `ReimuFoodTier = 0 | 1 | 2 | 3 | 4 | 5` design.
- Specified exact task-count mapping for tiers `0` through `4`, the `5+` visual cap, six meal-density composition plates, and count-preserving fallback semantics.
- Reviewed six maintainer-provided GPT visual prototypes and recorded their provenance, permitted internal use, excluded elements, and high-level composition lessons without committing the images.
- Documented a provisional face, proportion, palette, silhouette, and pixel-production specification.
- Researched the current Codex pet format using public OpenAI documentation, the OpenAI-bundled `hatch-pet` contract, and read-only inspection of the installed desktop app.
- Added a non-installable v2 manifest example and a repository validation script.
- Added this persistent GPT handoff and GitHub synchronization protocol.
- Surveyed nine open desktop-pet/Shimeji projects for behavior architecture (priority ladders, state classes, transition locks, autonomous schedulers, sleep chains, click escalation, drag handling) and recorded the adopted patterns.
- Audited Reimu's first-party characterization against original official texts (game omake/manuals, PMiSS, ZUN print works), separating canon, inferred, and fanon traits.
- Authored the Reimu action system: a two-axis `WorkloadState × CharacterBehavior` model, a priority-banded FSM with base/transient/transition/held state classes, an autonomous scheduler with cooldowns, a sleep chain, interaction reactions, drag-as-flight, a design-only incident chain, a reusable eating vocabulary, and the locked tier 0–5 emotion progression.
- Registered all 35 actions in `pets/reimu/metadata/actions.json`, explicitly marked as a project-internal behavior specification rather than a Codex manifest.
- Extended `docs/reimu-design.md` (standard Codex actions vs. extended behavior vocabulary) and `pets/reimu/design/visual-spec.md` (per-action-category silhouette, expression, prop, and consistency constraints).

## 5. Decisions currently in force

### Product and art

- Phase 1 contains Reimu only.
- Art must be original fan-made work; do not extract or copy commercial sprites or third-party fan art.
- Do not generate placeholder or final art before the maintainer approves the visual system.
- Reimu must read through black hair, a large red bow, a red-and-white shrine maiden outfit, controlled chibi proportions, and a manually consistent face system.
- Cozy food and low-table humor may be inspired by the atmosphere of Touhou Mystia's Izakaya, but its assets and layouts are not source material.

### Technical

- Local desktop target: Codex pet v2, 1536×2288, 8×11 grid, 192×208 cells, `spriteVersionNumber: 2`.
- Public web upload is a separate compatibility target currently documented as 1536×1872.
- Keep visual assets, Codex compatibility, and workload observation as separate layers.
- Use `ReimuFoodTier = 0 | 1 | 2 | 3 | 4 | 5`; do not reintroduce named workload ranges.
- With a valid source, map tier as `min(activeTaskCount, 5)`: tiers `0` through `4` are exact and tier `5` means five or more. Preserve the uncapped observed count outside the visual tier.
- A tier selects an overall meal composition; food-item counts do not need to equal active-task counts.
- The six-plate family progresses from tea-only repose at tier `0`, through increasingly rich meals at tiers `1` through `4`, to a table-filling comic banquet at tier `5`.
- Preserve recurring tea and held-onigiri anchors where state semantics permit, while increasing dish variety and occupied tabletop area at each tier.
- The GPT prototypes are internal composition evidence only. Do not commit, trace, crop, downscale, palette-sample, or reuse their pixels; do not carry their task signs or room background into the pet asset.
- Unavailable or invalid activity data selects tier `0` as an explicitly degraded fallback and must not be reported as an observed zero.
- The current custom-pet manifest does not expose active-task, workflow, tool, or subagent counts. Do not claim live workload behavior until a supported and tested interface exists.

### Behavior and action system

- Reimu's behavior is `WorkloadState (ReimuFoodTier) × CharacterBehavior (FSM node)`; task count never selects an individual animation directly.
- The FSM uses priority bands `FAILED > INCIDENT > REACTION > DRAG > REVIEW > WORKING > AUTONOMOUS > SLEEP > IDLE`; transient actions return to the *current base state* (`returnTo: "base"`), never unconditionally to idle; an unknown node falls back to `idle_relaxed` with logging.
- Core temperament contrast: lazy/unhurried at rest, instantly competent when something happens. Pacing principle: **Reimu should feel alive, not busy** — autonomous one-shots have per-action cooldowns and a global 20–45 s floor, and "do nothing" is the most likely scheduler outcome.
- Sleep is a chain (`idle_yawn → doze_nod → sleep_table`, exit only via `wake_up`), entered only at tier 0 after ~5 minutes of inactivity; no "Zzz" text or floating symbols.
- Locomotion is low-altitude flight; drag is `drag_float` (composed floating, never limp dangling) plus `drag_land`.
- The incident chain (`incident_notice → incident_ready → incident_fly`) is **design-only**: no supported urgent-event trigger exists in Codex today and the registry marks it accordingly.
- The tier 0–5 emotion progression is locked and monotonic: 0 unhurried boredom, 1 crying-while-eating (absurd relief, food restrained), 2 residual tears but visibly easier, 3 openly content, 4 clearly happy (one small sweat cue at most, never fatigue), 5 laughing-while-crying banquet ("how is there this much food", not work collapse).
- Eating uses a shared body construction plus a tier-specific table-composition layer and small expression differences; sprite production must not multiply by six tiers.
- `pets/reimu/metadata/actions.json` is a project-internal behavior specification for future tooling; it is not a Codex manifest and must not be presented as one. Codex-mappable actions vs. extended-runtime actions are separated in `docs/reimu-action-system.md` section 9.

## 6. Open decisions requiring maintainer review

- Review and approve the Reimu action system (`docs/reimu-action-system.md`): the FSM priority bands, the 35-action catalog, the sleep chain, interaction reactions, drag-as-flight, the design-only incident chain, and the autonomous pacing values (cooldowns, sleep-entry delay).
- Approve or revise the 96×104 logical grid with 2× nearest-neighbor export.
- Approve Reimu's neutral silhouette and head-to-body ratio.
- Approve the manually controlled face grid and expression set.
- Approve or revise the provisional palette in `pets/reimu/design/visual-spec.md`.
- Approve the low-table footprint, recurring prop anchors, exact dish vocabulary, expression arc, and tier `0` through tier `5` meal-density plates.
- Decide which prototype foods survive simplification at intended pet size, especially the large hot dish used to distinguish tiers `4` and `5`.
- Decide whether left/right movement should use low-altitude flight and whether mirroring is safe.
- Decide how visual references will be reviewed without committing copyrighted images.

## 7. Next actions

Do these in order; do not skip directly to a full sprite sheet.

1. Maintainer reviews the action system and the prototype-informed Milestone 0 six-tier specification, plus the open decisions above.
2. Audit and register specific official or officially licensed Reimu references as links and study notes only.
3. Produce an original reviewable model sheet for silhouette, face anchors, palette, table, recurring prop anchors, and all six meal-density compositions; do not transform the GPT prototype pixels.
4. Obtain explicit approval of that model sheet.
5. Only then begin original standard-row sprite production and deterministic v2 validation.
6. Investigate workload integration separately; a static sprite prototype must not pretend to react to task count.

## 8. Current handoff status

- Blockers: none for repository synchronization.
- Validation command: `./scripts/check-repository.sh`
- Expected result: `repository scaffold checks passed`
- Change-specific review: confirm all maintained documentation uses `ReimuFoodTier`, contains none of the removed four-range mapping or literal one-food-item-per-task rule, keeps the six GPT prototype files outside the repository, keeps `actions.json` labeled as a project-internal specification, and keeps the incident chain marked design-only.
- Uncommitted or unpushed work: check `git status` and GitHub before starting; this section must be updated if synchronization fails.
- Latest completed change: authored the Reimu action system (behavior research, canon audit, FSM, 35-action catalog, machine-readable registry) and integrated it into the design and visual specifications.

## 9. Required update procedure

For every repository-changing task:

1. Fetch/pull the current remote state and inspect the working tree before editing.
2. Read `AGENTS.md` and this document.
3. Make only the scoped changes and preserve unrelated work.
4. Run proportionate validation, including `./scripts/check-repository.sh`.
5. Update Sections 3–8 of this document so the next GPT sees the real state, decisions, completed work, next actions, blockers, and validation.
6. Review `git diff` and `git status`.
7. Commit the implementation and its handoff update together.
8. Push the active branch to GitHub. Use `main` unless the maintainer has requested a branch/PR workflow.
9. Verify the remote contains the new commit and the local working tree is clean.

Never mark a task complete while material repository changes exist only in a local working tree.

## 10. Handoff log

### 2026-09-02 — Reimu action system and behavior FSM

- Surveyed Ice-teapop/desktop-pet, clawd-buddy, clawd-on-desk, kokoronoka/desktopPet, He2y/desktop_pet, Shimeji-ee/Shimeji-Desktop, Adrianotiger/desktopPet, and vscode-pets for behavior architecture only; adopted patterns are documented with sources in `docs/reimu-action-system.md` section 2.
- Audited Reimu's first-party characterization (game omake/manual texts, PMiSS, IaMP profile, ZUN print works) and recorded a canon/inferred/fanon table; poverty-mania and other flanderizations are explicitly excluded.
- Added `docs/reimu-action-system.md`: two-axis model, priority-banded FSM, base-state return rule, transition locks, autonomous scheduler pacing, sleep chain, interaction set, drag-as-flight, design-only incident chain, locked tier emotion progression, Codex-standard vs. extended action split, and sprite-economy strategy.
- Added `pets/reimu/metadata/actions.json` (35 actions, project-internal specification) and extended `docs/reimu-design.md`, `pets/reimu/design/visual-spec.md`, `docs/references.md`, and `scripts/check-repository.sh` accordingly.
- Next owner: obtain maintainer review of the action system and pacing values, then proceed to the Milestone 1 model sheet; do not begin sprite production or claim extended-runtime support.

### 2026-09-02 — GPT composition-prototype review

- Reviewed the six local GPT-generated images labeled from `0 tasks` through `5 tasks`; the originals remain outside the repository.
- Corrected the earlier literal serving-slot interpretation: task count selects a meal-density composition rather than an equal number of visible food items.
- Recorded the tea-only tier `0`, eating transition at tier `1`, growing meal scale through tier `4`, and comic table-filling tier `5` direction.
- Excluded prototype task signs, full backgrounds, environmental decorations, glossy face treatment, and source pixels from the final pet asset.
- Next owner: approve the simplified prop set and expression arc, then author an original cell-scale model sheet.

### 2026-09-02 — discrete Reimu food-tier correction

- Removed the former four-range workload model from repository instructions and maintained documentation.
- Established exact tiers `0` through `4` plus capped tier `5` for five or more active tasks.
- Defined six stable food composition plates, centralized selection and degraded fallback behavior, and tier-specific future acceptance tests.
- Kept the existing technical limitation explicit: the current static Codex pet manifest cannot receive task counts or select these variants live.
- Next owner: review the six-tier composition system and remaining Milestone 1 visual decisions before producing art.

### 2026-09-02 — Milestone 0 and persistent handoff baseline

- Established the initial repository and Reimu-first documentation scaffold.
- Recorded current Codex v1/v2 findings and the lack of a native custom workload-count hook.
- Added the root handoff document and required GitHub synchronization workflow.
- Next owner: obtain maintainer decisions in Section 6 before creating Reimu art.
