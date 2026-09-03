// Character registry: Character -> StateSet -> State -> frames.
// `frames` is an ordered list. Every state starts on its immutable static
// base sprite; animations.js upgrades `frames`/`durationsMs`/`loop`/
// `reducedMotionFrame` in place when a validated runtime manifest
// (animation.json, published by tools/build_reimu_animations.py) is present.
// A missing or broken manifest leaves the state on this explicit static
// fallback. Paths are relative to app/index.html.

function eatingState(assetDir) {
  const base = `${assetDir}/base.png`;
  return {
    assetDir,
    base,
    manifest: `${assetDir}/animation.json`,
    frames: [base],
    durationsMs: [0],
    loop: false,
    reducedMotionFrame: base,
    animation: { status: 'static-base', detail: 'manifest not loaded' },
  };
}

export const characters = {
  reimu: {
    displayName: 'Hakurei Reimu',
    stateSets: {
      eating: {
        // Semantic binding checked against every loaded manifest
        // (animations.js): a manifest published for another character,
        // state set, or state must never be attached to this one.
        binding: { character: 'reimu', stateSet: 'eating' },
        defaultState: 'idle',
        states: {
          idle:   eatingState('../assets/reimu/eating/idle'),
          task_1: eatingState('../assets/reimu/eating/task_1'),
          task_2: eatingState('../assets/reimu/eating/task_2'),
          task_3: eatingState('../assets/reimu/eating/task_3'),
          task_4: eatingState('../assets/reimu/eating/task_4'),
          task_5: eatingState('../assets/reimu/eating/task_5'),
        },
      },
    },
  },
};
