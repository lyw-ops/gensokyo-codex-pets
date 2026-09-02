# Reimu production visual specification

Status: **provisional values for review; not a locked model sheet**

## Canvas and pixel method

Final Codex cell: **192×208 px**.

Preferred first experiment: author on a **96×104 logical grid** and upscale exactly 2× with nearest-neighbor sampling. This keeps the face and line work manually controllable while satisfying the native cell contract. Compare this against native-resolution pixel work before locking the pipeline.

Candidate safe bounds at final resolution:

- leave at least 12 px above the bow at its highest neutral position;
- leave at least 14 px on both sides for non-locomotion rows;
- keep the table/feet baseline in a stable band around y=188–194;
- reserve extra vertical travel for the jumping row rather than scaling the character down per frame;
- keep detached sleeves visually connected by overlap or a deliberate readable gap that survives transparency cleanup.

These bounds are candidates and must be validated across every pose before approval.

## Proportions

- Head, including hair but excluding the bow: approximately 48–55% of standing character height.
- Bow: wide enough to remain Reimu's strongest upper-silhouette landmark, but never clipped in look poses.
- Body: compact with short limbs; detached sleeves must not read as unrelated floating components.
- Low table: wider than the torso but narrow enough to leave side margins and keep food silhouettes separate.
- Food: exaggerate shape differences rather than adding surface detail.

## Face grid

Create one shared head template with fixed anchors for:

- eye baseline and inter-eye distance;
- hairline and side locks;
- mouth center;
- bow knot center;
- chin and cheek width.

Use no more than four approved eye families and four mouth families in Phase 1. Directional looks should shift the eyes first and alter head silhouette only where needed. No detailed nose rendering, glossy multi-highlight irises, airbrushed skin, or frame-specific face proportions.

## Provisional palette

These swatches are original working targets, not sampled reference colors. Lock them only after reference and contrast review.

| Role | Candidate |
| --- | --- |
| outline | `#3A2228` |
| hair dark | `#201C22` |
| hair light | `#3B3037` |
| bow red | `#D83B3B` |
| deep red | `#A8262E` |
| outfit red | `#B72E39` |
| warm white | `#FFF4E4` |
| white shadow | `#E8D8C8` |
| skin | `#F4D0B5` |
| skin shadow | `#DDAE95` |
| table wood | `#9B5A3C` |
| tea green | `#7FA166` |
| rice highlight | `#FFF6DC` |

Prefer a compact shared palette and hard-edged clusters. Add colors only when they improve actual-size readability.

## Silhouette invariants

Every frame must preserve:

- clearly black/dark hair mass;
- a dominant red bow above or beside the hair silhouette;
- red torso/skirt mass separated from white blouse/sleeves;
- one consistent head volume and face placement;
- stable table scale and lower-body anchor in non-locomotion rows;
- readable onigiri triangle/rounded-triangle shapes without tiny garnish noise.

## Task-count composition plates

Design six plates named `tier-0` through `tier-5`. They must reuse the same table footprint, camera, dish scale, Reimu construction, and baseline so a tier change does not look like a zoom or pose reset.

- Tier `0`: nearly empty table, stable tea anchor, Reimu resting with chin in hand rather than eating.
- Tier `1`: compact first meal, with Reimu holding an onigiri and tea retained.
- Tier `2`: small set meal, adding a staple plate, soup, and one small side.
- Tier `3`: full set meal, enlarging the staple group and adding a small number of strongly differentiated sides.
- Tier `4`: large feast, introducing one substantial hot-dish silhouette and broader table coverage.
- Tier `5`: maximum banquet, combining the broadest approved dish vocabulary with a controlled streaming-tears expression.

The number names the selected composition; it does not require the same number of food items. Preserve a recurring tea position and a common held-onigiri action for tiers `1` through `5` when animation semantics permit. Add supporting dishes from stable center and side zones so the family feels cumulative even when exact items change. Distinguish adjacent tiers by large silhouette groups and occupied area, not by tiny garnish or an item count that disappears at intended display size.

Tier `5` must look saturated but remain inside the cell and preserve Reimu's face, bow, sleeves, state cue, and transparent perimeter. Do not include a task-count sign, room background, lantern, flower vase, daruma, donation bottle, wall notices, or other environmental storytelling elements from the composition prototypes.

## GPT visual-prototype translation

The six maintainer-provided GPT images are 1448×1086 opaque landscape illustrations with embedded `0 tasks` through `5 tasks` signs. They are approved for internal composition study only and remain outside the repository.

Do not crop, downscale, trace, palette-sample, or reuse pixels from them. Translate only these high-level observations into original pet art:

- the jump from tea-only repose at tier `0` to active eating at tier `1`;
- a centered Reimu, low table, recurring tea cup, and held-onigiri action;
- increasing meal scale, variety, and tabletop occupancy through tiers `1` to `5`;
- a restrained expression arc ending in comic streaming tears at tier `5`;
- warm, cozy shrine-room atmosphere expressed within the character-and-table silhouette rather than through a full background.

## Art review sheet required before animation

The review sheet should show, at minimum:

- neutral front at 1× and intended display scale;
- black-on-white silhouette;
- flat-color palette key;
- neutral, focused, waiting, failed, and maximum-tier faces on the same head grid;
- a single contact sheet of tier `0` through tier `5`, with recurring anchors and occupied-area growth annotated outside the sprite cells;
- tier `0`, tier `1`, and tier `5` at intended display scale;
- front, right, back, and left directional anchors;
- a reduced-motion candidate frame.

No animation production begins until this sheet is explicitly approved.
