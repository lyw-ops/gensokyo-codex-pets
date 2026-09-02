# Reimu task-to-food system

Status: **behavior specification; no live integration implemented**

## Domain model

The visual layer consumes a discrete, Reimu-specific tier:

```text
ReimuFoodTier = 0 | 1 | 2 | 3 | 4 | 5
```

For an available source reporting a valid non-negative integer active-task count, selection is:

```text
ReimuFoodTier = min(activeTaskCount, 5)
```

Tiers `0` through `4` therefore preserve the exact count. Tier `5` is a deliberate visual cap representing **five or more** active tasks. The adapter must preserve the uncapped observed count in its snapshot or diagnostics; the art must not imply that tier `5` distinguishes counts above five.

A future adapter may build a snapshot like:

```text
WorkloadSnapshot
  observedAt
  activeTaskCount
  needsInputCount
  blockedCount
  readyUnreadCount
  activeAgentCount?      # only if a supported source exposes it
  source
  sourceAvailable
```

`activeTaskCount` counts unique, non-archived tasks currently reported as running or pending by the supported source. Tasks waiting for user input, blocked tasks, and completed unread tasks remain separate signals; they do not silently inflate the active count. A negative, fractional, missing, or otherwise invalid count is unavailable data, not a value to coerce into a tier.

## Fixed selection policy

| Observed active tasks | `ReimuFoodTier` | Visual meaning |
| ---: | ---: | --- |
| `0` | `0` | tea-only, nearly empty table |
| `1` | `1` | compact first meal |
| `2` | `2` | small set meal |
| `3` | `3` | full set meal |
| `4` | `4` | large feast |
| `5` or more | `5` | maximum table-filling banquet; visual capacity reached |

This mapping is the design contract, not a configurable table of workload ranges. It must be implemented once at the policy boundary. Animation and rendering code consume `ReimuFoodTier` and must not introduce named bands, alternate thresholds, or special mappings for particular rows.

A configuration may control transition timing and unavailable-source behavior without changing the count-to-tier meaning:

```json
{
  "maximumVisualTier": 5,
  "unavailableSourceTier": 0,
  "transitionDebounceMs": 3000
}
```

`maximumVisualTier` records the fixed contract for validation; a value other than `5` is incompatible with the Phase 1 Reimu design. A debounce may delay a visual swap during a brief observation transition, but it must not merge adjacent counts into wider bands.

## Food composition contract

`ReimuFoodTier` is an ordinal composition choice, not a literal food-item counter. A tier may contain more onigiri or dishes than its numeric value. The six plates communicate progression through the combined silhouette of the meal, dish variety, tabletop occupancy, and Reimu's expression and eating pose.

- Tier `0` keeps the table nearly empty, with tea as the sole food-related anchor and Reimu not yet eating.
- Tiers `1` through `3` progress from a compact first meal to a small and then full set meal.
- Tier `4` introduces a large feast with a substantial hot dish and wider table coverage.
- Tier `5` is the maximum banquet, using the broadest approved dish variety and a comic tearful performance.
- Tea should remain a stable anchor across the family when cell space permits.
- A held onigiri should unify tiers `1` through `5`; supporting dishes expand outward from stable zones rather than jumping randomly between frames.
- Adjacent tiers must remain distinguishable at intended display size even when individual foods lose detail.
- Tier `5` must look saturated without implying any exact count above five.

Every plate shares Reimu's construction, palette, camera, table footprint, baseline, and prop scale. Source and export names may use `tier-0` through `tier-5`; they must not encode uncapped counts such as `tier-6`. The pet art must not include an explanatory task-number sign: that was a visual-prototype aid, not part of the character asset.

## Separation of concerns

### A. Visual assets

Define one approved composition per `ReimuFoodTier`. This layer knows the six visual plates but not where the observed task count came from.

### B. Codex compatibility

Assemble and validate the fixed standard state rows required by the selected pet format. This layer knows row order and metadata, not how active tasks are counted.

### C. Dynamic behavior

Observe a supported Codex activity interface, normalize it into `WorkloadSnapshot`, validate the count, apply the centralized cap and any transition debounce, then ask the compatibility layer for a visual variant. The observer must be replaceable because Codex interfaces can change.

## Current feasibility

The current local v2 package is a static manifest plus sprite sheet. It has one `running` row and no custom script or task-count field. The app itself knows activity counts for its tray, but the custom pet sprite component receives a resolved standard state rather than the count.

Consequences for Phase 1:

- tier `0` can inform the static `idle` composition and tier `1` can inform the static `running` composition, but those rows remain symbolic rather than count-reactive;
- all six tiers can be designed as separate source variants without claiming they switch live;
- a proof of dynamic behavior must wait for a supported API, hook, or separately reviewed adapter;
- periodically rewriting installed sprite files or scraping private state is not an acceptable production default without an explicit reliability and safety review.

If the activity source is unavailable or its count is invalid, the adapter reports `sourceAvailable: false`, selects tier `0` as an explicit degraded fallback, and preserves the error reason. It must not invent a count or report the fallback as an observed zero.

## State interaction rules

Task-count tier and Codex state are orthogonal:

```text
VisualVariant = Character × CodexState × ReimuFoodTier
```

Not every combination needs unique art. The tier primarily affects `running` and may affect `idle`; `waiting`, `review`, and `failed` must preserve their required semantic read while reusing the selected table load when technically possible.

Priority remains consistent with Codex: needs input, blocked, ready/unread, then running. Tier `5` must never hide a waiting, failure, or review cue.

## Future acceptance tests

- Counts `0`, `1`, `2`, `3`, and `4` select matching tiers.
- Counts `5`, `6`, and a large valid integer all select tier `5` while the snapshot retains the original count.
- Archived, waiting, blocked, and ready/unread tasks are not counted as active by default.
- Duplicate task observations are deduplicated.
- Negative, fractional, missing, and malformed counts select the explicit degraded fallback rather than being coerced.
- Temporary source loss selects tier `0`, exposes degraded status, and does not claim an observed zero.
- Transition timing does not redefine or merge count tiers.
- All six plates preserve recurring visual anchors and form a clearly ordered meal-density progression at intended display size.
- No plate relies on embedded task-count text or a literal one-item-per-task rule.
- Standard Codex state priority remains readable at every tier.
