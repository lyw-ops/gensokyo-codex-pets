# Tools

Deterministic project tooling. Do not place generated art or copied app
internals here.

- [`split_eating_sheet.py`](split_eating_sheet.py) — derives the six Eating
  Set v1 runtime sprites from the approved reference sheet (alpha-connectivity
  segmentation, bottom-center anchoring). Regenerate from an updated approved
  sheet instead of hand-editing `base.png` files.
- [`build_reimu_animations.py`](build_reimu_animations.py) — the Sprite
  Harness consumer build entry point: expands
  `pets/reimu/animations/eating/animation-set.json` into one Animation Plan
  per state, drives the public `sprite-harness` CLI
  (`plan → render → validate --write-qa → preview → contact-sheet → report`),
  and publishes validated frames plus a runtime `animation.json` manifest next
  to each state's immutable `base.png`. See
  [`docs/sprite-harness-integration.md`](../docs/sprite-harness-integration.md).
- [`test_build_reimu_animations.py`](test_build_reimu_animations.py) — unit
  and integration tests for the build pipeline:
  `python3 -m unittest tools.test_build_reimu_animations -v`.
