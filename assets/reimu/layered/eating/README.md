# Reimu Eating Set — layered sources (Animation Plan v2)

This tree holds the **explicitly authored** PNG layers that Sprite Harness
Animation Plan v2 composes into real local motion. It is version-controlled
source: reviewable, immutable at build time, and never written by the
renderer or the builder.

- Contract (machine-readable): `pets/reimu/layers/eating/layer-set.json`
- Specification, per-layer ownership, QA checklist:
  `docs/reimu-layered-assets-v1.md`
- Exact eight required pilot PNGs, recommended/optional layers, full 596×596
  export policy and static reconstruction sequence:
  `docs/task-2-layer-asset-intake.md`
- Read-only intake: `python3 tools/check_reimu_layer_assets.py` from the
  repository root (Python with Pillow). Prints `READY` or `ART ASSET REQUIRED`
  with exact paths. READY is file validation, not visual approval.

```text
shared/    layers used by all six states (tatami, body, head, table)
idle/      state-specific layers (eyes, mouth, hands, food, effects)
task_1/ … task_5/
```

Status: **no layer PNGs exist yet** (`ART ASSET REQUIRED`; the pilot state is
`task_2`). Do not derive layers from the flattened
`assets/reimu/eating/<state>/base.png` — segmentation, thresholding,
inpainting, and bbox guessing are all forbidden. The flattened sprites remain
visual reference and runtime fallback only.
