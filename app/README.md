# State-switching preview app

A dependency-free preview for the Reimu Eating Set v1 runtime states. It is the current development harness for the visual state system; it is **not** a Codex pet package and does not observe real task activity.

## Run

Serve the repository root over HTTP (ES modules do not load over `file://` in all browsers):

```bash
python3 -m http.server 8123
```

Then open <http://localhost:8123/app/>.

## What it does

- Loads each state's published runtime manifest (`assets/reimu/eating/<state>/animation.json`) and plays its ordered, harness-validated `frames[]` with per-frame durations and loop settings. The current published set is the identity baseline (one frame per state), so playback is visually static until multi-frame animations ship; the player machinery is already exercised and state switches swap the frame set instantly.
- Falls back **explicitly** to `base.png` when a manifest is missing, malformed, or references broken frames: the state is marked `static-fallback` in the on-page animation status line and a warning is logged. Broken manifests are never silently absorbed.
- Maps a debug task count to a state through the single policy boundary in [`task-state-mapping.js`](task-state-mapping.js): `0 → idle`, `1..4 → task_1..task_4`, `>= 5 → task_5`, negative or invalid → `idle`.
- Honors reduced motion: `prefers-reduced-motion` (motion mode `auto`) or the explicit `reduced` QA toggle shows the state's declared reduced-motion frame and stops the frame timer.
- Debug task provider: buttons (`-1, 0, 1, 2, 3, 4, 5, 6, 10`), a free number input, keyboard keys `0–9` and `↑`/`↓`, and a `?tasks=N` URL parameter.
- QA controls: display size (160 px "pet size" up to 596 px native), background (checker / desktop / dark), and motion mode (auto / full / reduced).

## Structure

- [`characters.js`](characters.js) — Character → StateSet → State → frames registry. Every state starts on its static `base.png` and declares where its manifest lives.
- [`animations.js`](animations.js) — strict runtime-manifest loader: validates `animation.json`, preloads frames, and upgrades each state's `frames[]` in place, or records an explicit fallback status.
- [`task-state-mapping.js`](task-state-mapping.js) — the only place that converts a task count into a state id.
- [`main.js`](main.js) / [`index.html`](index.html) — preview shell, the single token-guarded frame player (exactly one playback loop at any time; state switches clear the pending timer), and debug providers.
