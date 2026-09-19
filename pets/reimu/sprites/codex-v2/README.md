# Reimu Codex v2 row sources

This directory contains reviewed source cells for the local Codex v2 atlas.
It is intentionally incomplete and is not an installable pet package.

## Approved rows

`rows/idle/` contains the confirmed `idle-v1-mother-locked-hair-settle`
loop for Codex standard row 0. Six 192x208 RGBA cells use the shipped idle
timing 280/110/110/140/140/320 ms. The fixed seated pose and open eyes remain
unchanged; only the image-left loose hair curl lower contour settles by 1–2px
and returns. The earlier blink, breathing and tea-sip ideas are deferred.

`rows/running/` contains the maintainer-approved `chew-v7-mother-locked`
fixed-pose eating loop adapted to Codex standard row 7 (`running`). Codex uses
that row while a chat is actively working. The six 192x208 RGBA source cells
use the fixed Codex timing 120/120/120/120/120/220 ms and perform one small
neutral-to-puff-to-neutral cheek/jaw chew. Food, hands, body, eyes, table, and
tatami remain fixed.

`rows/waiting/` contains the confirmed
`waiting-v1-mother-locked-attentive-brow` loop for Codex standard row 6. Its
six 192x208 RGBA cells use the shipped waiting timing
150/150/150/150/150/260 ms. The fixed seated eating pose remains unchanged;
only the image-right eyebrow and its immediate antialias/skin band rise by
1–3px and return. Eye interiors, eyelids, lashes, food, hands, body, tea,
table, and tatami remain fixed. The earlier chin-in-hand concept is deferred.

`rows/review/` contains the confirmed `review-v1-mother-locked-focused-brow`
loop for Codex standard row 8. Its six 192x208 RGBA cells use the shipped
review timing 150/150/150/150/150/280 ms. The fixed seated eating pose remains
unchanged; only the complete image-right eyebrow and immediate skin band lower
uniformly by 1–2px and return. Its original location is fully cleared with
source skin, so no split or residual eyebrow line remains. Eye interiors,
eyelids, lashes, props, body, and ground remain fixed. The task-slip/nod idea
is deferred.

The source manifest records the approved Harness identity, exact frame
digests, phase selection, cell conversion, permission status, and the runtime
limitation: the current Codex custom-pet manifest has no task-count hook, so
this row cannot claim to represent exactly two active tasks.

## Build

```bash
python3 tools/build_reimu_codex_idle_row.py --harness /path/to/sprite-harness
python3 tools/build_reimu_codex_waiting_row.py --harness /path/to/sprite-harness
python3 tools/build_reimu_codex_running_row.py --harness /path/to/sprite-harness
python3 tools/build_reimu_codex_review_row.py --harness /path/to/sprite-harness
```

Each builder uses only Sprite Harness's public CLI and writes a validated
1536x208 eight-cell row strip under `build/codex-v2/`. It also generates the
Harness preview, contact sheet, QA, and M5 export metadata. The final two cells
of each row are verified fully transparent.

The tool deliberately does not create a 1536x2288 atlas, `pet.json`, or
`spritesheet.webp`. Those outputs stay blocked until all standard rows and
the 16 look directions have approved source art.

`tools/import_reimu_chew_v7_running.py` is the guarded one-time importer for
this row. It accepts only the confirmed chew-v7 Harness build and refuses any
source identity or pixel digest drift.

`tools/import_reimu_idle_v1.py` provides the same fail-closed boundary for the
idle source: it pins the confirmed animation id, plan/source hashes, all six
frame hashes, the nearest-neighbor cell conversion, and the authorization.

`tools/import_reimu_waiting_v1.py` provides the same fail-closed boundary for
the waiting source and pins its confirmed animation id, plan/source hashes,
all six frame hashes, conversion, row timing, and authorization.

`tools/import_reimu_review_v1.py` provides the same fail-closed boundary for
the review source, including the corrected single-line eyebrow frame hashes,
conversion, shipped row timing, and authorization.
