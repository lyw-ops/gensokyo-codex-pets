import { characters } from './characters.js';
import { eatingStateForTaskCount, EATING_STATE_IDS } from './task-state-mapping.js';

const character = characters.reimu;
const stateSet = character.stateSets.eating;

const spriteEl = document.getElementById('sprite');
const stateLabelEl = document.getElementById('state-label');
const taskInputEl = document.getElementById('task-input');
const buttonRowEl = document.getElementById('debug-buttons');
const stageEl = document.getElementById('stage');

// Preload every frame once so state switches never pop in late.
for (const state of Object.values(stateSet.states)) {
  for (const src of state.frames) {
    new Image().src = src;
  }
}

let currentTaskCount = 0;

function applyTaskCount(taskCount) {
  currentTaskCount = taskCount;
  const stateId = eatingStateForTaskCount(taskCount);
  const state = stateSet.states[stateId] ?? stateSet.states[stateSet.defaultState];
  spriteEl.src = state.frames[0];
  stateLabelEl.textContent = `tasks: ${taskCount} → state: ${stateId}`;
  taskInputEl.value = String(taskCount);
  for (const btn of buttonRowEl.querySelectorAll('button[data-tasks]')) {
    btn.classList.toggle('active', Number(btn.dataset.tasks) === taskCount);
  }
}

// Debug task provider: buttons for canonical and edge values.
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

// Display-size and background toggles for QA at desktop-pet scale.
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

// ?tasks=N picks the initial value (useful for screenshots).
const params = new URLSearchParams(location.search);
const initial = Number(params.get('tasks'));
applyTaskCount(Number.isFinite(initial) && params.has('tasks') ? initial : 0);
document.title = `${character.displayName} — eating set preview`;

// Expose EATING_STATE_IDS for console debugging.
window.__pet = { applyTaskCount, EATING_STATE_IDS };
