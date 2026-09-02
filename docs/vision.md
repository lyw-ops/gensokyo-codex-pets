# Project vision

## Purpose

Gensokyo Codex Pets should make Codex activity readable and charming through original Touhou-inspired desktop companions. The pets are small status instruments first and character performances second: their poses must communicate what Codex is doing without losing the quiet humor of everyday Gensokyo.

## Creative principles

### Recognizable, controlled character design

Each pet should be identifiable through silhouette, palette, costume, and a deliberately authored chibi face system. Avoid generic AI-anime rendering, excess facial detail, inconsistent proportions, and identity drift between frames.

### Cozy work, not combat spectacle

Food, tea, low tables, small chores, and understated reactions are the core vocabulary. Touhou Mystia's Izakaya is an atmosphere reference for cozy Gensokyo life, not an asset source or a template to clone.

### Behavior belongs to the character

Codex's standard states should receive character-specific performances. Reimu may sip tea while idle, eat while working, look expectantly toward the user when input is needed, and drop an onigiri after failure. Locomotion should feel like low-altitude Touhou flight when that remains readable in the fixed directional rows.

### Evidence before integration claims

The project should distinguish ideas from supported behavior. Workload-reactive food is a design goal, but the current static pet package does not receive task counts. A future integration must use a documented or responsibly inspected interface and must degrade safely when activity data is unavailable.

## Layer model

```text
Codex activity source
        ↓
WorkloadSnapshot → configurable WorkloadPolicy → WorkloadLevel
                                                   ↓
                                      compatibility/runtime adapter
                                                   ↓
                               original Reimu visual asset variants
```

The visual asset layer must remain useful even if the workload adapter changes. The compatibility layer owns atlas and manifest rules. The dynamic layer owns task counting, filtering, thresholds, hysteresis, and fallbacks.

## Character roadmap

Phase 1 is Hakurei Reimu. Possible later characters include Kirisame Marisa, Izayoi Sakuya, Konpaku Youmu, Cirno, Remilia Scarlet, Flandre Scarlet, and Komeiji Koishi. Later additions should reuse the compatibility pipeline while defining their own state performances and workload motifs.

## Milestone 0 success

Milestone 0 succeeds when the repository is connected but not pushed, the current pet contract is documented with evidence levels, Reimu's design constraints and workload model are reviewable, and the next art step can begin without inventing technical capabilities or copying protected assets.
