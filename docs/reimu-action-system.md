# Reimu action system

Status: **Behavior specification with a partially implemented native runtime. Current installed-build and implementation evidence lives in `HANDOFF.md`; this document is the authoritative behavior design. The latest design decision below governs, and a design decision is not by itself an asset, runtime, installation, or visual-approval claim.**

## Latest design decision — 2026-09-19: workload eating, idle onigiri, and an independent grabbed pose

The maintainer reaffirmed the project's original central metaphor: **when Codex is
actively working, Reimu is eating**. The number of concurrently active tasks selects
the eating presentation through `ReimuFoodTier = min(activeTaskCount, 5)`. This
supersedes any later wording that treated working as neutral standing or made eating
only an idle activity. It does not make eating the source of task truth: the observer
and task card remain authoritative, and animation never creates or changes work.

The approved visual reference is
[`docs/reference/reimu/eating_set_v1/eating-set-v1-sheet.png`](reference/reimu/eating_set_v1/eating-set-v1-sheet.png).
It is a composition and emotion reference, not an instruction to copy detached effects
into every runtime frame. Read left-to-right, top-to-bottom:

| Active tasks | Food tier | Work presentation |
| ---: | ---: | --- |
| 0 | 0 | No work meal. The empty-table, bored/slouch image informs tier-0 idle actions; the normal base may remain the approved standing blink. |
| 1 | 1 | One onigiri; touched and tearful, eating earnestly. |
| 2 | 2 | Two onigiri plus tea; residual wetness, visibly more settled than tier 1. |
| 3 | 3 | Rice and a modest side dish; content, no tears. |
| 4 | 4 | A richer noodle/dumpling meal; clearly delighted and more energetic. |
| 5+ | 5 | Capped banquet; laughing while crying from delight. More tasks never create a seventh tier. |

All tiers share one `work_eating` behavior family. The body construction, table,
anchor, and reusable bite vocabulary should be shared; table-food layers and a small
expression set carry the tier identity. A task-count change swaps the tier composition
at a safe loop boundary without restarting the FSM node. Hearts, sparkles, sweat drops,
and steam in the concept sheet are optional mood cues, not mandatory detached sprite
effects; prefer face, pose, timing, and meal richness at actual pet size.

Current native coverage is deliberately narrower than this complete design. Tier 2 has
the approved 16-frame exact chew loop. Tier 3 has a separate native identity backed by
the byte-exact existing Eating Set v1 still; the user approved its native size and pose
on 2026-09-20, so production-identity packaging is allowed. Because no reviewed
multi-frame or layered tier-3 source exists, it is still a static hold and is not an
animation-completion claim. Tiers 1, 4, and 5 remain explicit standing fallbacks. A
damaged optional tier package degrades only that tier, and no tier may borrow another
tier's artwork.

Eating an onigiri also remains a separate idle behavior:

- `idle_onigiri` is a bounded autonomous one-shot available only while the observed
  base is idle. It uses a neutral or quietly pleased expression, not tier 1's work-linked
  tears, so an idle snack cannot be mistaken for one active task.
- `feed_onigiri` is the design name for the existing user-requested/manual feeding episode
  (`feed` in the current native runtime). It may share the
  same core clip with `idle_onigiri`, but the trigger, cooldown, logging, and interruption
  reason remain distinct.
- Neither action changes `activeTaskCount`. If real work begins during an idle snack,
  the runtime changes to `work_eating[min(activeTaskCount, 5)]` at the nearest safe
  frame; no snack or work action is queued for replay.

Dragging has its own native action and artwork. `drag_float` means **caught and held by
the pointer**, not ordinary standing, eating, or voluntary left/right flight:

- the low table, tatami, and food disappear for the held pose;
- feet leave the baseline while sleeves, hair, skirt, and bow hang with restrained
  downward follow-through;
- the face reads briefly surprised and then mildly displeased, never limp or panicked;
- pointer motion may produce a small lag/sway, but it must not select or reuse
  `fly_low_left` / `fly_low_right` artwork;
- release plays the independent `drag_land` transition and then resolves the latest
  base. A task-count or status change while held updates that return target; the runtime
  never restores stale pre-drag food or state.

The Codex static v2 atlas may still use `running-left` and `running-right` for its own
standard directional contract. That compatibility mapping is separate from the native
desktop runtime's required grabbed pose and must not be used to claim the independent
native interaction is drawn or implemented.

The intended presentation selector is therefore:

```text
failed / critical state  -> fail_fumble
pointer held             -> drag_float -> drag_land -> latest base
explicit user action     -> click reaction or feed_onigiri -> latest base
working                  -> work_eating[min(activeTaskCount, 5)]
idle                     -> idle base + eligible autonomous actions, including idle_onigiri
```

This section freezes behavior semantics only. `idle_onigiri` and the independent
caught/landing art still require authored assets, Harness validation, native integration,
normal-size visual QA, and explicit approval before they can be reported as production.

## Current implementation — 2026-09-20: native tier-2 through tier-5 vertical slice

The native observer-to-artwork path now preserves `WorkStatus.active` through
`PetBehavior.setWorkStatus`. When the observed base is `working` and the exact count is
two, the selector uses the explicit `work_eating_task_2` runtime identity and the approved
16-frame `task_2-chew-v9` package at 10 fps. Exact counts three and four use the separate
`work_eating_task_3` and `work_eating_task_4` identities. The capped tier for five or more
uses `work_eating_task_5` through that same mapping boundary. Tiers three through five each
hold one immutable Eating Set frame; they are static native poses, not completed eating
animations. All four identities are separate from the generic manual/idle eating clip; no
filename inference is used.

This is deliberately partial coverage:

- `ReimuFoodTier` remains `min(activeTaskCount, 5)`, while the uncapped observed count
  remains in `WorkStatus` and the status card. Animation never writes task truth.
- tier 1 uses a named standing fallback. Counts above five cap at tier 5 and select the
  same `work_eating_task_5` identity; there is no distributed second `>= 5` threshold.
- ordinary count changes commit at the current visual loop boundary. Leaving `working`
  and the existing higher-priority failure, waiting, click, drag, and pause paths preempt
  immediately. Recovery resolves the latest observed count rather than a stale tier.
- reduced motion holds frame 0 for all four tiers. A missing base/frame or identity/digest
  mismatch degrades only that tier to standing and leaves the existing clips available.

The source frames and provenance files are unchanged. The user approved the current
native tier-2 loop preview on 2026-09-19 and the tier-3, tier-4, and tier-5 static previews
on 2026-09-20. Tiers 4 and 5 therefore no longer have preview-only packaging gates, but no
formal Tier 4 or Tier 5 package was generated or installed in those approval steps.
Installation remains open. Tier 1, `idle_onigiri`, `drag_float`, and `drag_land` remain unimplemented
artwork/runtime deliveries except for their previously documented honest fallbacks.

**Transition backlog.** A later, separately gated delivery may add authored transitions
for standing/fallback → task_2 entry, task_2 → another base exit, cross-tier composition
changes once those tiers exist, and recovery from a transient action into the latest work
tier. These transitions must not delay failure, needs-input, drag, click, or pause
preemption; recovery must still read the newest observed count. The current direct switch
remains the approved tier-2 baseline until replacement transitions pass their own source,
technical, native visual, and consumer gates.

## Current implementation — 2026-09-16: declarative action registry and the chewing pause

The action layer is now data instead of branches, and the first new action since 1.3 ships on it.
Nothing was drawn for this round: the whole app still contains eleven PNGs (standing `base`,
`poses/closed`, `poses/half`; seven unique eating frames; one annoyed reaction).

**P0 — infrastructure.** `PetBehavior` gained four pieces the catalog below needs:

- `ActionSpec` declares duration, priority, caption, artwork, rest, lock, reaction art, frame
  program and default continuation. Adding an action is one enum case plus one table row; the
  presentation path no longer switches on action names.
- `FramePlan` (`still` / `table` / `ramp` / `loop`) makes frame selection data. The existing
  actions' hardcoded index tables were moved into it unchanged.
- Two-level rest: `cooldown` is how long an action waits for its own repeat, `globalRest` is the
  pacing floor between any two self-started behaviors. The meal keeps 180 s for both, so a future
  cheap beat can rest briefly for everyone while still waiting a long time for itself.
- A weighted pool (`PoolEntry`) with per-entry eligibility, plus explicit continuations: a pool
  entry may declare `then`, and only a *completed* action continues — every interruption returns
  to the base. Held actions (`duration: nil` with `maxHold`) are supported for the future
  table-slouch and sleep stages.

`ClipSpec.registry` in `main.swift` does the same for artwork: canvas side, frame count, fps,
manifest identity, Info.plist digest keys, frame-file resolver and window placement are one row
per clip. The loader, the placement function, hit testing and the drawing path all read the
registry, so a third clip is a row plus a `PetArtwork` case rather than another ternary.

**P1 — `pause_chew`.** The approved autonomous meal keeps its exact pacing (60 s quiet, 25 %,
30–45 s retry, 180 s rest) and its exact random draw count and order. The 25 % is split into
15 % plain meal and 10 % meal that continues into a two-second chewing pause: chewing slows to
two pulses (eating frames 4-7), the gaze drifts behind half-lidded eyes (frame 27, held 0.6 s),
then she looks up (frame 31) and settles (frame 0). The fully closed eye (frame 29) is
deliberately unused — this is a drift, not a blink. The 180 s rest is measured from the end of
the whole episode, so the pause does not make her eat sooner. Because the continuation reuses
the roll that already started the meal, it costs no extra random draw.

Validation: 99 behavior checks (84 previous ones pass verbatim), 29 native checks, 5 standing,
3 reaction, 28 status contract, 14 bridge tests, 74 builder tests and the repository gate.
Version 1.8 / build 10 is buildable; the installed app was not replaced in this round.

**Re-ranked, not done.** `look_at_food` and a seated blink were expected to be free, but the app
loads only `688×688 reference_onigiri_example/eat_blink` and `1254×1254 neutral_standing_v1/
idle_blink`, while the layered rig and the `eating/task_2` chew-v9 sequence are `596×596`. Those
two tracks have never been connected, so both actions need the canvas reconciliation that the
standing/seated transition also needs — they are not cheap runtime-only wins.

## Current app — 2026-09-07: one merged 1.7 build with an observation log

The user asked to keep a single 灵梦 app and merge the features, so the preview identity was
rebuilt under the installed identity as 1.7/build 9 at `/Users/lyuyuwei/Applications/灵梦桌宠.app`.
1.0 → 1.7 is one linear source lineage, so no archived build held a behavior 1.7 lacks; 1.3's
work-time endless eating had already been replaced by the approved standing default and bounded
idle meal, and was not restored. Seventeen historical bundles moved to
`.codex/artifacts/reimu-app-archive-20260907/` with a manifest and a restore script; nothing was
deleted. Resources are byte-identical to the approved 1.6 preview and a strict superset of 1.3's.

The behavior rules below are unchanged. What is new is observation only: `PetBehavior.onTrace`
(nil by default) plus `PetLog` append one JSON object per line to
`~/Library/Logs/ReimuPet/behavior.jsonl` for base changes, action start/end with reason, the real
`meal_attempt` roll and retry interval, gates, observed work snapshots and user input. Random draw
count and order are unchanged and all 66 approved behavior checks still pass verbatim. The menu
gained a real autonomy countdown and a reveal-log item; opening the menu is itself a suppressing
gate that restarts the 60-second quiet interval, so the log is the non-intrusive instrument.

Real-event probes (read-only, nothing injected): `working`, `round_ended`, `interrupted` and
`closed` are confirmed by real hook events; `needs_input` and `failed` have never been driven by
one, because they need `PermissionRequest` / matcher-gated `Notification` / `Elicitation` and
`StopFailure`, of which zero have ever arrived. `PostToolUseFailure` does arrive but observer.py
maps it to `working` on purpose. 84 behavior and 29 native checks pass.

## Superseded native implementation — 2026-09-07: approved bounded idle meal

The user approved the 8142 default `cut/`, aligned placement and 8-second meal, then
requested implementation and updated handoffs. Final preview 1.6/build 8 lives under
`.codex/artifacts/reimu-native-idle-meal-20260907-final/`; installed 1.3 is preserved.
Only observed `idle` is eligible after 60 quiet seconds. Each attempt has 25% chance;
a skipped attempt waits 30–45 seconds. Two original four-second cycles play once,
then cut to open-eye standing. Completion or interruption imposes 180 seconds before
another automatic meal, combined with 60 seconds of renewed quiet after interaction.
These deadlines use a process-local monotonic clock; restart begins a fresh 60-second
quiet period. There is no catch-up queue or work-count mutation.

Non-idle work status, clicks and dragging preempt the automatic meal. Pause, reduced
motion, sleep, pointer-held and menu-open gates suppress autonomy and reset eligibility
on resume; asset fallback also disables autonomy. Manual feeding remains four seconds;
annoyed art/lock, failure priority and latest-state restoration remain intact.

Whole-image uniform placement follows the approved 596 px Harness preview; alpha hit
testing uses the same drawing rectangle. The original PNG bytes are unchanged.
AppKit resampling is not claimed pixel-identical to the Pillow preview. This is a
whole-pose cut with aligned shoe/skirt-shadow support edges, not authored sit/stand
motion or anatomical layers. 66 behavior and 25 native checks pass; long-term real idle
random playback is still a user experience check. No probes or monitoring were added.
All sections below preserve the earlier design/review history; pending wording and
older versions there do not supersede this section or the top of HANDOFF.md.

## Historical offline preview — 2026-09-07: bounded meal and aligned pose switching

The next stage now has a local review page at http://127.0.0.1:8142/ (Harness
`build/reimu-idle-meal-transition-20260907-v1/`). Two existing 4-second eating cycles
form an 8-second meal inside a non-looping 12-second preview. Standing shoes and the
seated skirt/shadow support edge are aligned on a common 596 px canvas with uniform
scaling. `cut/` and `fade/` are the current candidates; fade is a 200 ms single-pose
fade-out/fade-in, not authored sit/stand motion. The overlapping `dissolve/` candidate
was visually rejected for double faces despite passing structural checks.

Sizing, duration and transition selection await user review before native integration.
A schedule is only proposed (60 seconds quiet idle, 30–45 second attempts, 25 percent
chance, at least 180 seconds cooldown after a meal). No scheduler, work receiver,
production snapshot, native 1.5 package or installed 1.3 was changed by this preview.

## Historical native integration — 2026-09-07: approved standing default

The user explicitly approved the standing blink v1 after the light/dark, 596/160 px
review. Separate native preview 1.5/build 7 now uses the original standing loop for
working/observed idle/round-ended states and the open pose for waiting/failure/unknown
states. The real status card remains independent. Normal clicks blink in standing;
drag/release hold the standing image. Manual feeding plays the existing 4-second clip
once, then resolves the latest state back to standing. The reviewed seated annoyed art
and its 1.2-second lock remain, with existing failure/cooldown/reduced-motion rules.

The old continuous work-eating loop and automatic chewing pause are removed from this
preview. Autonomous idle meals are not enabled yet. Standing/seated reactions currently
switch directly between approved images; authored transitions and common foot placement
need a separate preview. The installed 1.3, receiver, tier policy and design registry
remain unchanged. The catalog below is still a specification, not a runtime inventory.

## Historical decision — 2026-09-07: eating as one idle activity

This section records why bounded idle eating was introduced. Its claim that eating was
only an idle activity is superseded by the 2026-09-19 decision above: workload eating
remains the working base, while the idle onigiri episode remains an additional action.

The user decided: “可以，我打算把灵梦吃饭喂食这一版本做成挂机动作之一”.
The existing reviewed onigiri/eating/feeding presentation becomes one activity
in Reimu's future idle repertoire. The selected natural standing pose with gentle
blinking is the intended default idle base.

- **Autonomous idle meal:** occasionally play a bounded eating episode during
  eligible idle time, then resolve the latest base state. Most idle time remains
  quiet standing. Frequency and episode length will be tuned in a dedicated preview.
- **Manual feeding:** retain the right-click feeding entry and the reviewed eating
  clip. Feeding can request the activity without waiting for the idle scheduler,
  subject to the existing input, failure, pause and reduced-motion rules.
- **Separate meaning from appearance:** eating may occur without an active task.
  Real work status continues to come from the observer and the task card. Starting
  or finishing a meal never changes task counts, invents work, or implies completion.
- **Preserve responsiveness:** no queued meal spam or repeated restart on status
  updates. Failure, drag and existing transient arbitration still apply. At the end,
  use the latest state, returning to standing only when that state calls for idle.
- **Reuse approved art:** preserve the current 40-frame eating clip, feeding and
  annoyed-reaction assets. Standing-to-seated placement and the return transition
  need a later visual preview; the present art does not establish a sit-down/stand-up
  animation or a shared anatomical layer rig.

This is an accepted design direction, not an installed behavior change. Native 1.3
retains its current work-driven eating until integration. The historical
`work_eating` / `eat_onigiri` mappings and tier restrictions below and in
`actions.json` describe the earlier workload/static-atlas design; they must not be
used to forbid idle eating in the new native design. No `ReimuFoodTier` formula,
event protocol, runtime registry or static atlas is changed by this decision.
Standing-blink visual approval and the staged art workflow remain as recorded in
the latest handoff.

This document turns Reimu from a static, task-count-driven table display into a character with observable personality. It defines the behavior architecture, the finite state machine, the full action catalog, and the boundary between what the current Codex pet contract can express and what belongs to a future extended runtime.

The machine-readable registry lives at [`pets/reimu/metadata/actions.json`](../pets/reimu/metadata/actions.json). It is a **project-internal behavior specification**, not a Codex manifest; the current Codex desktop app does not consume it.

## 1. Design principles

1. **Lazy at rest, instantly competent.** When nothing is happening Reimu is unhurried — tea, cloud watching, slouching at the table. When something actually happens she reacts fast and precisely. This contrast is the character; she must never read as a perpetually busy AI mascot.
2. **Alive, not busy.** Most scheduler ticks result in no action. More actions in the catalog must not mean more actions per minute.
3. **Two axes, not one.** `Workload State` (the `ReimuFoodTier`) decides the meal on the table and the overall eating mood. `Character Behavior` decides what she is concretely doing right now. Task count never selects an individual animation directly.
4. **More work means more food means happier Reimu.** The tier emotion progression is monotonic toward joy and is locked in section 8.
5. **Honest capability claims.** Everything here is design. Only the actions mapped to real Codex v2 rows can appear in a shipped static package; the rest wait for a supported runtime. Nothing in this document changes the `1536×2288`, 8×11, `192×208`, `spriteVersionNumber: 2` contract.

## 2. Behavior-architecture research

Open desktop-pet and Shimeji-style projects were surveyed for architecture only — no character, art, or code is reused. Surveyed: [Ice-teapop/desktop-pet](https://github.com/Ice-teapop/desktop-pet) (TypeScript/Electron, three-class FSM), [bestxiangest/clawd-buddy](https://github.com/bestxiangest/clawd-buddy) and its origin [rullerzhou-afk/clawd-on-desk](https://github.com/rullerzhou-afk/clawd-on-desk) (Electron pets that mirror coding-agent state), [kokoronoka/desktopPet](https://github.com/kokoronoka/desktopPet) (minimal Electron baseline), [He2y/desktop_pet](https://github.com/He2y/desktop_pet) (Swift/AppKit, dual autonomy profiles), [Shimeji-ee](https://github.com/gil/shimeji-ee) / [Shimeji-Desktop](https://github.com/DalekCraft2/Shimeji-Desktop) (Java, data-driven behavior graphs), [Adrianotiger/desktopPet](https://github.com/Adrianotiger/desktopPet) (eSheep revival, probability-edge animation XML), and [tonybaloney/vscode-pets](https://github.com/tonybaloney/vscode-pets) (per-state `possibleNextStates`).

Patterns adopted into this specification, with their strongest sources:

1. **Numeric priority ladder; lower requests are rejected** (Ice-teapop, clawd-buddy) → section 5.2.
2. **Three state classes — looping base, one-shot with explicit `returnTo`, locked transition bridge** (Ice-teapop's A/B/C classes; clawd-buddy's `ONESHOT_STATES` + auto-return) → section 5.1 and the registry's `returnTo` field.
3. **Transition locks with a single top-priority escape hatch** (Ice-teapop) → section 5.4.
4. **Minimum display time and dropped-not-queued lower-priority triggers to kill flicker and races** (clawd-buddy's `MIN_DISPLAY_MS` / pending-state queue) → section 5.4.
5. **Random-action scheduler armed only in a base state, with per-action cooldowns, a global interval, and a `canAutoplay()`-style guard** (Ice-teapop's 20–40 s idle-egg arming; clawd-buddy's day/night pool) → section 6.
6. **Weighted next-behavior selection kept in data, not engine code** (Shimeji `Frequency`/`Condition`, eSheep `<next probability>`, vscode-pets `possibleNextStates`) → `actions.json` as the tunable registry.
7. **Sleep as a chain of interruptible stages, with wake-watching active only inside the sleep family and a startled/wake bridge back** (clawd-buddy `yawning → dozing → sleeping`; clawd-on-desk startled wake) → section 5.5.
8. **Click-escalation ladder: click < double click < rapid-click flail** (clawd-buddy, Ice-teapop) → section 7.
9. **Drag as a mandatory forced state with a distinct grabbed pose and a landing transition** (Shimeji requires `Dragged`/`Thrown`/`Fall`; clawd-on-desk pointer capture) → `drag_float` / `drag_land`.
10. **Cursor-following as an overlay channel rather than a state transition** (clawd-buddy, Ice-teapop eye-tracking) → `look_cursor` as the single sanctioned overlay.
11. **Busy states suppress idle eggs but yield to alerts; stale external sessions expire so a dead source cannot freeze the pet** (clawd-on-desk 300–600 s staleness) → section 5.2 bands plus the existing degraded-fallback rule in the workload document.
12. **An explicit quiet-autonomy profile is valuable** (He2y's companion vs. work modes) → Reimu's default is intentionally closer to the quiet profile; see section 6.

Deliberately rejected: constant walking/wandering (kokoronoka-style random walks would contradict Reimu's temperament), throw physics and gravity chains (out of scope for a table-anchored pet), and per-few-seconds action frequency.

## 3. Character basis

The behavior vocabulary is grounded in first-party characterization, with canon, inferred, and fanon claims kept separate. Sources were located through en.touhouwiki.net's verbatim transcriptions of official omake/manual texts; each claim below names the underlying official work (see the register in [references.md](references.md)).

| Trait used in this design | Status | Official source |
| --- | --- | --- |
| Laid-back, carefree, no sense of crisis | **canon** | EoSD manual ("appears carefree… really is"); Perfect Memento in Strict Sense (非常に暢気, least crisis-aware Hakurei maiden); SWR official profile |
| 随遇而安 — takes things as they are | **canon** | PCB キャラ設定.txt 「すべては在るがままに、である」; IN manual (fits in anywhere immediately) |
| Tea as a daily ritual | **canon** | PCB character text (daily routine: gazing at the sky, drinking tea); IaMP 上海アリス通信 (tea on the veranda as her one shrine-maiden-like activity); 儚月抄 official site |
| Dislikes training, low everyday motivation | **canon** | HRtP–MS omake (修業不足); PCB manual (修行嫌い); Wild and Horned Hermit ch. 5–6 (official print) |
| Spaces out at the quiet shrine, pretends to clean | **canon** | PMiSS (lazes about, pretends to clean, drinks tea); PCB (参拝客は殆ど来ない) |
| Direct, un-two-faced emotions (表里如一) | **canon** | IaMP profile 「怒る時は怒り、笑う時は笑う。裏表のない性格…」 |
| Treats everyone equally | **canon** | IN キャラ設定.txt; repeated in MoF/SA omake |
| Sharp intuition and natural talent | **canon** | PoFV (solves incidents by intuition); PMiSS (鋭い勘); IaMP (natural sense strong enough to doubt she's human) |
| Instantly fast and serious when an incident occurs | **canon** | PoFV manual (rushes out to resolve incidents at once); PMiSS (her usual carefreeness vanishes and she immediately investigates) |
| Flight | **canon** | EoSD manual onward: 空を飛ぶ程度の能力 |
| Shrine-maiden duty: barrier, extermination, incident resolution | **canon** | PMiSS (Hakurei duty across generations); Forbidden Scrollery ch. 53 |
| Yin-yang orbs as her armament | **canon** | HRtP 靈異伝.TXT; EoSD/PCB manuals; WaHH (go-shintai of the Hakurei god) |
| Ofuda and gohei as tools | **canon** | HRtP omake onward (ofuda); Curiosities of Lotus Asia ch. 2 (gohei) |
| Sees no one as a true comrade / cold-hearted loner | **inferred** | IN キャラ設定.txt states it speculatively; not used in this design |
| Extreme poverty obsession, money-grubbing (见钱眼开) | **fanon exaggeration** | Canon basis is only that the shrine gets few visitors and donations (PCB, PMiSS footnote); the cackling money-mania register is flanderization and is excluded |
| "Armpit miko" jokes | **fanon** | Derived from the canon sleeveless design; no official work comments on it; excluded |
| Violent extermination on a whim | **mostly fanon** | PMiSS/PoFV give only a canon-adjacent basis; excluded |

Design consequences adopted here:

- Keep the exaggerated poverty / money-grubbing register out of the core loop; the shrine's quietness appears only as unhurried spare time.
- Tea, spacing out, minimal chores, and low motivation are the default texture; sharp competence appears the moment a real event fires.
- Flight replaces running; the shrine-maiden identity stays visible through the outfit, ofuda, gohei, and yin-yang orb in small doses.
- Emotions are direct and readable: brief frown when poked, open irritation when poked repeatedly, open joy over food.

## 4. The two-axis model

```text
VisualState = CharacterBehavior(FSM node) × ReimuFoodTier(0…5)
```

- `ReimuFoodTier = 0 | 1 | 2 | 3 | 4 | 5` stays exactly as defined in [workload-food-system.md](workload-food-system.md): tiers `0`–`4` are exact counts, `5` is the visual cap for five or more. No named bands, no ranges.
- The tier is a **parameter** of a behavior, not a behavior. `work_eating` at tier 1 and tier 5 is the same FSM node with a different table composition and expression overlay.
- Active work selects `work_eating` for tiers 1–5. Tier 0 is not a work loop: it selects the idle base and its autonomous pool. `idle_onigiri` may still play there as a bounded snack without inventing a task.
- Behaviors declare `foodTiers`, the tiers in which they may fire. Example: `idle_table_slouch` and `idle_sweep` exist only at tier 0; `happy_eat` only at tiers 3–5.
- When the tier changes, the FSM node does not reset; only the composition layer swaps (with the debounce already specified in the workload document).

## 5. Finite state machine

### 5.1 Node classes

- **Base states** — hold indefinitely; something is always one of these: `idle_relaxed`, `work_eating`, `wait_chin_hand`, `review_task_slip`, `fail_fumble`, plus the sleep-chain holds `doze_nod` and `sleep_table`.
- **Transient one-shots** — play once and return: all `idle_*` and `eat_*` actions, `react_*`, `greet_wave`, `jump_float`.
- **Transitions** — non-loop connectors with a fixed successor: `idle_yawn → doze_nod`, `wake_up → base`, `drag_land → base`, and the incident chain.
- **Held interaction loops** — active while an input condition persists: `drag_float`, `look_cursor`, `fly_low_left/right`.

### 5.2 Priority bands

Higher band always wins; equal band never preempts (first action finishes or is explicitly replaced by its own successor).

| Rank | Band | Members |
| ---: | --- | --- |
| 90 | `FAILED` | `fail_fumble` (Codex-reported failure) |
| 80 | `INCIDENT` | `incident_notice → incident_ready → incident_fly` (design only) |
| 70 | `REACTION` | `react_annoyed` > `react_poke` > `react_notice`; also `look_cursor`, `greet_wave`, `jump_float` |
| 60 | `DRAG` | `drag_float`, `drag_land`, `fly_low_left/right` |
| 50 | `REVIEW` | `review_task_slip` |
| 40 | `WORKING` | `work_eating`, `wait_chin_hand` |
| 30 | `AUTONOMOUS` | all `idle_*` one-shots, all `eat_*` beats |
| 20 | `SLEEP` | `idle_yawn`, `doze_nod`, `sleep_table`, `wake_up` |
| 10 | `IDLE` | `idle_relaxed` |

Implementation note: although `DRAG` sits below `REACTION` conceptually, a physical drag begins immediately regardless of what is playing — an interruptible action is cancelled, a non-interruptible one (`react_annoyed`, `wake_up`, incident beats) finishes its last committed frame first, then drag takes over. The band order matters for *resolution*, not for denying the user's pointer.

### 5.3 The base-state rule (`returnTo: "base"`)

Every transient action must know where it returns. The registry uses the sentinel `base`, defined as **the currently selected base state**, computed from Codex/workload status at the moment the transient ends — never unconditionally `idle_relaxed`.

```text
working → react_poke → (poke finishes) → working      ✓
working → react_poke → (poke finishes) → idle          ✗ forbidden
sleeping → click → wake_up → idle_relaxed              ✓ (waking clears the sleep chain)
```

If a transient ends and its recorded return node is no longer valid (state changed mid-action, or the node's `foodTiers` no longer allow it), fall back to the freshly computed base state. An unknown or corrupt node always resolves to `idle_relaxed` — that is the FSM's invalid-state fallback, and it must be logged, not silently absorbed.

### 5.4 Transition locks and race prevention

- Exactly one action owns the body at a time; there is no blending layer in Phase 1 (eyes-only `look_cursor` is the single sanctioned overlay, and it drops out while any non-interruptible action plays).
- A non-interruptible action (`react_annoyed`, `wake_up`, `drag_land`, incident beats) sets a transition lock: queued triggers of lower or equal band are dropped, not queued — repeated pokes during `react_annoyed` do not schedule five more warnings.
- Transitions with fixed successors (`idle_yawn`, incident beats) may not be re-entered while their chain is active.
- A tier change never interrupts an action; it only swaps the composition layer at the next loop boundary.

### 5.5 Sleep chain

```text
idle_relaxed → idle_yawn → doze_nod → sleep_table
sleep_table / doze_nod → wake_up → base
```

- Entry requires tier 0 and roughly five minutes without user interaction or Codex activity; `idle → sleeping` directly is forbidden.
- `doze_nod` holds ~75 s (head nods, catches herself) before deepening into `sleep_table`.
- Sleeping Reimu lies on the low table, tea cup still beside her, the red bow fully visible. No "Zzz" text, no floating UI symbols.
- Any interaction or Codex state change exits through `wake_up` (short, non-interruptible: blink, small stretch, recompose). Waking straight into `work_eating` is allowed and is itself a small "instantly competent" beat.

## 6. Autonomous scheduler

The scheduler decides what Reimu does *on her own* while a base state holds.

- **Global floor:** at least 20 s between any two autonomous one-shots; a random 20–45 s jitter is recommended so the rhythm never feels metronomic.
- **Doing nothing is the default:** each tick chooses "no action" with the highest weight.
- **Per-action cooldowns:** `idle_tea` ≥ 90 s, `idle_cloudwatch` ≥ 120 s, `idle_table_slouch` ≥ 180 s, `idle_ofuda_check` ≥ 240 s, `idle_sweep` and `idle_yinyang` ≥ 300 s.
- **Frequency shape at tier 0:** mostly `idle_relaxed`; occasionally tea / cloudwatch / slouch; rarely sweep / ofuda / yin-yang; after long inactivity, yawn → sleep.
- **Eating beats at tiers 1–5** run on the same scheduler inside `work_eating` (and tiered idle): `eat_onigiri` is the common beat; `eat_side_dish`, `eat_soup`, `drink_tea_meal`, `pause_chew`, `look_at_food` add variety; `happy_eat` only at tiers 3–5. `look_at_food` gets a temporary weight boost right after a tier increase — she notices the new dishes.
- `idle_sweep` must visibly fail to sustain motivation: two strokes, a pause, put the broom down, sit back. Shrine-maiden duty plus Reimu laziness in one beat.

## 7. Interaction design

| Input | Action | Character note |
| --- | --- | --- |
| hover | `look_cursor` | Eyes lead, head and bow follow subtly; the body and table never rotate. |
| single click | `react_notice` | Sudden awareness: one blink, slight head lift. |
| double click | `react_poke` | Small frown plus slight lean back — dry displeasure, not exaggerated anime shock. |
| ≥4 rapid clicks | `react_annoyed` | Openly impatient; raises an ofuda or gohei as a warning. Never attacks; returns to the current base state. |
| drag | `drag_float` | Independent caught/held pose: table and food disappear, feet leave the baseline, clothes and hair hang with restrained follow-through, and pointer motion adds at most a small lag/sway. Do not reuse voluntary flight art. |
| release | `drag_land` | Gentle settle back to the table edge; no bounce physics. |

## 8. Workload states and the locked emotion progression

Task count maps to `ReimuFoodTier` exactly as before (`min(activeTaskCount, 5)`); the tier selects a meal composition, never a food-item count. The emotional read is locked and monotonic on both axes — happiness and meal richness:

| Tier | Meal | Reimu |
| ---: | --- | --- |
| 0 | nearly empty table, tea anchor only | unhurried boredom: spacing out, chin in hand, tea, occasional chores |
| 1 | first compact meal, very restrained | **crying while eating** — the absurd relief of finally having work *and* food; tears fall while she eats earnestly |
| 2 | slightly richer than tier 1 | residual wetness at the eye corners, but visibly eating with more ease; clearly more positive than tier 1 |
| 3 | modestly richer again | openly content: no tears, focused eating, a small satisfied smile |
| 4 | a properly rich spread | clearly happy, more energetic bites; one small sweat cue allowed, but never fatigue or distress |
| 5 | maximum table-filling banquet | **laughing while crying** — overwhelmed that this much food exists, not overwhelmed by work |

Growth restraint: tier 1→2 and 2→3 are small steps in dish variety and occupied area; only tier 5 reads as a banquet. Tea and the held onigiri remain the recurring anchors at every eating tier.

## 9. Codex standard actions vs Reimu extended actions

### 9.1 Codex standard actions (implementable now, static v2 atlas)

| Codex row | Action | Notes |
| --- | --- | --- |
| `idle` (row 0) | `idle_relaxed` | The approved 6-frame pilot keeps the fixed seated pose and open eyes; only the image-left loose hair curl settles by 1–2 px and returns. Frame 0 is the reduced-motion still. Blink, breathing and the earlier tea-sip idea remain future design options, not current pixels. |
| `running-right` (1) | `fly_low_right` | Low-altitude flight, sleeves back, bow readable. |
| `running-left` (2) | `fly_low_left` | Mirror only if bow/sleeve/prop handedness survives. |
| `waving` (3) | `greet_wave` | One controlled hand raise. |
| `jumping` (4) | `jump_float` | Brief float-up; optional yin-yang orb touch. |
| `failed` (5) | `fail_fumble` | Comic mishap; no red X, question marks, text, or floating icons. |
| `waiting` (6) | `wait_chin_hand` | The approved current row keeps the fixed seated eating pose and open eyes; only the image-right eyebrow rises 1–3px and returns as an attentive cue. The chin-in-hand pose and eye-flick remain future design-layer options. |
| `running` (7) | `work_eating` (+ `eat_onigiri` beat) | Tier-appropriate eating beat; task metadata remains in the external card. Never typing. |
| `review` (8) | `review_task_slip` | The approved current row keeps the fixed seated eating pose and open eyes; only the complete image-right eyebrow lowers uniformly by 1–2px and returns as a focused cue. The original brow is fully cleared, avoiding the rejected double-line artifact. Task-slip reading and nod remain future design-layer options. |
| look rows (9–10) | `look_cursor` | 16 clockwise directions; eyes lead. |

The static atlas carries exactly one appearance per row; multiple idle behaviors are compressed into the composed idle sequence. The sheet cannot switch food tiers live — tier variants remain design-layer source compositions until a supported runtime exists.

### 9.2 Reimu extended actions (design layer, future runtime)

Everything else in the catalog: the standalone idle one-shots (`idle_cloudwatch`, `idle_table_slouch`, `idle_sweep`, `idle_ofuda_check`, `idle_yinyang`), the sleep chain, the click/poke reactions, `drag_float`/`drag_land` as distinct grabbed states, the incident chain, and the differentiated eating beats. They require a runtime adapter, an extended pet shell, or a future pet API that can drive per-action playback. **The current Codex custom pet API cannot invoke these actions, and this repository must not claim otherwise.**

The incident chain additionally requires a *reliable* urgent event source (error burst, agent failure). No such hook exists today; the chain is specified so the design is ready, and it stays `design-only` in the registry until a supported trigger is documented and tested.

## 10. Action catalog

Full field-level definitions (trigger, tiers, duration, interruptibility, priority, fallback, mappings, props, expression, status) live in [`pets/reimu/metadata/actions.json`](../pets/reimu/metadata/actions.json). Summary:

| `action_id` | 中文 | Category | Loop | Tiers | Codex row | Status |
| --- | --- | --- | :---: | --- | --- | --- |
| `idle_relaxed` | 放松坐姿 | base | ✓ | 0–5 | `idle` | specified |
| `idle_tea` | 喝茶 | autonomous | – | 0–5 | folded into `idle` | specified |
| `idle_onigiri` | 挂机吃饭团 | autonomous | – | 0 | — | specified |
| `idle_cloudwatch` | 看天发呆 | autonomous | – | 0–2 | — | specified |
| `idle_table_slouch` | 趴桌撑脸 | autonomous | ✓ | 0 | — | specified |
| `idle_sweep` | 扫地（很快放弃） | autonomous | – | 0 | — | specified |
| `idle_ofuda_check` | 看御札 | autonomous | – | 0 | — | specified |
| `idle_yinyang` | 阴阳玉小动作 | autonomous | – | 0 | — | specified |
| `idle_yawn` | 打哈欠 | sleep-chain | – | 0 | — | specified |
| `doze_nod` | 打瞌睡 | sleep-chain | ✓ | 0 | — | specified |
| `sleep_table` | 趴桌睡着 | sleep-chain | ✓ | 0 | — | specified |
| `wake_up` | 醒来 | sleep-chain | – | 0 | — | specified |
| `look_cursor` | 视线跟随鼠标 | interaction | ✓ | 0–5 | look rows | specified |
| `react_notice` | 注意到用户 | interaction | – | 0–5 | — | specified |
| `react_poke` | 被戳 | interaction | – | 0–5 | — | specified |
| `react_annoyed` | 不耐烦警告 | interaction | – | 0–5 | — | specified |
| `drag_float` | 被抓取悬浮 | interaction | ✓ | 0–5 | — | specified |
| `drag_land` | 落地 | interaction | – | 0–5 | — | specified |
| `feed_onigiri` | 主动喂饭团 | interaction | – | 0–5 | — | specified |
| `incident_notice` | 察觉异变 | incident | – | 0–5 | — | design-only |
| `incident_ready` | 起身备战 | incident | – | 0–5 | — | design-only |
| `incident_fly` | 低空飞离 | incident | – | 0–5 | — | design-only |
| `work_eating` | 边吃边处理任务 | codex-state | ✓ | 1–5 | `running` | specified |
| `wait_chin_hand` | 托脸等输入 | codex-state | ✓ | 0–5 | `waiting` | specified |
| `review_task_slip` | 检查完成的任务 | codex-state | ✓ | 0–5 | `review` | specified |
| `fail_fumble` | 小失误 | codex-state | ✓ | 0–5 | `failed` | specified |
| `greet_wave` | 打招呼 | codex-state | – | 0–5 | `waving` | specified |
| `jump_float` | 短浮空 | codex-state | – | 0–5 | `jumping` | specified |
| `fly_low_right` | 低空飞行（右） | codex-state | ✓ | 0–5 | `running-right` | specified |
| `fly_low_left` | 低空飞行（左） | codex-state | ✓ | 0–5 | `running-left` | specified |
| `eat_onigiri` | 咬饭团 | eating | – | 1–5 | beat in `running` | specified |
| `eat_side_dish` | 吃小菜 | eating | – | 2–5 | — | specified |
| `eat_soup` | 喝味噌汤 | eating | – | 2–5 | — | specified |
| `drink_tea_meal` | 餐间喝茶 | eating | – | 1–5 | — | specified |
| `pause_chew` | 停下咀嚼 | eating | – | 1–5 | — | specified |
| `look_at_food` | 端详食物 | eating | – | 1–5 | — | specified |
| `happy_eat` | 开心猛吃 | eating | – | 3–5 | — | specified |

## 11. Sprite-economy strategy

The eating vocabulary must not multiply sprite production by six tiers:

- one shared body construction and arm cycle serves `eat_onigiri`, `eat_side_dish`, and (with a two-hand variant) `eat_soup` / `drink_tea_meal`;
- tier identity comes from the **table composition layer** and a small set of expression differences (tears at 1, drying at 2, smile at 3, energy at 4, laughing tears at 5);
- `pause_chew` and `look_at_food` are deliberately cheap filler beats that add life without new poses.

The goal is a reusable animation vocabulary, not six independent animation sets.

## 12. Final design checklist

1. Tier 0 Reimu reads as genuinely unhurried (tea, spacing out, slouch, half-hearted chores). ✓
2. Tea recurs at every tier as the anchor ritual. ✓
3. The lazy-at-rest / instantly-competent contrast exists (sleep chain and idle texture vs. `wake_up` straight into work and the incident chain). ✓
4. Locomotion is low-altitude flight, never running legs. ✓
5. Click / poke / drag reactions are Reimu-specific (dry frown, ofuda warning, self-possessed floating), not generic anime-girl reactions. ✓
6–10. Tier emotions are locked monotonic: crying-eating at 1, easing at 2, content at 3, happy at 4, laughing-crying at 5 — never work-collapse. ✓
11–12. Food grows in composition richness, restrained at low tiers, banquet only at 5; item count ≠ task count. ✓
13. Canon vs. fanon is separated in section 3. ✓
14. Codex standard vs. extended runtime actions are separated in section 9. ✓
15. No official or community assets are copied; references are recorded as links and study notes only. ✓
16. The v2 atlas contract (1536×2288, 8×11, 192×208, `spriteVersionNumber: 2`) is untouched. ✓
