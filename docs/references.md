# Reference register

No reference images are stored in this repository at Milestone 0. Links and notes are for study only and do not grant permission to copy or redistribute artwork.

Every future entry should record: title, publisher/creator, official or licensed status, URL, access date, traits studied, redistribution status, and whether the source influenced a committed asset.

## Touhou Project character references

### Official

- [Touhou Project fan-creator guidelines — Japanese](https://touhou-project.news/guideline/): current policy reference; check again before distribution.
- [Touhou Project fan-creator guidelines — English](https://touhou-project.news/guidelines_en/): official English guidance; the Japanese page has a newer listed update date.
- [Touhou Project 25th anniversary character page](https://touhou-x.jp/character/): high-level official/authorized character index. Use for identity study only; do not download or reproduce its images.

### Reimu study checklist

Use official game portraits or authorized character pages only to verify broad invariants: black hair, red bow, red-and-white shrine maiden clothing, detached sleeves, silhouette, and recurring accessories. Record the exact title and page before use. Do not extract game files.

## Officially licensed chibi Reimu references

No licensed chibi reference has been approved yet. Candidate products must be audited individually for publisher, license/authorization status, source URL, and permitted use.

Study only high-level construction choices such as:

- head-to-body ratio;
- bow size relative to the head;
- costume simplification at small scale;
- placement of eyes and mouth;
- how detached sleeves survive silhouette reduction.

Do not copy a licensed product's face grid, pose, sprite pixels, shading pattern, or costume simplification one-for-one.

## Touhou Mystia's Izakaya atmosphere and food references

Reference categories: low tables, tea service, rice balls, skewers, soup bowls, small dishes, food abundance, and cozy everyday humor.

No screenshots or extracted assets are committed. Before adding a link, prefer an official storefront, publisher, or developer page and record which atmosphere-level idea was studied. The Reimu scene must use an original layout, palette, prop drawings, and animation.

## User-provided GPT visual prototypes

### Reimu food-tier composition set

| Field | Record |
| --- | --- |
| Title | Reimu `0 tasks` through `5 tasks` food-tier composition set (six images) |
| Creator/tool | Maintainer-directed generation with ChatGPT Image |
| Status | User-provided AI-generated concept art; unofficial and not a canonical Touhou reference |
| Source | Local files supplied by the maintainer outside the repository; no public URL |
| Access date | 2026-09-02 |
| Traits studied | Tea-only tier `0`; transition to eating at tier `1`; increasing meal scale, dish variety, and table occupancy; recurring held onigiri and tea; maximum-tier comic tears; warm shrine-room mood |
| Redistribution | Maintainer authorized internal design-reference use. Original files remain outside the repository and are not approved here for redistribution. |
| Influence on committed work | Yes—composition hierarchy and tier descriptions in `docs/reimu-design.md`, `docs/workload-food-system.md`, and `pets/reimu/design/visual-spec.md` |

All six prototypes are 1448×1086 opaque RGB PNGs with full room backgrounds and embedded task-count signs. They are neither sprite sources nor model sheets. Do not commit, trace, crop, downscale, palette-sample, or reuse pixels from them. The final art must independently reconstruct the approved high-level composition at the 96×104 logical-grid candidate size and satisfy the transparent 192×208 cell contract.

## Codex pet format references

### OFFICIAL — public

- [OpenAI Pets documentation](https://learn.chatgpt.com/docs/pets): supported interfaces, public activity meanings, desktop workflow, reduced motion, CLI notes, and the current web-upload requirement.

### OFFICIAL — bundled local contract

The inspected ChatGPT/Codex macOS app version 26.831.21537 ships:

```text
/Applications/ChatGPT.app/Contents/Resources/skills/skills/.curated/hatch-pet/SKILL.md
/Applications/ChatGPT.app/Contents/Resources/skills/skills/.curated/hatch-pet/references/codex-pet-contract.md
/Applications/ChatGPT.app/Contents/Resources/skills/skills/.curated/hatch-pet/references/animation-rows.md
```

These files define local v2 packaging and animation details. They are installation evidence, not files to copy into this repository.

### COMMUNITY / REVERSE-ENGINEERED

No community repository was used for Milestone 0. If one is added later, label every finding as community/reverse-engineered and verify it against the current app before relying on it.
