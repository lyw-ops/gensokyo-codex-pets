# GPT project handoff / GPT 项目交接

Last updated: **2026-09-03**

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
- Current milestone: **Reimu Layered Assets v1 — production tooling ready — task_2 intake validation ready — ART ASSET REQUIRED**. The final source-mode and layer-root protection gates are fixed. The read-only intake tool and exact asset pack are ready; **no real Reimu layer PNGs exist in the inspected repository or maintainer archive**. The v2 builder remains verified with synthetic fixtures only. Real task_2 static reconstruction, motion and visual QA have not started, and no layered runtime has been approved or published. The six published states remain flattened one-frame identity holds.
- Repository content: documentation, design constraints, behavior/action specification, metadata example, validation script, approved Eating Set v1 reference art (`docs/reference/reimu/eating_set_v1/`), six derived runtime sprites plus published animation manifests and validated frames (`assets/reimu/eating/`), the consumer animation spec (`pets/reimu/animations/eating/animation-set.json`), the layered asset contract (`docs/reimu-layered-assets-v1.md`, `pets/reimu/layers/eating/layer-set.json`, empty source tree `assets/reimu/layered/eating/`), the Sprite Harness build entry point and tests (`tools/build_reimu_animations.py`, `tools/test_build_reimu_animations.py`), the integration contract (`docs/sprite-harness-integration.md`), and the frames[]-playback preview app (`app/`).
- Animation pipeline status: **production pipeline live and hardened** against Sprite Harness 0.7.0 via its public CLI/JSON contract only (no harness modules imported or Harness changes). Configured layer roots are protected even for flattened-only runs. Repository validation accepts mixed source modes and rechecks exact applicable authored IDs, optional participation, PNG format/dimensions and per-layer SHA-256. The new `tools/check_reimu_layer_assets.py` reports READY or ART ASSET REQUIRED; READY certifies files only. Real v2 production still requires authored PNGs, positional calibration, static reconstruction and visual approval.
- Sprite status: six static 596×596 RGBA eating-state sprites (`idle`, `task_1`–`task_5`) remain the immutable sources; each state also carries `animation.json` + `frames/frame_000.png` (identity baseline, byte-identical to `base.png`). No multi-frame motion and no Codex atlas art exist yet — both are gated on future layered assets.
- Runtime status: **no workload adapter exists yet**; the preview app uses a manual debug task count only.
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
- Integrated Sprite Harness as the animation production and validation tool: consumer animation spec, deterministic build entry point (`plan → render → validate --write-qa → preview → contact-sheet → report`, all via the public CLI in `--json` mode with exit-code checks), staged fail-safe publication of `animation.json` + validated frames per state, strict runtime-manifest loading with explicit static fallback, frames[] playback with reduced-motion support in the preview app, extended repository checks (manifest/frame/digest integrity), a 14-test pipeline suite, and the integration contract document.
- Measured and documented the flattened-sprite motion limitation (whole-sprite translation moves the tatami ground line by the full amplitude) and shipped the identity baseline instead of fake motion.
- Fixed dual-mode runtime source validation and unconditional protection of the declared layer root, with regression checks for source-byte immutability. Delivered `docs/task-2-layer-asset-intake.md` and the read-only intake tool; inventoried available art and selected a single full-canvas export policy. No authored art, motion or runtime changes were fabricated.

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
- The six older GPT prototypes are internal composition evidence only. Do not commit, trace, crop, downscale, palette-sample, or reuse their pixels; do not carry their task signs or room background into the pet asset.
- Exception decided by the maintainer on 2026-09-02: the approved **Eating Set v1** sheet (their own generated concept art) is committed under `docs/reference/reimu/eating_set_v1/` and is the source of the runtime sprites. Reference art is never loaded at runtime; runtime code loads only `assets/reimu/eating/`.
- Runtime sprites are derived mechanically (`tools/split_eating_sheet.py`): alpha-connectivity panel segmentation, nearest-panel assignment of floating effects, bottom-center anchoring on a 596×596 transparent canvas; no repainting, no non-uniform scaling. Regenerate from an updated approved sheet instead of hand-editing `base.png` files.
- The task-count → eating-state mapping lives only in `app/task-state-mapping.js` (`0 → idle`, `1..4 → task_n`, `>= 5 → task_5`, negative/invalid → `idle`); the character model is `Character → StateSet → State → frames[]` (`app/characters.js`) so additional characters and future multi-frame animation extend data, not code.
- Animation production and validation go through Sprite Harness (`https://github.com/lyw-ops/Spirite-harness`, canonical contract `HARNESS.md`) using only its public CLI/JSON interface. Do not vendor or re-implement harness internals, do not add Reimu-specific logic to the harness core, and do not modify the harness from consumer tasks unless a reproducible harness bug is found.
- The task-count → state policy stays solely in `app/task-state-mapping.js`; the animation pipeline, manifests, and player never re-implement `min(taskCount, 5)`.
- Published runtime animation artifacts (`assets/reimu/eating/<state>/animation.json` + `frames/`) are produced only by `tools/build_reimu_animations.py` after harness validation passes; `base.png` is immutable source and doubles as the explicit static fallback. The runtime never reads `build/` (gitignored, disposable).
- The Eating Set v1 baseline is an identity hold (one validated frame per state). Whole-sprite motion on the flattened sources is rejected by measurement: the ground line moves with the full motion amplitude. Real local motion (breathing, chewing, blink…) is gated on explicit layered Reimu PNGs and Animation Plan v2 — never approximate layers from the flattened sprite (no segmentation, thresholding, bbox guessing, or inpainting).
- Layered Assets v1 contract (2026-09-03): layered sources live in `assets/reimu/layered/eating/` (immutable, never in `build/`). The layer-set declares 12 possible IDs, of which eight are required for the pilot; do not create empty layers to fill slots. Export **full 596×596 transparent RGBA canvases**, with parts in final composition coordinates (`canvas_policy: full_canvas`), replacing the earlier cropped-layer policy. Anchors/positions remain provisional and unchanged until real PNGs are inspected; do not use their historical translations as placement instructions for full-canvas exports. The exact pack, overlap/ownership guidance and calibration sequence are in `docs/task-2-layer-asset-intake.md`. Pilot remains `task_2`; no other-state expansion or atlas work in this task.
- Production order: intake file validation → calibrate real layer placements → static reconstruction using a temporary config and `--no-publish` → static visual approval → task_2 layered motion → animation visual approval → publish through the existing builder. Static and animated comparison must include 596 px, 192×208 cell context and especially 160 px. Initial motion target is 8 fps / 12 frames / loop with natural frame 0, restrained 1–3 px local displacement, stationary table/tatami/table food, and coordinated hand/held food. Blink/chew/head bob are conditional on visual quality, not mandatory effects.
- Blink/chew under the current harness v2 contract use complementary opacity cross-fades on explicit `eyes_open`/`eyes_closed` (and mouth) layers; if pilot QA at 160 px rejects the cross-fade, escalate as a reproducible harness feature request (discrete variant tracks), not a consumer renderer.
- Build safety invariants (enforced + regression-tested): the disposable build dir must never equal, contain, be contained by, or alias (relative path or symlink, on resolved paths) the source root, publish root, layered asset root, or any source sprite; all six states publish as one logical generation or every changed state rolls back; failed rollbacks leave `.publish-recovery.json` markers that `scripts/check-repository.sh` refuses; the runtime loader rejects manifests whose `character`/`state_set`/`state` do not match the state slot they are loaded for.
- The build pipeline is offline and deterministic; Sprite Harness M4 generation (paid provider calls) is never invoked implicitly and requires explicit maintainer authorization.
- `ReimuFoodTier`/`task_1..task_5` and the Codex v2 atlas rows are different state spaces; do not map food tiers onto Codex standard rows or claim task-count-driven Codex behavior. The future atlas path is documented in `docs/sprite-harness-integration.md` and requires new per-row visual assets.
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

Do these in order; do not skip ahead.

1. **ART ASSET REQUIRED** — follow `docs/task-2-layer-asset-intake.md`. Author eight full-canvas RGBA PNGs: `shared/tatami|body|head|table.png` and `task_2/eyes_open|mouth|hand_right|table_food.png`. Recommended optional: `eyes_closed` and `held_food`; `hand_left`/`effects` only when needed. Preserve both visible hands and held food through explicit ownership, even when separate optional files are absent.
2. Run `python3 tools/check_reimu_layer_assets.py` with a Python environment containing Pillow. Resolve every reported path/format issue. READY is not visual approval.
3. Inspect real alpha bounds/composition and calibrate provisional positions. Reconstruct statically via a temporary config and the existing builder with `--no-publish`. Review identity, occlusion, seams and ground line at 596 px, 192×208 and 160 px before touching production source_mode.
4. After static approval, enable task_2 layered v2 motion only. Build with `--no-publish`, review restrained motion, clean loop, connected grip and natural reduced-motion frame 0. Publish only after visual approval; rebuild twice and run mixed-source repository validation.
5. Stop at task_2 pilot validation for maintainer review. Do not expand the other five states or begin the Codex atlas without a subsequent task. Workload integration also remains separate.

## 8. Current handoff status

- Blocker: **ART ASSET REQUIRED** — all eight required pilot PNGs are missing. No authored layers were found in this consumer, the Harness workspace or the previously authorized maintainer archive (`~/Desktop/灵梦`). Static reconstruction: not run. Real task_2 Animation Plan v2: not produced. Visual QA: not run. Layered runtime publication: not performed. Six flattened identity runtimes are unchanged.
- Validation commands: `./scripts/check-repository.sh` and `python3 -m unittest tools.test_build_reimu_animations -v` (the integration tests need the `sprite-harness` CLI via PATH or `SPRITE_HARNESS_BIN`; they skip loudly when it is absent).
- Verified result: `repository scaffold checks passed`; **67 tests passed with no skips**, including the real Harness 0.7.0 CLI integration and the new mixed-source, path-protection and intake regressions. Used the existing Harness venv's Python/Pillow and CLI. `git diff --check` passed. The intake command correctly exits 1 with ART ASSET REQUIRED, lists all eight required paths, and separates four optional absences.
- Rebuild check: `python3 tools/build_reimu_animations.py` with the same sources and harness version must be a no-op diff (published output is byte-identical).
- Change-specific review: confirm all maintained documentation uses `ReimuFoodTier`, contains none of the removed four-range mapping or literal one-food-item-per-task rule, keeps the six GPT prototype files outside the repository, keeps `actions.json` labeled as a project-internal specification, keeps the incident chain marked design-only, keeps `base.png` byte-identical to its committed state after any rebuild, and keeps `app/task-state-mapping.js` as the only task-count policy.
- Uncommitted or unpushed work: check `git status` and GitHub before starting; this section must be updated if synchronization fails.
- Latest completed change: fixed the final two production gates, delivered the task_2 intake validator and asset pack, adopted full-canvas PNG exports while retaining unverified positions, and recorded the precise missing-art boundary. Six-state rebuild twice produced no runtime diff and left all base.png bytes unchanged. No Harness code, artwork, production animation config, or runtime artifact changes.

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

### 2026-09-03 — final production gates and task_2 intake boundary

- Started from fetched consumer main `6f60fc9` and Harness main `619d4a7`, both clean. Confirmed HARNESS.md and the layered v2 contract; no reproducible Harness bug or Harness edit was needed.
- Repository source validation now branches on `source.mode`. Flattened bindings retain the base.png rule; layered bindings require the official contract and recompute the current state-filtered, z-ordered source IDs. Present optionals must be bound, absent optionals must not be bound. Missing/unknown/duplicate/extra layers, stale SHA-256, unreadable/non-RGBA/incompatible PNGs and wrong layer-set paths fail. State selection and path resolution are shared with the existing builder.
- Builder loads any configured layer-set metadata before destructive work, even when all six requested states are flattened. Equal/inside/containing/symlink-alias layer-root build paths are rejected; tests prove no deletion/build invocation and unchanged source bytes.
- Added `tools/check_reimu_layer_assets.py` and `docs/task-2-layer-asset-intake.md`. Intake is read-only, does not render, calls no provider, and makes no visual-content judgments. PNG inspection uses Pillow; no Harness internals or new rendering backend were introduced.
- Inventoried the source tree and maintainer archive. Two archive PNGs match the committed sheet/single-render SHA-256; the other two PNGs are flattened concept sheets. No authored layers were available. Source images were only read, never cut apart or altered.
- Full 596×596 RGBA canvas policy replaces cropped exports for the pilot. No anchors/positions were guessed or promoted from provisional. The eight-file minimum and recommended eye/food variants are explicit; static reconstruction precedes production motion, and visual approval precedes publication.
- Verification: 67 tests passed, real CLI integration included; repository check and diff check passed. Six-state identity rebuild ran twice with no runtime diff. Intake returned the expected ART ASSET REQUIRED and exact eight missing required paths. Regression fixtures are synthetic and temporary, not final art.
- Result A: **Reimu Layered Assets v1 — production tooling ready — task_2 intake validation ready — ART ASSET REQUIRED**. Real static reconstruction, animation and visual QA are pending. Current runtime remains unchanged. Next owner: maintainer/art author supplies the PNGs in the intake pack.

### 2026-09-03 — pipeline hardening and Layered Assets v1 contract

**Phase A — consumer pipeline hardening (`tools/build_reimu_animations.py`, `app/`, `scripts/`):**

- Added a fail-closed filesystem boundary validator: before any `shutil.rmtree`, the disposable build directory is checked (on fully resolved paths, so `..`, relative aliases, and symlinks are caught) for equality, containment, or reverse containment against the source root, publish root, layered asset root, and every source sprite. Covered by 11 regression tests, including one proving `base.png` bytes survive a malicious `--build-dir` pointing at the source tree.
- Replaced per-state publication with a set-level transaction: stage all states → re-verify the staged package → commit state by state → on any failure roll back every state changed by the run. Six failure-injection tests prove the publish tree ends all-old or all-new, never mixed. A failing rollback writes `.publish-recovery.json`, preserves the staging directory (which still holds the previous generation), and raises an explicit error; `check-repository.sh` fails while a marker exists. `base.png` is never moved, backed up, or replaced by the transaction.
- Hardened the runtime loader: `app/characters.js` declares the state set's semantic binding and `app/animations.js` rejects any manifest whose `character`/`state_set`/`state` do not match the slot (verified in-browser: `task_3`'s manifest at `task_2`'s path falls back explicitly with "manifest state mismatch"). SHA-256 integrity remains a build/`check-repository.sh` gate by design — no crypto in the browser.
- Verified: `check-repository.sh` passes; 43 unit/integration tests pass; a full real rebuild of all six states publishes byte-identically (no git diff in `assets/`); loader re-verified in-browser with all six states `animated`.

**Phase B — Reimu Layered Assets v1 (contract + production system, art pending):**

- Established the layered source tree `assets/reimu/layered/eating/{shared,idle,task_1..task_5}/` (version-controlled authored PNGs only; never in `build/`; empty pending art) and the asset-production specification `docs/reimu-layered-assets-v1.md` (12-layer schema, per-layer includes/excludes/reason, 596×596 reference-canvas coordinate rules, z-order with the table-in-front occlusion, allowed/forbidden transforms — the tatami must never breathe — naming/alpha/provenance rules, pilot QA checklist).
- Added the machine-readable contract `pets/reimu/layers/eating/layer-set.json` (anchors, provisional positions, unique z, shared vs state scope, `{state}` path templating, optional layers); `check-repository.sh` validates its JSON, id/z uniqueness, canvas, and that the layered tree holds only PNGs/docs.
- Upgraded the single builder (no second builder) to two source modes: `flattened` (plan v1, unchanged, byte-identical output) and `layered` (`source_mode: "layered"` consumer key → Animation Plan v2 inline `source` composed from the layer set, `plan` invoked without `--source`, per-layer SHA immutability verification, layered manifest source binding). Missing required layer PNGs fail closed with `ART ASSET REQUIRED`. The runtime manifest format and app player are untouched — the player cannot tell v1 from v2 builds.
- The layered path is integration-tested end to end against the real sprite-harness 0.7.0 CLI using synthetic authored layers with a real local-motion track (4 distinct frames, deterministic rebuild, publish with layered source binding).
- Decision: pilot state is `task_2` (held food + table food + transitional expression; complex enough to exercise body/head/face/hand/prop decomposition, without the tier 5 banquet). Blink/chew use explicit variant layers with complementary opacity cross-fades under the current harness v2 contract; discrete variant tracks would be a future harness feature request if 160 px QA rejects the cross-fade.
- Explicitly NOT done, by policy: no layers derived from the flattened sprites, no placeholder/AI Reimu art, no M4 provider generation, no Codex atlas production (blocked on the non-eating action assets).
- Next owner: obtain maintainer review of the layer contract, then the **ART ASSET REQUIRED** pilot PNGs for `task_2` (exact list in `docs/reimu-layered-assets-v1.md` §Pilot); after committing them, measure real positions into `layer-set.json`, flip `task_2` to `source_mode: "layered"` with restrained pilot tracks, build, and run the QA checklist.

### 2026-09-03 — Sprite Harness integration and identity baseline

- First production use of Sprite Harness (`lyw-ops/Spirite-harness`, 0.7.0) as the animation build/validation tool, strictly through the public `sprite-harness` CLI/JSON contract; no harness core changes and no Reimu-specific harness logic were needed.
- Added the consumer animation spec `pets/reimu/animations/eating/animation-set.json` (shared defaults + per-state overrides, expanded deterministically into one legal Animation Plan per state — no six copy-pasted plans) and the build entry point `tools/build_reimu_animations.py` (`plan → render → validate --write-qa → preview → contact-sheet → report`, exit codes checked, `--json` everywhere, validation failure blocks publication, staged fail-safe publish, source SHA verified unchanged, harness version + plan digest recorded).
- Published per-state runtime artifacts `assets/reimu/eating/<state>/animation.json` + `frames/frame_000.png` for all six states; `base.png` remains immutable and repeated builds are byte-identical.
- Decision: the baseline is an **identity hold** (one validated frame per state). A restrained whole-sprite breathing experiment (±2 px translate_y) validated cleanly but measurement showed the tatami ground line moving by the full amplitude with the table and food — whole-scene bobbing reads worse than a stable still at 160 px. Local eating motion requires explicit layered source assets (Animation Plan v2); recorded in `docs/sprite-harness-integration.md` together with the future Codex-atlas boundary (food tiers are not Codex rows).
- Upgraded the preview app: strict manifest loader (`app/animations.js`), token-guarded single frame player with per-frame durations/loop, reduced-motion support (OS preference + QA toggle), instant state switching without flicker, and explicit logged/visible fallback to `base.png` on missing or malformed manifests. `app/task-state-mapping.js` is untouched.
- Extended `scripts/check-repository.sh` (manifest integrity: contiguous numbering, per-frame digests, reduced-motion frame, source binding, 596×596 RGBA frames) and added `tools/test_build_reimu_animations.py` (14 tests: spec composition, harness discovery errors, manifest determinism, publish rollback, end-to-end + determinism + validation-failure integration tests against the real CLI).
- Verified in-browser: all six states load as `animated`, task-count edge values map correctly, playback cycles frame order exactly and stops on state switch, non-loop states hold the last frame, reduced motion holds the declared still, missing/malformed manifests fall back with explicit status.
- Next owner: get maintainer review of the identity baseline, then produce explicit layered Reimu PNGs and move the eating states to Animation Plan v2 local motion; do not fake layers from the flattened sheet and do not invoke harness M4 generation without explicit authorization.

### 2026-09-02 — Eating Set v1 static prototype

- Inventoried the maintainer's local design archive (`~/Desktop/灵梦`); selected the approved 1254×1254 six-panel transparent sheet (low table + tatami + chin-in-hands idle) as Eating Set v1 and its companion task_1 single render as reference; rejected two superseded concept sheets and five downloaded third-party fan-art files (the latter are barred from the repository by `AGENTS.md`).
- Committed the approved sheet and companion render under `docs/reference/reimu/eating_set_v1/` with provenance notes, per explicit maintainer instruction.
- Wrote `tools/split_eating_sheet.py` (deterministic alpha-connectivity segmentation; panels 5/6 touch at the tatami corners and are separated by an erosion-seeded nearest-seed split; hearts/sweat/steam/sparkles assigned to nearest panel; 596×596 bottom-center-anchored transparent canvases) and generated `assets/reimu/eating/{idle,task_1..task_5}/base.png`.
- Built the static preview app (`app/`): `Character → StateSet → State → frames[]` registry, the single task-count→state policy boundary in `app/task-state-mapping.js`, and a debug task provider (buttons −1/0–6/10, numeric input, keyboard, `?tasks=N`), plus display-size and background QA toggles. No animation, per milestone scope.
- Extended `scripts/check-repository.sh` to require the new files and validate all six sprites as 596×596 RGBA PNGs.
- Next owner: get maintainer review of the six runtime states at pet size, then plan animation frames and the real workload adapter; do not claim live Codex integration.

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
