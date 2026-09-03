# Sprite Harness integration

Status: **Eating Set v1 identity baseline shipped; the full source → build →
validation → publish → runtime pipeline is in production use**

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
- a validation failure (or any unexpected validation warning) aborts the whole
  run before anything is published: all requested states publish together or
  none do;
- publication is staged inside the state directory and the previous frame
  generation is restored on failure, so `assets/` never holds a half-published
  state;
- the source SHA-256 is verified unchanged after building and after
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
preloads every frame, and upgrades the state's ordered `frames[]` in place. A
missing, malformed, or broken manifest drops that state to its static
`base.png` with an explicit UI status and console warning — never silently.
`scripts/check-repository.sh` re-verifies every published manifest: contiguous
frame numbering, per-frame digests, the reduced-motion frame, and the recorded
`base.png` digest.

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

## Future: layered sprites (Animation Plan v2)

When explicit Reimu layers exist (for example `body.png`, `head.png`,
`eyes_open/closed.png`, `mouth_*.png`, `hand_right.png`, `food.png`,
`table.png`, `tatami.png`), the same pipeline upgrades in place:

- `animation-set.json` state entries gain a v2 `source` override
  (`reference_canvas` + ordered `layers`) and local tracks (breathing, head
  bob, eating hand, blink, chew) — the builder already passes any per-state
  override through to the generated plan;
- `sprite-harness plan/render/validate` handle v2 natively (layered contract:
  [`docs/layered-sprites.md`](https://github.com/lyw-ops/Spirite-harness/blob/main/docs/layered-sprites.md));
- the published `animation.json` format and the app player do not change at
  all — states simply gain more frames.

Do not fake layers before then: no automatic body segmentation, bbox-guessed
parts, color-based layer splits, or ignored `TARGET_TRACKS_SKIPPED` warnings.

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
