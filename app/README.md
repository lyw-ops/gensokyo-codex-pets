# Static state-switching preview app

A dependency-free static preview for the Reimu Eating Set v1 runtime sprites. It is the current development harness for the visual state system; it is **not** a Codex pet package and does not observe real task activity.

## Run

Serve the repository root over HTTP (ES modules do not load over `file://` in all browsers):

```bash
python3 -m http.server 8123
```

Then open <http://localhost:8123/app/>.

## What it does

- Renders one static sprite per eating state from `assets/reimu/eating/<state>/base.png`.
- Maps a debug task count to a state through the single policy boundary in [`task-state-mapping.js`](task-state-mapping.js): `0 → idle`, `1..4 → task_1..task_4`, `>= 5 → task_5`, negative or invalid → `idle`.
- Debug task provider: buttons (`-1, 0, 1, 2, 3, 4, 5, 6, 10`), a free number input, keyboard keys `0–9` and `↑`/`↓`, and a `?tasks=N` URL parameter.
- QA controls: display size (160 px "pet size" up to 596 px native) and background (checker / desktop / dark) to inspect transparency and readability.

## Structure

- [`characters.js`](characters.js) — Character → StateSet → State → frames registry. Adding a character or a multi-frame animation extends this file; the renderer already treats `frames` as a list.
- [`task-state-mapping.js`](task-state-mapping.js) — the only place that converts a task count into a state id.
- [`main.js`](main.js) / [`index.html`](index.html) — preview shell and debug providers.

This milestone is intentionally static: no GIFs, no sprite-sheet playback, no frame loops.
