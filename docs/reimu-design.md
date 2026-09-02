# Hakurei Reimu pet design

Status: **Milestone 0 design brief; art not yet approved or generated**

Reimu's full behavior system — the finite state machine, autonomous idle vocabulary, sleep chain, interaction reactions, and incident chain — is specified in [reimu-action-system.md](reimu-action-system.md). This brief keeps the character read, prop vocabulary, and the food-tier comedy; the action system defines how those elements move.

## Character read

Reimu must remain unmistakable at desktop-pet scale through a small set of controlled signals:

- black hair with a simple, readable silhouette;
- a large red hair bow that remains visible in side and look-direction poses;
- a red-and-white shrine maiden outfit with detached-sleeve readability;
- compact chibi proportions and low visual noise;
- economical expressions built from a shared face grid;
- a dry, cozy comedic tone rather than melodrama;
- the core temperament contrast: unhurried and low-motivation when nothing is happening, instantly sharp and fast when something real occurs. She must never read as a permanently busy AI mascot.

Do not use a glossy, heavily rendered, generic AI-anime face. The face should be manually authored and reused as a controlled construction across poses.

## Scene and prop vocabulary

The core scene is Reimu at a small low table. Food and work coexist in one compact silhouette. Approved candidate props are:

- onigiri;
- a small tea cup or yunomi;
- miso soup;
- small side-dish plates such as pickles or edamame;
- one compact noodle bowl at a high food tier;
- tamagoyaki or another rectangular side with a strong silhouette;
- skewers and compact snacks;
- a short task slip or rolled note for review, if it is established as part of the base prop vocabulary;
- an optional yin-yang orb for a jump/flying accent.

The scene should evoke cozy everyday Gensokyo without reproducing Touhou Mystia's Izakaya layouts, sprites, UI, dishes, or decorative assets.

## Standard-state performances (Codex standard actions)

These are the performances that can ship inside the current static v2 atlas. Each row is the Codex-mappable projection of a richer behavior defined in [reimu-action-system.md](reimu-action-system.md).

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

## Extended Reimu behavior vocabulary

Beyond the fixed Codex rows, Reimu has a full character-behavior vocabulary specified in [reimu-action-system.md](reimu-action-system.md) and registered in [`pets/reimu/metadata/actions.json`](../pets/reimu/metadata/actions.json):

- **autonomous idle behaviors** — tea (`idle_tea`), cloud watching (`idle_cloudwatch`), table slouch (`idle_table_slouch`), half-hearted sweeping (`idle_sweep`), ofuda glance (`idle_ofuda_check`), yin-yang orb fidget (`idle_yinyang`);
- **a sleep chain** — `idle_yawn → doze_nod → sleep_table`, exited only through `wake_up`;
- **interaction reactions** — cursor gaze, click notice, poke frown, repeated-poke ofuda warning, drag-as-flight and gentle landing;
- **an incident chain** — the lazy-to-competent snap (`incident_notice → incident_ready → incident_fly`), design-only until a supported urgent-event source exists;
- **an eating vocabulary** — shared bite/sip/chew beats that reuse one body construction across all food tiers.

The extended vocabulary is a design-layer contract for a future runtime adapter or extended shell. The current Codex custom pet API cannot invoke these actions; the static atlas compresses the idle vocabulary into one composed idle row and ships exactly one appearance per standard row. Pacing follows one principle: **Reimu should feel alive, not busy** — most of the time she is simply sitting there, unhurried.

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
| `0` | exactly 0 | nearly empty table with tea as the sole food-related anchor | chin-in-hand waiting, quiet boredom |
| `1` | exactly 1 | compact first meal centered on a held onigiri and tea | eating begins; strong comic relief or emotion is possible |
| `2` | exactly 2 | small set meal with onigiri, soup, a small side, and tea | occupied but still contained |
| `3` | exactly 3 | full set meal with a larger staple group and several side dishes | visibly enthusiastic |
| `4` | exactly 4 | large feast adding a substantial hot dish and wider table coverage | delighted effort, with a restrained sweat cue possible |
| `5` | 5 or more | maximum table-filling banquet with the broadest approved dish variety | streaming comic tears while still eagerly eating |

The task count selects a whole composition; food items are not a literal counter. Successive tiers should read through meal scale, dish variety, occupied tabletop area, and Reimu's performance. Tea is a recurring anchor, tier `0` is the only non-eating composition, and a held onigiri is the preferred common action for tiers `1` through `5`. Tier `5` is intentionally saturated and does not claim to distinguish five tasks from six or more.

The six maintainer-provided GPT images are composition prototypes, not source art or a locked model sheet. Their embedded task signs, shrine-room background, flowers, daruma, donation objects, detailed glossy face rendering, and exact pixels are excluded from the pet asset. Only the broad staging and abundance progression may inform original production art.

These are variant specifications, not claims about the current static Codex sheet. The current v2 format has only one `running` row and exposes no task count to the custom pet package.

## Approval gates before animation

Do not produce a final sprite sheet until maintainers approve:

- one neutral front construction and silhouette;
- face grid and expression vocabulary;
- logical pixel scale and exact bounding box;
- palette swatches and outline hierarchy;
- low-table footprint and baseline;
- recurring tea and held-food anchors, exact dish vocabulary, and tier `0` through tier `5` meal-density compositions;
- a simplified expression progression translated from the prototypes onto the approved face grid;
- approach for workload variants under the actual available runtime interface.

See [the production visual specification](../pets/reimu/design/visual-spec.md) for measurable constraints.
