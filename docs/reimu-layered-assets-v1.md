# Reimu Layered Assets v1 — asset production specification

Status: **production tooling ready; task_2 intake validation ready; ART ASSET REQUIRED**

The actionable delivery checklist and current asset inventory are in the
[Task 2 Layer Asset Intake Pack](task-2-layer-asset-intake.md).

This document specifies the explicitly authored PNG layers that upgrade the
Reimu Eating Set from the flattened v1 identity baseline to real local motion
(Sprite Harness Animation Plan v2). The machine-readable counterpart is
[`pets/reimu/layers/eating/layer-set.json`](../pets/reimu/layers/eating/layer-set.json);
the builder ([`tools/build_reimu_animations.py`](../tools/build_reimu_animations.py))
turns that contract into the inline `source` object of a v2 plan. The harness
layered contract itself is
[`Spirite-harness/docs/layered-sprites.md`](https://github.com/lyw-ops/Spirite-harness/blob/main/docs/layered-sprites.md)
and is not duplicated here.

## Hard boundaries

- **Layers are authored, never derived.** Do not produce layers from the
  flattened `base.png` via segmentation models, color thresholds, bbox
  guessing, connected components, background removal, or AI inpainting. The
  flattened Eating Set stays as visual reference and runtime fallback only.
- **No implicit generation.** Producing these PNGs is an art task. The build
  pipeline never invokes Sprite Harness M4 generation to "fill in" missing
  layers; a missing required layer fails the build with `ART ASSET REQUIRED`.
- **Sources are immutable.** Committed layer PNGs are never rewritten by the
  renderer or the builder; the builder verifies their SHA-256 is unchanged
  after every build.
- **Source / build / publish / reference separation.** Layered sources live in
  `assets/reimu/layered/eating/` (version-controlled, reviewable). Builds go to
  the disposable `build/` tree. Published runtime frames stay in
  `assets/reimu/eating/<state>/`. Reference art stays in
  `docs/reference/reimu/eating_set_v1/`. Never put layered sources in `build/`.

## Coordinate system

- **Reference canvas: 596 × 596** — identical to the flattened Eating Set
  sprites, so the layered composite is directly comparable to `base.png`.
- Pixel (i, j) has center (i + 0.5, j + 0.5); x points right, y points down;
  positive rotation is clockwise (harness M2/M3 convention).
- Every layer declares an **anchor** (`center`, `bottom_center`, or normalized
  `custom`) and a **position** in reference-canvas pixels: the anchor point of
  the layer image maps to the declared position (plus local translation).
  The existing bottom-center/center anchors and their positions are historical
  provisional values, not approved placements for the incoming artwork.
- Pilot export uses **full 596×596 transparent RGBA canvases**: every part
  stays in final composition coordinates. `canvas_policy: full_canvas` is
  checked by intake and layered runtime validation. No trimming, recentering,
  or mixing cropped and full-canvas exports.
- All positions remain **provisional** until real PNGs arrive. Inspect alpha
  bounds and alignment, then update placement metadata with the real art.
  A top-left custom anchor at position `(0, 0)` preserves a full canvas
  unchanged; any other anchor must map to its corresponding pixel position
  for identity placement. Do not apply the old provisional translations to
  full-canvas exports. See the intake pack's calibration and static gate.

## Layer schema and z-order

Array/z order is back-to-front. Reimu sits **behind** the low table, so the
table and tabletop food occlude her lower body; the held food and the near
eating hand render in front of the table.

| z   | id           | scope  | motion policy      | required |
| --- | ------------ | ------ | ------------------ | -------- |
| 0   | `tatami`     | shared | static (never)     | yes      |
| 10  | `body`       | shared | breathing          | yes      |
| 20  | `head`       | shared | bob / tilt         | yes      |
| 30  | `eyes_open`  | state  | blink visibility   | yes      |
| 31  | `eyes_closed`| state  | blink visibility   | no       |
| 40  | `mouth`      | state  | chew               | yes      |
| 50  | `hand_left`  | state  | static             | no       |
| 60  | `table`      | shared | static             | yes      |
| 70  | `table_food` | state  | static             | yes      |
| 80  | `held_food`  | state  | follows hand       | no       |
| 90  | `hand_right` | state  | eating hand        | yes      |
| 100 | `effects`    | state  | static overlay     | no       |

This order is the contract default. If authoring the pilot proves a different
occlusion is correct (e.g. the resting hand on the tabletop must render above
the table), adjust `layer-set.json` and record the rationale in `HANDOFF.md`
in the same commit. Only create a new layer when it needs independent
transform, visibility, or per-tier replacement — do not fragment further.

### Per-layer ownership

**`tatami`** — Includes: tatami mat, floor shading. Excludes: everything that
sits on it. Reason: the ground plane must be provably immobile; this is the
main motivation for leaving the flattened baseline. *The tatami must never
breathe.*

**`body`** — Includes: seated torso, legs, skirt, detached sleeves, shoulder
line. Excludes: head, both hands, any prop. Reason: breathing is a very
slight body-local motion; hands and head move on their own tracks.

**`head`** — Includes: hair, the large red bow, face base (skin, blush,
eyebrows). Excludes: eyes, mouth, hands, food. Reason: the head needs an
independent, very subtle bob/tilt while eyes and mouth need discrete
expression changes per tier.

**`eyes_open` / `eyes_closed`** — Tier-specific eye pair implementing the
locked emotion progression (tier 1 crying → tier 2 residual tears → tier 3
content → tier 4 happy → tier 5 laughing happy-tears; idle unhurried).
Blink uses the visibility mechanism below. Eyes move together with the head:
give them the same motion tracks as `head`, never independent drift.

**`mouth`** — Tier-specific mouth. Chew is either a barely visible local
motion or a variant swap; the mouth must never slide across the face.

**`hand_left`** — Far or resting hand, only where the approved pose shows it
apart from the body silhouette (e.g. resting on the table edge).

**`table`** — Low table, front face and top. Its ground line never moves.

**`table_food`** — The tier's tabletop meal composition (dishes, tea, the
banquet at tier 5). Static by default: no food drift unless a motion is
explicitly designed for a semantic reason.

**`held_food`** — The food in the eating hand (the recurring onigiri anchor
where tier semantics keep it). It shares the eating hand's tracks exactly so
food and hand never separate.

**`hand_right`** — The near eating hand. Small local arc between table height
and mouth height; the loop must return it naturally (sine-family curves with
integer cycles), never teleport it. For the minimum eight-file pilot, this
layer may own the co-moving two-hand grip and held onigiri when those optional
layers are absent; document that ownership and never duplicate the pixels.
Separate gripping hands/held food must stay coordinated during motion.

**`effects`** — Foreground overlays owned per tier: steam, sparkles, happy
tears, the single allowed sweat cue at tier 4. Static in the pilot.

### Blink and chew with today's harness contract

Animation Plan v2 animates declared layers with translate / rotate / scale /
**opacity** tracks; there is no discrete per-frame variant swap. Blink is
therefore authored as the `eyes_open`/`eyes_closed` pair cross-faded with
complementary opacity tracks (short, few-frame dip). Chew may use a tiny
mouth translate or the same two-layer opacity mechanism. If pilot QA at
160 px shows the cross-fade reads poorly, the correct escalation is a
reproducible feature request to Sprite Harness (discrete variant tracks) —
not a consumer-side renderer and not a harness patch from this repository.

## File and naming convention

```text
assets/reimu/layered/eating/
  shared/          tatami.png  body.png  head.png  table.png
  idle/            eyes_open.png [eyes_closed.png] mouth.png hand_right.png
                   table_food.png [held_food.png] [hand_left.png] [effects.png]
  task_1/ … task_5/   same pattern as idle/
```

- Lowercase snake_case ids; the file name equals the layer id, `.png` only.
- Shared layers live in `shared/` and are used by all six states; the
  layer-set's `{state}` placeholder resolves state-specific paths.
- Full-canvas RGBA PNG with actual transparent pixels; required layers must
  have visible pixels. This consumer intake is stricter than Harness's
  general alpha-format support. No matte, white background or premultiplied
  export artifacts. Keep visible content off the image edge.
- Optional layers (`required: false` in the layer-set) may be absent for a
  state; required layers missing at build time fail with `ART ASSET REQUIRED`.

## Shared vs tier-specific

Shared construction (`tatami`, `body`, `head`, `table`) plus tier-specific
expression (`eyes_*`, `mouth`) and tier-specific food composition
(`table_food`, `held_food`, `effects`). Do **not** author six unrelated rigs.
If one state genuinely needs a unique pose (e.g. the tier 5 banquet), give
that state a state-scoped override layer and record why — but the default is
sharing. Sharing must not break the approved visual consistency of the six
Eating Set plates: when a shared layer cannot reproduce a state's approved
look, that state gets a specific layer instead of degrading the art.

## Allowed and forbidden transforms

Allowed (all local, all restrained; Reimu should feel alive, not busy):

- `body` translate_y breathing ≤ ~1.5 px amplitude, sine, integer cycles;
- `head` translate_y bob ≤ ~1 px and/or rotate ≤ ~0.5°, in phase with the body;
- `hand_right` (+ `held_food`, coordinated tracks) starts around 1–3 px;
- `eyes_open`/`eyes_closed` complementary opacity (blink);
- `mouth` translate ≤ ~1 px or opacity variant (chew).

Forbidden:

- any motion on `tatami` or `table` (no ground bounce, ever);
- `table_food` drift without an explicit designed reason;
- whole-composite (`sprite` target) bobbing as a breathing substitute;
- non-uniform scale anywhere (harness rejects it); mirroring/flipping layers;
- motion that moves a layer's ground contact line;
- eyes or mouth translating independently of the head (face sliding).

Every track target in a state's plan must name a layer declared for that
state — `TARGET_TRACKS_SKIPPED`-style silent degradation is a v1 concept and
must not reappear; the harness rejects unknown targets in v2 plans.

## Source provenance

Every committed layer PNG records in the commit message (and `HANDOFF.md`)
how it was authored: painted from scratch against the approved Eating Set v1
reference, by whom/which tool, at what resolution. The `AGENTS.md` rules stay
binding: no third-party sprites, no traced reference art, no commercial game
material. Reference art is never loaded at runtime.

## Pilot: `task_2`

`task_2` is the pilot state: medium complexity, held food + table food, and
the transitional expression (residual tears, visibly easing) — enough to
exercise body/head/face/hand/prop decomposition without the tier 5 banquet.
Changing pilot state requires a concrete unavoidable visual reason recorded
in `HANDOFF.md`; task_2 remains the selected pilot.

Pilot animation priority: very slight body breathing, then small eating-hand
motion. Blink and chew are conditional on visual quality; head bob is last.
Start at 8 fps, 12 frames, loop. First frame must be a natural rest pose
(it is the reduced-motion still).

### ART ASSET REQUIRED — pilot request

To start the pilot, the maintainer (or an explicitly authorized art pass)
must produce these full 596×596 RGBA PNGs:

```text
shared/tatami.png      shared/body.png     shared/head.png    shared/table.png
task_2/eyes_open.png   task_2/mouth.png
task_2/hand_right.png  task_2/table_food.png
recommended optional: task_2/eyes_closed.png  task_2/held_food.png
only when needed: task_2/hand_left.png  task_2/effects.png
```

Run `python3 tools/check_reimu_layer_assets.py` for exact missing/invalid
paths. After intake is READY, inspect real art and calibrate positions, then
use a temporary config with `--no-publish` for the static reconstruction.
Only after that passes should task_2's production config become layered with
motion tracks. Review animation using `--no-publish`; publication follows
recorded visual approval. The intake pack gives the full sequence.

## QA checklist (pilot acceptance)

Run `plan → render → validate --write-qa → preview → contact-sheet → report`,
then review:

- **Identity** — face recognizably identical to the approved plate; hair/bow/
  outfit proportions stable; no detached limbs; no visible layer seams.
- **Motion** — no table bounce; no tatami bounce; no food drift; no hand
  teleporting; no face sliding.
- **Loop** — clean seam; no visible jump; blink does not stick; the eating
  hand returns naturally.
- **Display size** — judge at 160 px and in a 192×208 cell context, not only
  at 596 px zoom.
- **Reduced motion** — the first frame is a natural rest pose.
- **Composite parity** — the layered rest frame reads as the same plate as
  the approved flattened `task_2/base.png` (not pixel-identical, but the same
  approved composition).

Stop at task_2 pilot validation for maintainer review. Other-state expansion
and the Codex atlas require a subsequent task.
