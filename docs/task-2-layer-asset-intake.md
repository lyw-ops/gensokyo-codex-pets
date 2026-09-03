# Task 2 Layer Asset Intake Pack

Status: **ART ASSET REQUIRED** — production tooling and intake validation
are ready; the real static reconstruction and animation have not started.
Pilot stays **task_2**. The six published flattened identity holds remain current.

## What is available

Read-only inventory on 2026-09-03 covered this consumer repository (including
its layered source tree), the Harness workspace, and the maintainer archive
previously identified in HANDOFF (`~/Desktop/灵梦`). No explicitly authored
Reimu part PNGs or layered authoring masters were found in those locations.

- `assets/reimu/eating/task_2/base.png`: approved **flattened reference and
  fallback**, 596×596 RGBA, not an authored layer master.
- `docs/reference/reimu/eating_set_v1/eating-set-v1-sheet.png`: approved
  flattened sheet, 1254×1254; SHA-256
  `a2cc731c83f2e114f036b77ca1041c7bb5647ec30cf45f859826b153d4a028e3`.
- The archive's `ChatGPT Image 2026年9月2日 20_27_17.png` is that same sheet;
  `615859ed-035c-405b-bf53-cee162692d81.png` is the committed task_1 single
  render. The other two PNGs are superseded flattened concept sheets,
  visually inspected as complete scenes. JPEG fan-art references are not
  layer sources and remain excluded.
- Harness example frames are programmatic test placeholders, not Reimu art.

No segmentation, masking, bbox crops, background removal, inpainting, or
other cutouts may turn these references into layers. No provider calls,
M4 generation, or new AI artwork are authorized by this task.

## Files to author

Place the following under **`assets/reimu/layered/eating/`**. All eight are
required; filenames must match the existing layer IDs exactly.

| Path | Pixels owned by this layer |
| --- | --- |
| `shared/tatami.png` | Tatami and floor/contact shading; no character or table |
| `shared/body.png` | Seated torso, legs, skirt, sleeves and shoulders; no face, hands or props |
| `shared/head.png` | Hair, large red bow, skin/face base, blush and eyebrows; no eyes or mouth |
| `shared/table.png` | Entire low table and its own shading; no dishes or food |
| `task_2/eyes_open.png` | Open eye pair, same gaze/expression family as approved task_2 |
| `task_2/mouth.png` | Natural neutral eating mouth; underlying face belongs to head |
| `task_2/hand_right.png` | Eating hand/grip, with enough authored overlap to stay joined to its sleeve |
| `task_2/table_food.png` | Stationary plate with two onigiri and tea cup from the approved task_2 composition |

Recommended: `task_2/eyes_closed.png` for blink and `task_2/held_food.png`
for the onigiri held at the mouth. Supply `task_2/hand_left.png` and
`task_2/effects.png` only when the pose needs those separate layers.

The approved pose shows **two hands holding one onigiri**. Optional files
do not mean optional visible content. If `held_food` is absent, include the
held onigiri in the co-moving `hand_right` grip. If `hand_left` is absent,
that grip may own both hands as one group. Record this ownership in the
delivery notes; otherwise supply the separate PNGs. Never duplicate the same
visible hand/food pixels across layers or add empty files to fill 12 slots.
When separate food or a second gripping hand is present, coordinate its
motion with the eating hand so the grip cannot separate.

Keep the same identity, proportions, palette, expression and composition as
Eating Set v1. The new layered master need not reproduce every flattened
pixel. Preserve head/bow size, hair silhouette, outfit, hand grip, tabletop
arrangement, table footprint and tatami ground line. Do not amplify the
task_2 expression into the crying task_1 or happy task_3 design.

## Export coordinates

Every file uses a **full 596×596 transparent RGBA PNG canvas** with its part
already placed in final composition coordinates. Export each layer from the
same canvas, at the same scale and origin. No trimming, recentering, per-part
resizing, palette/LA exports, opaque matte, or mixed cropped/full-canvas modes.
Each required layer must contain visible pixels and some transparent pixels.
Author occluded overlap where motion will reveal it; do not rely on cutouts
of the flattened picture. This is an artist's construction task.

The machine-readable `canvas_policy: full_canvas` governs intake dimensions.
Existing `anchor`, `position`, and `position_status: provisional` values are
retained as unverified historical authoring metadata; **do not move exported
art to match those provisional numbers**. They have not been approved for
the full-canvas PNGs.

After real files arrive, inspect their alpha bounds and composition. Verify
head/eye/mouth alignment, hand contacts, and the table/tatami ground lines.
Then update placement metadata together with that evidence. For full-canvas
identity placement, a top-left custom anchor `(0, 0)` at position `(0, 0)`
maps every pixel unchanged under Harness v2. If a measured rotation pivot
is needed later, position must equal that anchor's pixel coordinates in the
reference canvas to preserve the static placement. Do not certify or change
positions before inspecting real artwork.

Record artist, authoring tool, original resolution, permission/provenance,
optional-layer ownership and export date in the delivery/HANDOFF. Do not
commit third-party sprites or source-editor files into the PNG source tree.

## One-command intake check

From the consumer root, using Python with Pillow installed (the Sprite
Harness virtual environment already supplies it):

```bash
python3 tools/check_reimu_layer_assets.py
```

This defaults to task_2; `--state task_2` is equivalent. Exit **0** prints
`READY`; exit **1** prints `ART ASSET REQUIRED` and the exact missing or
invalid paths. Optional absences are listed separately and do not block.
It checks readable PNG, RGBA, transparency, nonempty required layers, exact
canvas dimensions, layer ID/filename, source-root containment, and unexpected
authored PNGs. Other states' declared files are allowed but not required by
task_2 intake. It reads files without modifying them or invoking Harness.

`READY` means the **file contract** passes. It says nothing about artistic
quality, positional calibration, occlusion, visual approval or publication.
Do not change task_2's production `source_mode` just because intake is READY.

## Static reconstruction before animation

1. Inspect actual PNGs and calibrate the provisional placements as above.
2. Copy `pets/reimu/animations/eating/animation-set.json` to a disposable
   `build/task2-static-config.json`. In that copy only, make task_2 layered,
   use 8 fps / 1 frame / loop, and remove motion tracks. Keep the official
   layer-set binding and use a separate build directory.
3. If `eyes_closed` exists, hide it in this one-frame build with a local
   opacity track: amplitude `1`, unit `ratio`, curve `sine`, cycles `1`,
   phase `0.75`. At frame 0 its effective opacity is zero. Open eyes stay
   visible. Omit this track when the optional closed-eye layer is absent.
4. Run the existing consumer pipeline without publication:

   ```bash
   python3 tools/build_reimu_animations.py --states task_2 \
     --config build/task2-static-config.json \
     --build-dir build/task2-static --no-publish
   ```

5. Compare its static frame/contact sheet with the approved task_2 reference
   at 596 px, in a 192×208 cell (uniform fit, bottom-center), and at 160 px.
   Check silhouette, face, bow, hair, outfit, both hands, food, table, tatami
   and ground line. Reject seams, gaps, double edges, floating parts, wrong
   occlusion, missing pixels or accidental overlap. Correct authored source
   construction before motion. Record reviewer and result in HANDOFF.

No static reconstruction preview is delivered with this intake pack because
there are no authored PNGs to reconstruct.

## Animation and publication after static approval

Only after the static gate passes, prepare task_2's layered Animation Plan
v2 via the existing builder. Start at **8 fps, 12 frames, loop** with a
natural frame 0. Start local displacement experiments around 1–3 px on the
596 px canvas. Prioritize slight body breathing and eating-hand motion.
Keep `tatami`, `table` and `table_food` static. Coordinate held food with the
grip. Add blink only if both eye variants work at 160 px; reject obvious
cross-fade ghosting as `visual QA failed: discrete eye variant needed`.
Add chew only if the mouth stays attached; head bob is last and tiny.

Run `plan → render → validate --write-qa → preview → contact-sheet → report`
through the consumer builder using `--no-publish` while reviewing. Inspect
all three sizes, loop return, grip/food attachment and the natural
reduced-motion frame 0. Only after recorded visual approval may the existing
builder publish task_2. Rebuild it twice to verify deterministic output and
run repository checks with five flattened states plus the one layered state.

Stop at pilot validation for maintainer review. Do not expand the other five
states or start the Codex atlas in this task.
