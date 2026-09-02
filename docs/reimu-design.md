# Hakurei Reimu pet design

Status: **Milestone 0 design brief; art not yet approved or generated**

## Character read

Reimu must remain unmistakable at desktop-pet scale through a small set of controlled signals:

- black hair with a simple, readable silhouette;
- a large red hair bow that remains visible in side and look-direction poses;
- a red-and-white shrine maiden outfit with detached-sleeve readability;
- compact chibi proportions and low visual noise;
- economical expressions built from a shared face grid;
- a dry, cozy comedic tone rather than melodrama.

Do not use a glossy, heavily rendered, generic AI-anime face. The face should be manually authored and reused as a controlled construction across poses.

## Scene and prop vocabulary

The core scene is Reimu at a small low table. Food and work coexist in one compact silhouette. Approved candidate props are:

- onigiri;
- a small tea cup or yunomi;
- miso soup;
- one small side-dish plate;
- skewers and compact snacks;
- a short task slip or rolled note for review, if it is established as part of the base prop vocabulary;
- an optional yin-yang orb for a jump/flying accent.

The scene should evoke cozy everyday Gensokyo without reproducing Touhou Mystia's Izakaya layouts, sprites, UI, dishes, or decorative assets.

## Standard-state performances

| Codex row | Reimu interpretation |
| --- | --- |
| `idle` | Relaxed at the table; quiet breathing, blink, or one small tea sip. First frame must be a strong still. |
| `running-right` | Low-altitude flight or shrine-maiden glide to the right; props must remain attached and readable. |
| `running-left` | Matching leftward flight; mirror only if bow, sleeves, and props remain correct. |
| `waving` | Simple shrine-maiden greeting with one controlled hand motion. |
| `jumping` | Small lift or float; an attached yin-yang-orb interaction is optional. |
| `failed` | A small comic mishap such as fumbling or dropping the held onigiri within the connected silhouette. |
| `waiting` | Head near the table or slowly eating, but eyes/pose must clearly ask the user for input. |
| `running` | Focused eating-while-working loop. The native sheet provides one workload appearance only. |
| `review` | Reimu inspects an established task slip/scroll while eating; finished work should read as ready, not blocked. |
| look rows | Eyes lead, then head/bow subtly follow; table and lower-body anchor remain stable. |

Avoid detached motion lines, floating punctuation, glow, floor shadows, loose tears, or decorative particles. Any comic effect must remain attached to the sprite and legible within one 192×208 cell.

## Face system

The first art review should approve a neutral face construction before animation:

1. fixed head silhouette and hairline;
2. fixed eye baseline and spacing;
3. a tiny set of eye shapes: neutral, focused, tired, squeezed/crying;
4. a tiny set of mouths: neutral, eating, small smile, comic distress;
5. no frame-specific redraw that changes apparent age, eye style, nose, or head volume.

Expressions should work through pixel placement and silhouette rather than gradients or detailed irises.

## Task-count food comedy

The visual progression uses six discrete, numbered compositions:

| `ReimuFoodTier` | Active-task meaning | Composition direction | Reimu read |
| ---: | ---: | --- | --- |
| `0` | exactly 0 | no task-linked serving; only approved invariant props may remain | resting, observant |
| `1` | exactly 1 | one clearly readable serving | unhurried eating |
| `2` | exactly 2 | two clearly readable servings | comfortably occupied |
| `3` | exactly 3 | three clearly readable servings | focused, brisk rhythm |
| `4` | exactly 4 | four clearly readable servings | table feels full but ordered |
| `5` | 5 or more | five readable primary servings; compact abundance accents may reinforce the cap | cute, tearful determination rather than distress |

Each higher tier adds one task-linked serving in a stable slot. Onigiri is the preferred primary token because its silhouette survives at pet scale; tea, dishes, or condiments may be invariant or decorative only if they cannot be mistaken for additional task tokens. Tier `5` is intentionally saturated: it does not claim to distinguish five tasks from six or more.

These are variant specifications, not claims about the current static Codex sheet. The current v2 format has only one `running` row and exposes no task count to the custom pet package.

## Approval gates before animation

Do not produce a final sprite sheet until maintainers approve:

- one neutral front construction and silhouette;
- face grid and expression vocabulary;
- logical pixel scale and exact bounding box;
- palette swatches and outline hierarchy;
- low-table footprint and baseline;
- five serving slots, invariant props, and tier `0` through tier `5` compositions;
- approach for workload variants under the actual available runtime interface.

See [the production visual specification](../pets/reimu/design/visual-spec.md) for measurable constraints.
