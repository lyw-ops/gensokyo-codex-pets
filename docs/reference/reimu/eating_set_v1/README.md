# Reimu Eating Set v1 — approved concept reference

Maintainer-approved concept art for the six-state eating set. These files are **reference/source material**, not runtime assets; runtime code must load only from `assets/reimu/eating/`.

## Files

- `eating-set-v1-sheet.png` — the approved 1254×1254 six-panel sheet (3×2, transparent background, low table + tatami, no labels). Source of truth for the v1 runtime sprites. Panel order, reading left-to-right then top-to-bottom: idle, task_1, task_2, task_3, task_4, task_5.
- `eating-set-v1-task1-single-render.png` — companion high-resolution single render of the task_1 state from the same design pass, kept as a style reference.

## Provenance

Maintainer-generated original concept art (2026-09-02), supplied from the local design archive (`~/Desktop/灵梦`). Earlier iterations in that archive (a dining-table/chair sheet with wall background, an idle-pose tatami-vs-cushion comparison, and downloaded third-party fan-art references) were **not** committed: the iterations were superseded by this sheet, and third-party fan art must never enter the repository (see `AGENTS.md`).

## Derivation

`tools/split_eating_sheet.py` segments the sheet by alpha connectivity (panels 5 and 6 touch and are separated by an erosion-seeded nearest-seed split), assigns floating effects (hearts, sweat drops, steam, sparkles) to their nearest panel, and normalizes each panel onto a 596×596 bottom-center-anchored transparent canvas. No pixels are invented, repainted, or non-uniformly scaled.

## Behavior-design use

The maintainer reconfirmed on 2026-09-19 that the six panels define the workload-eating
progression. Panel 0 is the no-task idle reference; panels 1–4 correspond to exactly that
many active tasks; panel 5 is the capped appearance for five or more. Active work selects
the shared `work_eating` behavior family with the corresponding food composition and
emotion. A tier change swaps composition at a safe loop boundary instead of restarting
the behavior.

The sheet does not forbid a separate tier-0 `idle_onigiri` one-shot. That action is a
bounded idle snack with a neutral/pleased expression and must not reuse panel 1's
work-linked tearful meaning. The concept sheet's detached hearts, sparkles, sweat drops,
and steam are optional visual cues; production sprites should prefer readable face,
pose, timing, and meal richness at normal pet size.
