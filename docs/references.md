# Reference register

No reference images are stored in this repository at Milestone 0. Links and notes are for study only and do not grant permission to copy or redistribute artwork.

Every future entry should record: title, publisher/creator, official or licensed status, URL, access date, traits studied, redistribution status, and whether the source influenced a committed asset.

## Touhou Project character references

### Official

- [Touhou Project fan-creator guidelines — Japanese](https://touhou-project.news/guideline/): current policy reference; check again before distribution.
- [Touhou Project fan-creator guidelines — English](https://touhou-project.news/guidelines_en/): official English guidance; the Japanese page has a newer listed update date.
- [Touhou Project 25th anniversary character page](https://touhou-x.jp/character/): high-level official/authorized character index. Use for identity study only; do not download or reproduce its images.

### Reimu first-party characterization study (2026-09-02)

| Field | Record |
| --- | --- |
| Title | Reimu canon-characterization audit for the action system |
| Locator used | [en.touhouwiki.net/wiki/Reimu_Hakurei](https://en.touhouwiki.net/wiki/Reimu_Hakurei) and [PMiSS Reimu article](https://en.touhouwiki.net/wiki/Perfect_Memento_in_Strict_Sense/Reimu_Hakurei), which reproduce the original Japanese official texts verbatim; thwiki.cc was unreachable (WAF) and not consulted |
| Underlying official works cited | PC-98 omake texts (靈異伝.TXT, 封魔録.txt, 夢時空.txt, 幻想郷.txt, 怪綺談.txt); EoSD manual and おまけ.txt; PCB manual and キャラ設定.txt; IaMP 上海アリス通信.txt; IN manual and キャラ設定.txt; PoFV texts; MoF/SA omake; SWR and 儚月抄 official sites; Perfect Memento in Strict Sense; Symposium of Post-mysticism Part 6; Strange Creators of Outer World Vol. 1; Wild and Horned Hermit; Forbidden Scrollery; Curiosities of Lotus Asia |
| Traits studied | Laid-back temperament, tea ritual, dislike of training, spacing out at the shrine, direct emotions, equal treatment of all, intuition, incident responsiveness, flight, shrine-maiden duty, yin-yang orb / ofuda / gohei armament |
| Canon/fanon separation | Recorded in `docs/reimu-action-system.md` section 3; poverty-mania, armpit jokes, and whimsical violence are marked fanon/flanderization and excluded |
| Redistribution | Text study only; no images downloaded or committed |
| Influence on committed work | Yes — the character-basis table and behavior selection in `docs/reimu-action-system.md` |

### Desktop-pet behavior-architecture study (2026-09-02)

Architecture-only survey; no character, art, or code reused. Projects: [Ice-teapop/desktop-pet](https://github.com/Ice-teapop/desktop-pet), [bestxiangest/clawd-buddy](https://github.com/bestxiangest/clawd-buddy), [rullerzhou-afk/clawd-on-desk](https://github.com/rullerzhou-afk/clawd-on-desk), [kokoronoka/desktopPet](https://github.com/kokoronoka/desktopPet), [He2y/desktop_pet](https://github.com/He2y/desktop_pet), [gil/shimeji-ee](https://github.com/gil/shimeji-ee), [DalekCraft2/Shimeji-Desktop](https://github.com/DalekCraft2/Shimeji-Desktop), [Adrianotiger/desktopPet](https://github.com/Adrianotiger/desktopPet), [tonybaloney/vscode-pets](https://github.com/tonybaloney/vscode-pets). Lessons adopted (priority ladder, state classes with explicit returns, transition locks, autonomous scheduling with cooldowns, sleep chains, click escalation, drag as a forced state, cursor-following as an overlay) are recorded in `docs/reimu-action-system.md` section 2.

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
