# Sprite Harness integration

Status: **Eating Set v1 identity baseline shipped and hardened (path
isolation, set-level publish transaction, state-bound runtime manifests);
Reimu Layered Assets v1 production tooling and task_2 intake validation ready;
ART ASSET REQUIRED**

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
  all requested states remain flattened;
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

**Local eating motion requires explicit layered source assets.** That is the
next art milestone, not a build-tooling gap.

## Layered sprites (Animation Plan v2) — builder ready, assets pending

The builder now supports two source modes behind the same pipeline and the
same runtime contract:

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

The published `animation.json` format and the app player do not change: a
layered state's manifest carries a layered `source` binding (layer set +
per-layer digests) instead of the `base.png` digest, and `base.png` remains
the fallback when animation loading fails. Reduced motion holds the validated
manifest's frame 0 when available. The preview app cannot tell (and does not
need to know) whether frames came from v1 or v2 — that is the architecture
boundary.

The authoring contract, per-layer ownership, coordinate system, z-order,
allowed/forbidden transforms, and the pilot (`task_2`) QA checklist live in
[`reimu-layered-assets-v1.md`](reimu-layered-assets-v1.md). The layered v2
path is integration-tested end to end against the real CLI with synthetic
authored layers; **no real Reimu layer PNGs exist yet** — producing them is
an explicit art task, not a tooling gap.

Use the [Task 2 Layer Asset Intake Pack](task-2-layer-asset-intake.md) and
`python3 tools/check_reimu_layer_assets.py` before production. The first
pilot uses full 596×596 RGBA layer canvases. Intake READY does not certify
the provisional positions or visual quality: calibrate from real PNGs,
pass static reconstruction using a temporary config and `--no-publish`, then
review restrained local motion before publishing task_2. The current
production animation-set still keeps every state flattened.

Do not fake layers: no automatic body segmentation, bbox-guessed parts,
color-based layer splits, AI inpainting, or ignored
`TARGET_TRACKS_SKIPPED` warnings. The flattened sprites stay visual
reference and runtime fallback only.

## Future: Codex v2 atlas boundary

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

Producing a real atlas still requires new visual assets and animation design
for every standard row (idle, both flight directions, waving, jumping, failed,
waiting, running, review, and the 16-direction look family) at 192×208 cell
scale. The current Eating Set cannot populate those rows, and no placeholder
"final atlas" will be generated from it.

## No implicit generation

The build pipeline is deterministic and offline. Sprite Harness's optional M4
generation stage (`sprite-harness generate`, external provider adapters) is
**never** invoked by `tools/build_reimu_animations.py`. Any future use of M4
requires explicit maintainer authorization, explicit credentials, and an
explicit command — no hidden or automatic provider calls.
