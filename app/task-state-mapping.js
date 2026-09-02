// Central policy boundary: active-task count -> eating state id.
// Mirrors ReimuFoodTier = 0 | 1 | 2 | 3 | 4 | 5 (see docs/workload-food-system.md).
// Keep every task-count-to-state decision in this module; nothing else may
// re-implement the clamp.

export const EATING_STATE_IDS = [
  'idle',   // tier 0 — no active tasks
  'task_1', // tier 1 — exactly one active task
  'task_2', // tier 2 — exactly two active tasks
  'task_3', // tier 3 — exactly three active tasks
  'task_4', // tier 4 — exactly four active tasks
  'task_5', // tier 5 — five or more active tasks (visual cap)
];

// Negative, NaN, or non-numeric input degrades to the idle tier; callers that
// need to distinguish "observed zero" from "no data" must do so before calling.
export function eatingStateForTaskCount(taskCount) {
  const n = Number(taskCount);
  if (!Number.isFinite(n) || n <= 0) return EATING_STATE_IDS[0];
  return EATING_STATE_IDS[Math.min(Math.floor(n), 5)];
}
