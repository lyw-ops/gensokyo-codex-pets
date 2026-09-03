# Reimu eating-set runtime sprites (v1)

Six runtime state directories, one per eating state, derived from the approved **Eating Set v1** concept sheet in `docs/reference/reimu/eating_set_v1/`.

Each state directory contains:

- `base.png` — the immutable static source sprite (never overwritten);
- `animation.json` — the consumer runtime manifest published by the Sprite Harness pipeline (`tools/build_reimu_animations.py`), recording frame order, durations, loop, the reduced-motion frame, the source digest, and build provenance;
- `frames/frame_000.png …` — harness-validated animation frames referenced by the manifest.

The current published animation is the deliberate **identity baseline**: one validated frame per state, byte-identical to `base.png`. The flattened sources cannot support local motion without moving the table/tatami ground line; see [`docs/sprite-harness-integration.md`](../../../docs/sprite-harness-integration.md). Runtime consumers read `animation.json` + `frames/`; `base.png` doubles as the explicit static fallback when a manifest is missing or broken.

| State | Task count | Composition |
| --- | --- | --- |
| `idle` | 0 (or invalid/negative input) | empty table, chin resting in both hands, bored |
| `task_1` | 1 | one onigiri, slightly teary while eating |
| `task_2` | 2 | onigiri in hands plus a plate and tea, calm |
| `task_3` | 3 | rice bowl and a small side dish, satisfied closed eyes |
| `task_4` | 4 | ramen, happy slurping, small hearts |
| `task_5` | 5+ | banquet: ramen centerpiece, onigiri, sides, drink, laughing with happy tears |

## Sprite specification

- `base.png`, 596×596, RGBA with true transparency.
- Uniform character/table/tatami scale (all states are cut from one sheet, no rescaling).
- Bottom-center anchored: each state's content is horizontally centered with a 10 px bottom margin, so the tatami sits at a stable ground line when states switch.
- No text, numbers, panel borders, or backgrounds.

## Provenance and regeneration

`base.png` is derived mechanically (alpha-mask segmentation, no repainting) from `docs/reference/reimu/eating_set_v1/eating-set-v1-sheet.png` by `tools/split_eating_sheet.py`. Never edit `base.png` by hand-painting; regenerate from an updated approved sheet instead.

`animation.json` and `frames/` are published only by `tools/build_reimu_animations.py` after `sprite-harness validate` passes; never hand-edit them. Rebuild with:

```bash
python3 tools/build_reimu_animations.py
```
