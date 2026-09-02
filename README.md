# Gensokyo Codex Pets

Gensokyo Codex Pets is a fan-made collection of Touhou Project desktop pets for OpenAI Codex and compatible ChatGPT interfaces. The project explores small, character-specific animations that make task activity feel like everyday life in Gensokyo.

Phase 1 focuses only on Hakurei Reimu / 博丽灵梦. Later phases may add Marisa, Sakuya, Youmu, Cirno, Remilia, Flandre, Koishi, and other characters, but only after the Reimu pipeline and compatibility contract are stable.

## The Reimu idea

Reimu sits at a low table and snacks while Codex works. Her proposed food display is a direct, capped visualization of active tasks:

- tier `0` means no active tasks and uses a nearly empty, tea-only table;
- tiers `1` through `4` mean exactly one through four active tasks and use progressively richer meal compositions;
- tier `5` is the maximum table-filling feast and represents five or more active tasks.

The six visual tiers are identified by number, not by broad workload labels. The tier number selects an overall composition; it is not a requirement to show the same number of onigiri or dishes. Tea provides a recurring anchor, food variety and table occupancy rise with the tier, and the highest tier becomes a cute, tearful banquet.

The character art will use an original, manually controlled chibi system. Recognizability comes from Reimu's black hair, large red bow, red-and-white shrine maiden outfit, clean proportions, and economical expressions—not from a generic highly rendered anime face.

## Current status

**Static visual prototype stage.** The maintainer-approved **Eating Set v1** concept sheet is committed under `docs/reference/reimu/eating_set_v1/`, its six derived runtime sprites live under `assets/reimu/eating/`, and a dependency-free static preview app under `app/` switches states from a debug task count (see `app/README.md`). There is still no animation, no installable Codex pet package, and no real workload integration; the preview's task count is a manual debug input.

The current Codex desktop app supports a local v2 pet atlas with 8 columns, 11 rows, 192×208 pixel cells, and a 1536×2288 final image. The public web-upload documentation currently describes a separate 1536×1872 sheet. See [the format research](docs/codex-pet-format.md) before making assets.

## Architecture

The project keeps three concerns separate:

1. **Visual asset layer** — original character art, palettes, poses, and animation frames.
2. **Codex compatibility layer** — atlas assembly, manifest generation, validation, and installation.
3. **Dynamic workload layer** — a future adapter that converts a supported active-task count into `ReimuFoodTier = 0 | 1 | 2 | 3 | 4 | 5`.

A fixed sprite sheet must not be presented as live workload integration. Current findings show that a custom pet receives app-selected animation states, but its manifest has no task-count or custom state-logic hook.

## Repository map

```text
app/                  Static state-switching preview app (debug task provider)
assets/reimu/eating/  Eating Set v1 runtime sprites (one state directory each)
docs/                 Project vision, format research, design, references, and roadmap
docs/reference/       Approved concept/reference art (never loaded at runtime)
pets/reimu/           Reimu-specific design, future Codex atlas sprites, and metadata examples
scripts/              Deterministic project checks and future build scripts
tools/                Asset derivation and future compatibility/workload tooling
```

Start with [the project vision](docs/vision.md), [Reimu's design brief](docs/reimu-design.md), and [the workload/food model](docs/workload-food-system.md).

## GPT handoff

[`HANDOFF.md`](HANDOFF.md) is the canonical project handoff for both GPT and human maintainers. It records the current milestone, decisions, open questions, validation status, and next actions. Every repository update must refresh the handoff in the same commit and be pushed to GitHub so a new GPT can resume from the remote state.

## Fan-work notice

This is an unofficial Touhou Project fan work. It is not affiliated with or endorsed by Team Shanghai Alice, ZUN, OpenAI, or the creators and publishers of referenced Touhou fan games. Project assets are intended to be original fan-made work; commercial sprites and third-party fan art must not be extracted, copied, or redistributed here. See [LICENSE-or-NOTICE.md](LICENSE-or-NOTICE.md).
