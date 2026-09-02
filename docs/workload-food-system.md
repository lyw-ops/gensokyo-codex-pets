# Workload-to-food system

Status: **behavior specification; no live integration implemented**

## Domain model

The visual layer should consume a semantic value, not raw Codex counters:

```text
WorkloadLevel = calm | normal | busy | overloaded
```

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

The default `activeTaskCount` should count unique, non-archived chats currently reported as running or pending. Tasks waiting for user input, blocked tasks, and completed unread tasks remain separate signals; they should not silently inflate the active count.

## Default configurable policy

| WorkloadLevel | Active tasks | Food composition | Reimu read |
| --- | ---: | --- | --- |
| `calm` | 0–1 | one onigiri, tea | relaxed |
| `normal` | 2–4 | two onigiri, tea, miso soup, one side dish | engaged |
| `busy` | 5–8 | several onigiri, skewers, soup, snacks | increasingly busy |
| `overloaded` | 9+ | absurdly full table | crying while eating; comic and cute |

Thresholds must live in one policy/configuration object. Callers consume the resulting level and must not repeat raw ranges.

Illustrative configuration shape:

```json
{
  "levels": [
    { "id": "calm", "minActiveTasks": 0, "maxActiveTasks": 1 },
    { "id": "normal", "minActiveTasks": 2, "maxActiveTasks": 4 },
    { "id": "busy", "minActiveTasks": 5, "maxActiveTasks": 8 },
    { "id": "overloaded", "minActiveTasks": 9, "maxActiveTasks": null }
  ],
  "enterDelayMs": 3000,
  "exitDelayMs": 8000,
  "minimumLevelDwellMs": 15000
}
```

Entry/exit delays and minimum dwell time prevent the table from visibly popping between food arrangements during short task transitions.

## Separation of concerns

### A. Visual assets

Define one approved table/food composition per `WorkloadLevel`, sharing Reimu's construction, palette, baseline, and prop scale. Do not encode task numbers into filenames or redraw the character identity per tier.

### B. Codex compatibility

Assemble and validate the fixed standard state rows required by the selected pet format. This layer knows row order and metadata, not how workload is counted.

### C. Dynamic behavior

Observe a supported Codex activity interface, normalize it into `WorkloadSnapshot`, apply policy and hysteresis, then ask the compatibility layer for a visual variant. The observer must be replaceable because Codex interfaces can change.

## Current feasibility

The current local v2 package is a static manifest plus sprite sheet. It has one `running` row and no custom script or task-count field. The app itself knows activity counts for its tray, but the custom pet sprite component receives a resolved standard state rather than the count.

Consequences for Phase 1:

- the calm Reimu composition can be the first static prototype;
- food tiers can be designed as separate source variants without claiming they switch live;
- a proof of dynamic behavior must wait for a supported API, hook, or separately reviewed adapter;
- periodically rewriting installed sprite files or scraping private state should not be treated as an acceptable production design without an explicit reliability and safety review.

If the activity source is unavailable, the adapter should report `sourceAvailable: false` and use the calm visual fallback. It must not invent a count.

## State interaction rules

Workload level and Codex state are orthogonal:

```text
VisualVariant = Character × CodexState × WorkloadLevel
```

Not every combination needs unique art. Workload primarily affects `running` and possibly `idle`; `waiting`, `review`, and `failed` should preserve their required semantic read while reusing the current table load when technically possible.

Priority should remain consistent with Codex: needs input, blocked, ready/unread, then running. A high food tier must never hide a waiting or failure cue.

## Future acceptance tests

- Boundary counts map correctly: 0, 1, 2, 4, 5, 8, 9.
- Archived, waiting, blocked, and ready/unread tasks are not counted as active by default.
- Duplicate task observations are deduplicated.
- Temporary source loss selects the explicit calm fallback and exposes degraded status.
- Threshold changes require only configuration edits.
- Hysteresis prevents rapid tier oscillation.
- Standard Codex state priority remains readable at every food tier.
