import { characters } from './characters.js';
import { loadStateAnimations } from './animations.js';
import { eatingStateForTaskCount, EATING_STATE_IDS } from './task-state-mapping.js';

const character = characters.reimu;
const stateSet = character.stateSets.eating;

const spriteEl = document.getElementById('sprite');
const stateLabelEl = document.getElementById('state-label');
const animLabelEl = document.getElementById('anim-label');
const taskInputEl = document.getElementById('task-input');
const buttonRowEl = document.getElementById('debug-buttons');
const stageEl = document.getElementById('stage');

let currentTaskCount = 0;
let currentStateId = stateSet.defaultState;

// ---- Reduced motion -------------------------------------------------------
// 'auto' follows the OS preference; 'full'/'reduced' are explicit QA
// overrides from the motion buttons.
const reducedMotionMedia = window.matchMedia('(prefers-reduced-motion: reduce)');
let motionMode = 'auto';

function reducedMotionActive() {
  if (motionMode === 'reduced') return true;
  if (motionMode === 'full') return false;
  return reducedMotionMedia.matches;
}

reducedMotionMedia.addEventListener('change', () => {
  if (motionMode === 'auto') showState(currentStateId);
});

// ---- Frame player ---------------------------------------------------------
// Exactly one playback loop exists at any time: showState invalidates the
// previous loop's token and clears its pending timer before starting.
let playToken = 0;
let pendingTimer = null;

function stopPlayback() {
  playToken += 1;
  if (pendingTimer !== null) {
    clearTimeout(pendingTimer);
    pendingTimer = null;
  }
}

function showState(stateId) {
  const state = stateSet.states[stateId] ?? stateSet.states[stateSet.defaultState];
  currentStateId = stateId;
  stopPlayback();

  const animBadge =
    state.animation.status === 'animated'
      ? `animation: ${state.animation.detail}`
      : `animation: ${state.animation.status} (${state.animation.detail})`;

  if (reducedMotionActive()) {
    spriteEl.src = state.reducedMotionFrame;
    animLabelEl.textContent = `${animBadge} — reduced motion: holding still frame`;
    return;
  }
  animLabelEl.textContent = animBadge;

  const token = playToken;
  let index = 0;
  const step = () => {
    if (token !== playToken) return;
    spriteEl.src = state.frames[index];
    if (state.frames.length <= 1) return; // static: no timer to schedule
    const durationMs = state.durationsMs[index];
    const next = index + 1;
    if (next >= state.frames.length && !state.loop) return; // hold last frame
    index = next % state.frames.length;
    pendingTimer = setTimeout(step, durationMs);
  };
  step();
}

function applyTaskCount(taskCount) {
  currentTaskCount = taskCount;
  const stateId = eatingStateForTaskCount(taskCount);
  showState(stateId);
  stateLabelEl.textContent = `tasks: ${taskCount} → state: ${stateId}`;
  taskInputEl.value = String(taskCount);
  for (const btn of buttonRowEl.querySelectorAll('button[data-tasks]')) {
    btn.classList.toggle('active', Number(btn.dataset.tasks) === taskCount);
  }
}

// ---- Debug task provider --------------------------------------------------
const DEBUG_VALUES = [-1, 0, 1, 2, 3, 4, 5, 6, 10];
for (const v of DEBUG_VALUES) {
  const btn = document.createElement('button');
  btn.dataset.tasks = String(v);
  btn.textContent = String(v);
  btn.addEventListener('click', () => applyTaskCount(v));
  buttonRowEl.appendChild(btn);
}

taskInputEl.addEventListener('change', () => {
  const n = Number(taskInputEl.value);
  applyTaskCount(Number.isFinite(n) ? n : 0);
});

// Keys 0–5 switch directly; ArrowUp/ArrowDown step the count.
document.addEventListener('keydown', (e) => {
  if (e.target === taskInputEl) return;
  if (/^[0-9]$/.test(e.key)) applyTaskCount(Number(e.key));
  else if (e.key === 'ArrowUp') applyTaskCount(currentTaskCount + 1);
  else if (e.key === 'ArrowDown') applyTaskCount(currentTaskCount - 1);
});

// ---- QA toggles: display size, background, motion mode --------------------
for (const btn of document.querySelectorAll('button[data-size]')) {
  btn.addEventListener('click', () => {
    stageEl.style.setProperty('--sprite-size', btn.dataset.size + 'px');
    document.querySelectorAll('button[data-size]').forEach((b) => b.classList.toggle('active', b === btn));
  });
}
for (const btn of document.querySelectorAll('button[data-bg]')) {
  btn.addEventListener('click', () => {
    stageEl.dataset.bg = btn.dataset.bg;
    document.querySelectorAll('button[data-bg]').forEach((b) => b.classList.toggle('active', b === btn));
  });
}
for (const btn of document.querySelectorAll('button[data-motion]')) {
  btn.addEventListener('click', () => {
    motionMode = btn.dataset.motion;
    document.querySelectorAll('button[data-motion]').forEach((b) => b.classList.toggle('active', b === btn));
    showState(currentStateId);
  });
}

// ---- Startup ---------------------------------------------------------------
// Load runtime manifests first (each state either upgrades to validated
// frames or explicitly falls back to base.png), then apply the initial count.
const params = new URLSearchParams(location.search);
const initial = Number(params.get('tasks'));
animLabelEl.textContent = 'loading animation manifests…';
loadStateAnimations(stateSet).then(() => {
  applyTaskCount(Number.isFinite(initial) && params.has('tasks') ? initial : 0);
});
document.title = `${character.displayName} — eating set preview`;

// Expose internals for console debugging.
window.__pet = { applyTaskCount, showState, EATING_STATE_IDS, stateSet };
