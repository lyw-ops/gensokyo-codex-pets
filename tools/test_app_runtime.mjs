#!/usr/bin/env node
// Dependency-free runtime checks for task-count mapping, animation loading,
// and explicit static fallback. Run with Node's module default enabled.

import assert from 'node:assert/strict';

import { loadStateAnimations } from '../app/animations.js';
import { eatingStateForTaskCount } from '../app/task-state-mapping.js';


function stateSet() {
  const base = '../assets/reimu/eating/task_2/base.png';
  return {
    binding: { character: 'reimu', stateSet: 'eating' },
    states: {
      task_2: {
        assetDir: '../assets/reimu/eating/task_2',
        base,
        manifest: '../assets/reimu/eating/task_2/animation.json',
        frames: [base],
        durationsMs: [0],
        loop: false,
        reducedMotionFrame: base,
        animation: { status: 'static-base', detail: 'manifest not loaded' },
      },
    },
  };
}


function manifest(overrides = {}) {
  return {
    manifest_version: 1,
    character: 'reimu',
    state_set: 'eating',
    state: 'task_2',
    playback: { loop: true },
    frames: [
      { file: 'frames/frame_000.png', duration_ms: 100 },
      { file: 'frames/frame_001.png', duration_ms: 100 },
    ],
    reduced_motion: { mode: 'hold_first_frame', frame: 'frames/frame_000.png' },
    ...overrides,
  };
}


async function loadWith(payload, brokenImages = new Set()) {
  const set = stateSet();
  globalThis.fetch = async () => ({ ok: true, json: async () => payload });
  globalThis.Image = class {
    set src(value) {
      queueMicrotask(() => brokenImages.has(value) ? this.onerror?.() : this.onload?.());
    }
  };
  const warnings = [];
  const originalWarn = console.warn;
  console.warn = (message) => warnings.push(message);
  try {
    await loadStateAnimations(set);
  } finally {
    console.warn = originalWarn;
  }
  return { state: set.states.task_2, warnings };
}


assert.equal(eatingStateForTaskCount(0), 'idle');
assert.equal(eatingStateForTaskCount(2), 'task_2');
assert.equal(eatingStateForTaskCount(5), 'task_5');
assert.equal(eatingStateForTaskCount(99), 'task_5');
assert.equal(eatingStateForTaskCount(-1), 'idle');
assert.equal(eatingStateForTaskCount(Number.NaN), 'idle');

const valid = await loadWith(manifest());
assert.equal(valid.state.animation.status, 'animated');
assert.equal(valid.state.frames.length, 2);
assert.deepEqual(valid.state.durationsMs, [100, 100]);
assert.equal(valid.state.loop, true);
assert.equal(valid.warnings.length, 0);

const wrongState = await loadWith(manifest({ state: 'task_3' }));
assert.equal(wrongState.state.animation.status, 'static-fallback');
assert.deepEqual(wrongState.state.frames, [wrongState.state.base]);
assert.match(wrongState.state.animation.detail, /state mismatch/);
assert.equal(wrongState.warnings.length, 1);

const brokenUrl = '../assets/reimu/eating/task_2/frames/frame_001.png';
const brokenFrame = await loadWith(manifest(), new Set([brokenUrl]));
assert.equal(brokenFrame.state.animation.status, 'static-fallback');
assert.deepEqual(brokenFrame.state.frames, [brokenFrame.state.base]);
assert.match(brokenFrame.state.animation.detail, /failed to load/);

console.log('app runtime checks passed');
