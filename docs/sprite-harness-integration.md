# Sprite Harness integration

Status: **task_2 chew-v9 exact source activated and published as a validated
16-frame runtime; chew-v7 and the preceding fallback are retained as legacy; four Codex v2
rows remain separately approved; full atlas incomplete**

This document describes how `gensokyo-codex-pets` consumes
[Sprite Harness](https://github.com/lyw-ops/Spirite-harness) as its animation
production and validation tool. The canonical, provider-neutral harness
protocol is [`Spirite-harness/HARNESS.md`](https://github.com/lyw-ops/Spirite-harness/blob/main/HARNESS.md);
this document does not duplicate it and defers to it for every harness
contract (Animation Plan schema, build artifacts, validation codes, exit
codes, artwork-safety rules).

## Ownership boundary

**Sprite Harness owns** (external stable tool, used via its public CLI/JSON
contract only):

- the Animation Plan specification and its deterministic expansion;
- rendering (whole-sprite transforms in v1, explicit PNG layers in v2);
- validation: source identity, frame integrity, displacement/drift/ground
  checks, QA reports;
- preview GIFs, contact sheets, reports;
- optional explicit generation (M4) and grid atlas export (M5).

**gensokyo-codex-pets owns**:

- the immutable source sprites (`assets/reimu/eating/<state>/base.png`);
- pinned, maintainer-approved exact frame packages under
  `pets/reimu/animations/eating/sources/` when base-locked pixels are required;
- the consumer animation specification
  ([`pets/reimu/animations/eating/animation-set.json`](../pets/reimu/animations/eating/animation-set.json)),
  which is *not* a harness Animation Plan — the builder expands it into one
  legal plan per state;
- the build entry point [`tools/build_reimu_animations.py`](../tools/build_reimu_animations.py);
- the published runtime manifest format (`animation.json`, below) and the
  published frame sets;
- the preview/runtime model `Character → StateSet → State → frames[]`
  (`app/`) and the single task-count → state policy boundary
  ([`app/task-state-mapping.js`](../app/task-state-mapping.js)).

Nothing Reimu-specific lives in the harness; nothing harness-internal is
vendored or re-implemented here. Claude Code, Codex, humans, and CI all drive
the same `sprite-harness` CLI with the same JSON outputs and exit codes.

## Pipeline: source → build → validation → publish → runtime

```text
assets/reimu/eating/<state>/base.png        (immutable source, never rewritten)
or pets/reimu/animations/eating/sources/    (pinned exact-frame source)
        │
pets/reimu/animations/eating/animation-set.json   (consumer spec, 6 states)
        │  tools/build_reimu_animations.py
        ▼
build/animations/reimu/eating/<state>/      (disposable, gitignored)
  plan-spec.json                            generated Animation Plan spec
  build/                                    sprite-harness build directory
        │  sprite-harness plan → render → validate --write-qa
        │                → preview → contact-sheet → report   (all --json)
        ▼
assets/reimu/eating/<state>/                (published runtime artifacts)
  base.png                                  unchanged
  animation.json                            consumer runtime manifest
  frames/frame_000.png …                    validated frames
        │
        ▼
app/  (manifest loader + frames[] player; falls back to base.png loudly)
```

Build rules enforced by the entry point:

- the harness executable comes from `--harness`, `SPRITE_HARNESS_BIN`, or
  PATH; if absent the build fails with install instructions — there is no
  fallback renderer;
- every subprocess exit code is checked and every step runs in `--json` mode;
- **filesystem boundary (fail closed)**: the disposable build area
  (`--build-dir`) is validated against the source root, the publish root,
  the layered asset root, and every individual source sprite before any
  destructive operation — equality, containment in either direction, relative
  aliases, and symlink aliases are all rejected on fully resolved paths;
  any configured `layer_set` protects its resolved `asset_root` even when
  all requested states remain flattened; an exact-frame package is likewise
  protected against equality, containment and aliases;
- a validation failure (or any unexpected validation warning) aborts the whole
  run before anything is published;
- **set-level publication transaction**: all requested states are staged
  completely, the staged package is re-verified, and only then are states
  committed as one logical generation. Any commit failure rolls back every
  state changed by the run, so the published tree is never a mix of old and
  new generations. If a rollback itself fails, the builder writes an explicit
  recovery marker (`.publish-recovery.json`) next to the affected state,
  preserves the staging directory (which still holds the previous
  generation), and reports the failure — it never claims success.
  `scripts/check-repository.sh` fails while a recovery marker exists;
- `base.png` is never part of the transaction: it is immutable source (and
  the runtime fallback) and is verified unchanged after building and after
  publishing;
- repeated builds from identical inputs produce byte-identical published
  output (the harness renderer is deterministic and the manifest contains no
  timestamps);
- the harness version and the plan digest are recorded in each manifest.

Run it as:

```bash
python3 tools/build_reimu_animations.py            # build + validate + publish
python3 tools/build_reimu_animations.py --no-publish
python3 -m unittest tools.test_build_reimu_animations -v
node --experimental-default-type=module tools/test_app_runtime.mjs
```

## The runtime manifest (`animation.json`)

Each state directory carries a consumer-owned manifest, published only after
harness validation passes. It is deliberately distinct from the harness's
internal `frame-plan.json` and is the only animation file the runtime reads
(the runtime never reads `build/`):

```json
{
  "manifest_version": 1,
  "character": "reimu",
  "state_set": "eating",
  "state": "task_3",
  "animation_id": "reimu_eating_task_3",
  "playback": { "fps": 8, "loop": true },
  "frames": [ { "file": "frames/frame_000.png", "duration_ms": 125, "sha256": "…" } ],
  "reduced_motion": { "mode": "hold_first_frame", "frame": "frames/frame_000.png" },
  "source": { "file": "base.png", "sha256": "…" },
  "provenance": {
    "pipeline": "sprite-harness",
    "harness_version": "0.7.0",
    "plan_digest": "sha256:…",
    "render_mode": "full",
    "spec": "pets/reimu/animations/eating/animation-set.json",
    "builder": "tools/build_reimu_animations.py"
  }
}
```

The preview app (`app/animations.js`) validates the manifest strictly,
preloads every frame, and upgrades the state's ordered `frames[]` in place.
Beyond the structural checks (version, frame paths, durations, loop flag,
reduced-motion frame, image preload), every manifest is **semantically bound**
to the state it is loaded for: `character`, `state_set`, and `state` must
match the state set's declared binding (`app/characters.js`), so a manifest
published for `task_3` can never be attached to `task_2`. A missing,
malformed, mis-bound, or broken manifest drops that state to its static
`base.png` with an explicit UI status and console warning — never silently.
Full cryptographic verification stays out of the browser by design:
SHA-256 integrity is enforced by the build pipeline and
`scripts/check-repository.sh`, which re-verifies every published manifest:
contiguous frame numbering, per-frame digests, the reduced-motion frame, the
semantic binding, the absence of publish-recovery markers, and the current
source binding. Flattened manifests still require `file: base.png` and its
matching SHA-256. Layered manifests must name the official layer-set path and
bind exactly the currently applicable authored layer IDs in z-order, including
present optional layers and excluding absent ones. The checker reopens PNGs,
checks RGBA/transparency/canvas policy and digests, and rejects missing,
duplicate, unknown or undeclared layers. Mixed flattened/layered states are
the supported migration strategy. PNG inspection requires Pillow in the
Python used by `scripts/check-repository.sh`; the Harness venv supplies it.

## V1 limitation: flattened sprites, identity baseline

The Eating Set v1 sources are **flattened** single-image sprites: character,
low table, food, and tatami are baked into one RGBA image. Sprite Harness is
explicit that a flattened sprite is not a layered sprite — target-local tracks
(head, hand, eyes…) are *skipped with a warning*, never approximated.

The only motion available to a flattened sprite is whole-sprite transform, and
for this art that is a dead end, measured, not assumed: a restrained ±2 px
`translate_y` breathing experiment rendered and validated cleanly, but the
per-frame alpha bounding boxes show the tatami ground line oscillating by the
full motion amplitude (4 px peak-to-peak in source space) together with the
table and food — whole-scene bobbing that reads as camera shake, worse than a
stable still at the 160 px pet display size. Rotation and scale move the
ground line the same way.

Therefore the shipped baseline is an **identity hold**: one validated frame
per state (`frame_count: 1`, byte-identical to `base.png` through the
harness's exact-copy path), with `reduced_motion.mode: hold_first_frame`. This
proves the entire consumer pipeline end to end without faking motion the
sources cannot support.

Local eating motion requires either explicit authored layers that pass the
static reconstruction gate, or a separately approved exact-frame sequence.
The latter is intentionally supported for base-locked pixel work such as the
current `task_2` jaw/cheek loop; it is not a shortcut for unreviewed art.

## Consumer input modes

The builder supports three source modes behind the same runtime contract:

- **`flattened`** (default) — Animation Plan v1 bound to the immutable
  `base.png`, exactly as v1 shipped;
- **`layered`** — a state entry sets the consumer key
  `"source_mode": "layered"` (plus its local tracks); the builder composes a
  legal Animation Plan v2 inline `source` (reference canvas + ordered layers)
  from the machine-readable layer contract
  ([`pets/reimu/layers/eating/layer-set.json`](../pets/reimu/layers/eating/layer-set.json))
  and drives `sprite-harness plan` **without** `--source` (mixing modes is a
  harness error). Missing required layer PNGs fail closed with
  `ART ASSET REQUIRED`; layer files are SHA-verified unchanged after every
  build; the configured layered asset root is always protected.
- **`exact_frames`** — a state names a repository-contained `frame_source`
  manifest whose semantic binding, base digest, contiguous file set,
  per-frame SHA-256, durations and loop endpoints are checked before Harness
  runs. Harness plans against the exact neutral `base.png`; the builder copies
  the pinned sequence into the build as external frames, then runs
  `validate --write-qa → preview → contact-sheet → report`. No `render.json`
  exists in this mode because the consumer did not ask Harness to repaint or
  transform approved pixels. Publication still uses the ordinary manifest and
  transaction path, and frame 0 must equal the fallback base byte-for-byte.

The published `animation.json` format and the app player do not change: a
layered state's manifest carries a layered `source` binding (layer set +
per-layer digests) instead of the `base.png` digest, and `base.png` remains
the fallback when animation loading fails. Reduced motion holds the validated
manifest's frame 0 when available. The preview app cannot tell (and does not
need to know) whether frames came from flattened rendering, layers, or an
approved exact sequence — that is the architecture boundary.

The authoring contract, per-layer ownership, coordinate system, z-order,
allowed/forbidden transforms, and the pilot (`task_2`) QA checklist live in
[`reimu-layered-assets-v1.md`](reimu-layered-assets-v1.md). The layered v2
path is integration-tested end to end against the real CLI with synthetic
authored layers. Eleven current task_2 layer PNGs now pass the file-level
intake contract, but their static reconstruction is not pixel-equal to the
approved mother-locked neutral and therefore is not the color source for the
confirmed loop.

Use the [Task 2 Layer Asset Intake Pack](task-2-layer-asset-intake.md) and
`python3 tools/check_reimu_layer_assets.py` before production. The first
pilot uses full 596×596 RGBA layer canvases. Intake READY does not certify
the provisional positions or visual quality: calibrate from real PNGs,
pass static reconstruction using a temporary config and `--no-publish`, then
review restrained local motion before publishing a layered state. For the
current fixed-pose `task_2`, the approved exact source instead lives at
`pets/reimu/animations/eating/sources/task_2-chew-v9/`: 16 frames, 10 fps,
two asymmetric compress/puff beats, spatially tapered near-cheek motion, a
smaller far-cheek response, and byte-identical neutral endpoints. Three
independent no-publish consumer builds have identical non-location artifacts
and Harness reported zero errors/warnings. Production `task_2` now publishes
those exact 16 frames; its
approved neutral SHA `0251947e…` is both runtime `base.png` and frames 0/15,
while the preceding fallback SHA `d3139f4e…` is retained byte-exactly as
`base-eating-set-v1-legacy.png`. The previous chew-v7 exact package remains
pinned as a legacy source and still supplies the separately approved Codex
`running` row; v8 remains Harness-only comparison material.

Do not fake layers: no automatic body segmentation, bbox-guessed parts,
color-based layer splits, AI inpainting, or ignored
`TARGET_TRACKS_SKIPPED` warnings. The flattened sprites stay visual
reference and runtime fallback only.

## Codex v2 atlas boundary and approved row pilots

The Codex v2 atlas (1536×2288, 8×11, 192×208, `spriteVersionNumber: 2`, see
[codex-pet-format.md](codex-pet-format.md)) is a **different state space**
from `ReimuFoodTier`:

- Codex rows are `idle`, `running-right/left`, `waving`, `jumping`, `failed`,
  `waiting`, `running`, `review`, and 16 look directions — app-selected
  states, with no task-count hook in the current manifest;
- `ReimuFoodTier = 0..5` is this project's workload visual abstraction, and
  `task_1..task_5` must not be mapped onto Codex standard rows.

The future export path is:

```text
Reimu internal animation clips (per-state harness builds)
        ↓  project mapping: which clip performs each Codex standard state
Codex standard-state mapping
        ↓  sprite-harness export --spec … (M5 grid atlas, offline-validated)
Codex v2 atlas (1536×2288)
```

Four atlas inputs have now passed this boundary. The confirmed
`idle-v1-mother-locked-hair-settle` loop supplies standard row 0 (`idle`) and
the confirmed `waiting-v1-mother-locked-attentive-brow` loop supplies row 6
(`waiting`, user input needed); the maintainer-approved
`chew-v7-mother-locked` loop supplies row 7 (`running`, chat actively
working), and `review-v1-mother-locked-focused-brow` supplies row 8
(`review`, completed output is unread). Each is stored as six 192×208 source cells
under `pets/reimu/sprites/codex-v2/rows/`. Guarded importers pin the approved
Harness animation, plan, source and frame digests; the corresponding row
builders drive the public Harness CLI through plan, external-frame validation,
preview/contact sheet, M5 export and `validate-export`. Each resulting
1536×208 eight-cell row strip has six exact used cells and two verified
transparent cells. None of these rows represents an exact task count.

This is deliberately not a complete atlas. Producing an installable pet still
requires approved visual assets and animation design for both flight
directions, waving, jumping, failed, and the 16-direction
look family. No transparent placeholder rows, provisional `pet.json`, or
premature `spritesheet.webp` are generated.

## No implicit generation

The build pipeline is deterministic and offline. Sprite Harness's optional M4
generation stage (`sprite-harness generate`, external provider adapters) is
**never** invoked by `tools/build_reimu_animations.py`. Any future use of M4
requires explicit maintainer authorization, explicit credentials, and an
explicit command — no hidden or automatic provider calls.
