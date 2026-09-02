# Reimu Eating Set v1 — approved concept reference

Maintainer-approved concept art for the six-state eating set. These files are **reference/source material**, not runtime assets; runtime code must load only from `assets/reimu/eating/`.

## Files

- `eating-set-v1-sheet.png` — the approved 1254×1254 six-panel sheet (3×2, transparent background, low table + tatami, no labels). Source of truth for the v1 runtime sprites. Panel order, reading left-to-right then top-to-bottom: idle, task_1, task_2, task_3, task_4, task_5.
- `eating-set-v1-task1-single-render.png` — companion high-resolution single render of the task_1 state from the same design pass, kept as a style reference.

## Provenance

Maintainer-generated original concept art (2026-09-02), supplied from the local design archive (`~/Desktop/灵梦`). Earlier iterations in that archive (a dining-table/chair sheet with wall background, an idle-pose tatami-vs-cushion comparison, and downloaded third-party fan-art references) were **not** committed: the iterations were superseded by this sheet, and third-party fan art must never enter the repository (see `AGENTS.md`).

## Derivation

`tools/split_eating_sheet.py` segments the sheet by alpha connectivity (panels 5 and 6 touch and are separated by an erosion-seeded nearest-seed split), assigns floating effects (hearts, sweat drops, steam, sparkles) to their nearest panel, and normalizes each panel onto a 596×596 bottom-center-anchored transparent canvas. No pixels are invented, repainted, or non-uniformly scaled.
