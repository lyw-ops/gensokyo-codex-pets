# Gensokyo Codex Pets

Gensokyo Codex Pets is a fan-made collection of Touhou Project desktop pets for OpenAI Codex and compatible ChatGPT interfaces. The project explores small, character-specific animations that make task activity feel like everyday life in Gensokyo.

Phase 1 focuses only on Hakurei Reimu / 博丽灵梦. Later phases may add Marisa, Sakuya, Youmu, Cirno, Remilia, Flandre, Koishi, and other characters, but only after the Reimu pipeline and compatibility contract are stable.

## The Reimu idea

Reimu sits at a low table and snacks while Codex works. Her food should eventually respond to workload:

- calm work means an onigiri and tea;
- normal work adds another onigiri, soup, and a side dish;
- busy work fills the table with skewers and snacks;
- overloaded work becomes a cute, absurd feast while Reimu tearfully keeps eating.

The character art will use an original, manually controlled chibi system. Recognizability comes from Reimu's black hair, large red bow, red-and-white shrine maiden outfit, clean proportions, and economical expressions—not from a generic highly rendered anime face.

## Current status

**Early prototype / research stage.** Milestone 0 contains format research and production specifications only. It deliberately contains no final sprites, no extracted game assets, and no simulated workload integration.

The current Codex desktop app supports a local v2 pet atlas with 8 columns, 11 rows, 192×208 pixel cells, and a 1536×2288 final image. The public web-upload documentation currently describes a separate 1536×1872 sheet. See [the format research](docs/codex-pet-format.md) before making assets.

## Architecture

The project keeps three concerns separate:

1. **Visual asset layer** — original character art, palettes, poses, and animation frames.
2. **Codex compatibility layer** — atlas assembly, manifest generation, validation, and installation.
3. **Dynamic workload layer** — a future adapter that converts supported Codex activity data into configurable `WorkloadLevel` values.

A fixed sprite sheet must not be presented as live workload integration. Current findings show that a custom pet receives app-selected animation states, but its manifest has no task-count or custom state-logic hook.

## Repository map

```text
docs/                 Project vision, format research, design, references, and roadmap
pets/reimu/           Reimu-specific design, future sprites, and metadata examples
scripts/              Deterministic project checks and future build scripts
tools/                Future compatibility and workload adapter tooling
```

Start with [the project vision](docs/vision.md), [Reimu's design brief](docs/reimu-design.md), and [the workload/food model](docs/workload-food-system.md).

## GPT handoff

[`HANDOFF.md`](HANDOFF.md) is the canonical project handoff for both GPT and human maintainers. It records the current milestone, decisions, open questions, validation status, and next actions. Every repository update must refresh the handoff in the same commit and be pushed to GitHub so a new GPT can resume from the remote state.

## Fan-work notice

This is an unofficial Touhou Project fan work. It is not affiliated with or endorsed by Team Shanghai Alice, ZUN, OpenAI, or the creators and publishers of referenced Touhou fan games. Project assets are intended to be original fan-made work; commercial sprites and third-party fan art must not be extracted, copied, or redistributed here. See [LICENSE-or-NOTICE.md](LICENSE-or-NOTICE.md).
