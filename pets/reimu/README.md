# Hakurei Reimu / 博丽灵梦

Phase 1 pet. Current status: **task_2 fixed-pose chew published as a validated
16-frame exact sequence; Codex v2 idle, waiting, running, and review rows
separately approved; full atlas incomplete**.

This directory contains the six-tier eating animation specification, the
pinned task_2 exact-frame source, the first four reviewed Codex v2 row sources,
and the design/package specifications. It contains no placeholder full atlas
and is not currently installable.

## Contents

- `design/visual-spec.md` — measurable production constraints and provisional palette.
- `sprites/README.md` — asset naming and acceptance rules.
- `metadata/pet.v2.example.json` — non-installable manifest example for the local v2 target.
- `metadata/README.md` — packaging notes.

Project-level behavior is described in [`docs/reimu-design.md`](../../docs/reimu-design.md) and [`docs/workload-food-system.md`](../../docs/workload-food-system.md).

Do not add a final `pet.json` or `spritesheet.webp` until the remaining row
visual approval gates are complete and the atlas passes the current v2
validator. See `sprites/codex-v2/README.md` for the approved idle, waiting, running, and review rows.
