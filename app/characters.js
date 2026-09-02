// Character registry: Character -> StateSet -> State -> frames.
// `frames` is an ordered list so states can gain animation frames later
// without changing this shape; every state currently holds a single static
// base sprite. Paths are relative to app/index.html.

export const characters = {
  reimu: {
    displayName: 'Hakurei Reimu',
    stateSets: {
      eating: {
        defaultState: 'idle',
        states: {
          idle:   { frames: ['../assets/reimu/eating/idle/base.png'] },
          task_1: { frames: ['../assets/reimu/eating/task_1/base.png'] },
          task_2: { frames: ['../assets/reimu/eating/task_2/base.png'] },
          task_3: { frames: ['../assets/reimu/eating/task_3/base.png'] },
          task_4: { frames: ['../assets/reimu/eating/task_4/base.png'] },
          task_5: { frames: ['../assets/reimu/eating/task_5/base.png'] },
        },
      },
    },
  },
};
