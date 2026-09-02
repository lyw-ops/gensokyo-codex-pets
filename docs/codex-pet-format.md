# Codex pet format research

Research date: **2026-09-02**

Locally inspected desktop app: **ChatGPT/Codex 26.831.21537 (build 7579), macOS**

This document separates public product documentation, OpenAI-bundled local specifications, and implementation observations. No community repository was needed for these findings.

## Evidence classes

### OFFICIAL — public documentation

The current [OpenAI Pets documentation](https://learn.chatgpt.com/docs/pets) states that:

- desktop pets can follow activity across chats;
- the user-facing states are **Running**, **Needs input**, **Ready**, and **Blocked**;
- multiple-chat priority is Needs input, then Blocked, Ready, and Running;
- desktop-created custom pets are stored locally and do not automatically sync to the web;
- reduced-motion mode shows a still frame;
- web upload currently requires a transparent PNG or WebP exactly 1536×1872 and no larger than 20 MiB;
- terminal pets use the same four activity meanings for the current CLI session.

The public page does not document cell size, row order, metadata, a v2 atlas, or custom workload hooks.

### OFFICIAL — bundled with the desktop app

The installed app ships an OpenAI `hatch-pet` skill and `Codex V2 Pet Contract` under:

```text
/Applications/ChatGPT.app/Contents/Resources/skills/skills/.curated/hatch-pet/
```

That bundled contract defines the local v2 atlas, animation rows, manifest, installation directory, and validation workflow summarized below. It is versioned with the installed app and should be rechecked after app upgrades.

### LOCAL IMPLEMENTATION OBSERVATION — shipped app inspection

Read-only inspection of the shipped app bundle confirms that the current client accepts manifest versions 1 and 2, defaults an omitted version to 1, validates dimensions by version, hard-codes the row timing table, and passes a resolved animation state to the sprite renderer. These observations are useful for design but are not a promised public API.

## Supported atlas versions

| Version | Dimensions | Grid | Cell | Current interpretation |
| --- | ---: | ---: | ---: | --- |
| v1 | 1536×1872 | 8×9 | 192×208 | Default when `spriteVersionNumber` is absent; matches the size currently documented for web upload. |
| v2 | 1536×2288 | 8×11 | 192×208 | Current local desktop target; adds two rows containing 16 look directions. Requires `spriteVersionNumber: 2`. |

Both formats use transparent PNG or WebP. For a new local pet, package v2. Do not package the 1536×1872 intermediate produced while assembling v2.

The public web documentation only promises the 1536×1872 upload shape. Although the shipped client can recognize cloud pet images with v1 or v2 dimensions, v2 server-side upload acceptance is not publicly documented and remains **unverified**.

## V2 row and frame order

| Row | Internal state | Used columns | Frame timing |
| ---: | --- | ---: | --- |
| 0 | `idle` | 0–5 | 280, 110, 110, 140, 140, 320 ms |
| 1 | `running-right` | 0–7 | 120 ms each; last 220 ms |
| 2 | `running-left` | 0–7 | 120 ms each; last 220 ms |
| 3 | `waving` | 0–3 | 140 ms each; last 280 ms |
| 4 | `jumping` | 0–4 | 140 ms each; last 280 ms |
| 5 | `failed` | 0–7 | 140 ms each; last 240 ms |
| 6 | `waiting` | 0–5 | 150 ms each; last 260 ms |
| 7 | `running` | 0–5 | 120 ms each; last 220 ms |
| 8 | `review` | 0–5 | 150 ms each; last 280 ms |
| 9 | look A | 0–7 | 000°, 022.5°, 045°, 067.5°, 090°, 112.5°, 135°, 157.5° |
| 10 | look B | 0–7 | 180°, 202.5°, 225°, 247.5°, 270°, 292.5°, 315°, 337.5° |

Unused cells in rows 0–8 must be fully transparent. All cells in rows 9–10 are used. Angles advance clockwise: 000° means up, 090° right, 180° down, and 270° left. Neutral/front is not a directional cell; the pointer deadzone falls back to idle.

## How the app selects animation

| App condition | Pet state/row |
| --- | --- |
| No actionable or unread activity | `idle` |
| Chat actively working | `running` |
| Approval, answer, user input, or plan implementation needed | `waiting` |
| Failed/system-error task; cancelled remote task | `failed` |
| Completed activity is unread | `review` |
| Pet is first awakened | `waving` |
| Hover interaction where enabled | `jumping` |
| User drags right or left | `running-right` / `running-left` |
| Pointer direction with a v2 pet | rows 9–10 |

For non-idle status rows, the current renderer plays the state animation three times and then settles into a slowed idle loop while that state remains selected. With reduced motion enabled, it uses a single frame. These are implementation observations and may change.

The semantic distinction matters for Reimu: `waiting` means the user must act, while `review` means finished output is ready to inspect. It should not be designed as generic passive waiting.

## Local package and metadata

A local custom pet package is placed at:

```text
${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>/
├── pet.json
└── spritesheet.webp
```

The v2 manifest shape is:

```json
{
  "id": "reimu",
  "displayName": "Hakurei Reimu",
  "description": "A shrine maiden who snacks her way through the task queue.",
  "spriteVersionNumber": 2,
  "spritesheetPath": "spritesheet.webp"
}
```

The installed app tolerates an omitted `id` and derives the runtime custom ID from the directory, but this project should include an explicit stable ID. `spritesheetPath` must resolve inside the pet directory. Omitting `spriteVersionNumber` selects v1 and causes a 2288-pixel-tall v2 sheet to be rejected.

After local installation, use Settings → Pets → Refresh and select the pet. The public docs also describe Settings → Pets → Create your own pet, which installs the bundled generation skill and opens a new task.

## Workload and custom-state integration verdict

**What is available to the app:** the desktop client knows per-chat activity, attention/unread state, an activity-tray count, and some live tool activity details. It uses those data to choose one of its built-in pet states and to render the tray or badge.

**What is available to a custom pet package:** a static manifest and sprite sheet. The current manifest schema has no script, event, task-count, workflow-count, agent-count, state alias, or configurable animation mapping field. The sprite renderer receives the app-selected state, optional look frame, source image, and interaction state; the notification/task count is not passed into sprite selection.

| Requested signal | Evidence in the current app | Exposed to custom pet assets? |
| --- | --- | --- |
| Active chats/tasks | The app derives active/running status per chat and can group multiple activity items. | **No count.** Only the selected standard state reaches sprite selection. |
| Workflows / scheduled work | The wider app tracks scheduled and long-running work, but the pet manifest defines no workflow field or event. | **No.** No distinct workflow animation or workload input is exposed. |
| Concurrent tasks | The activity tray and badge can show multiple items. | **No count.** Multiplicity affects UI presentation and priority, not a custom atlas row. |
| Concurrent subagents | The app can render subagent activity inside task history. No subagent-count input appears in the pet manifest or sprite renderer. | **No.** It is not a distinct pet state or parameter. |
| Concurrent tools | Live status text can derive an active-tool count. | **No.** That count is used for status text, not sprite selection. |
| Working / waiting / review / blocked | App task conditions resolve to `running`, `waiting`, `review`, or `failed`. | **Yes, coarsely.** The app chooses the corresponding fixed row; custom logic cannot redefine the transition. |

Therefore:

- a custom sheet can reinterpret the standard rows visually;
- it cannot natively select calm/normal/busy/overloaded food variants from active-task count;
- concurrent subagents and workflows do not receive a distinct custom animation row;
- claiming that the current Reimu package reacts to exact task counts would be false.

A future dynamic layer would need a supported external activity source and an adapter that switches a package, composes an allowed variant, or uses a future pet API. That work should begin only after the interface and lifecycle are documented. See [workload-food-system.md](workload-food-system.md).

## Validation checklist for future sprites

- Final local v2 atlas is exactly 1536×2288.
- Grid is 8×11 with 192×208 cells.
- Used frame counts match the table; unused standard cells are fully transparent.
- Rows 9–10 form one coherent clockwise 16-direction family.
- `pet.json` declares `spriteVersionNumber: 2`.
- PNG/WebP alpha is clean; no opaque background, detached artifacts, or accidental interior holes.
- Row 0, column 0 works as a reduced-motion still.
- Motion reads clearly at actual pet size, not only in a zoomed contact sheet.

## Open questions to recheck

1. Will public web upload formally document or accept v2 sheets?
2. Will OpenAI expose a stable pet event or activity-count API?
3. Can a supported extension map task/workflow counts to asset variants without replacing local package files at runtime?
4. How do terminal renderers use v2 look rows on terminals without pointer-driven overlay behavior?

Re-run this research after significant Codex desktop updates or before shipping an installable pet.
