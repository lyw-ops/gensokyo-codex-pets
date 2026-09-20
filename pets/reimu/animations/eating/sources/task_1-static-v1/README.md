# task_1 static native source

This package is a byte-exact runtime binding of the existing Eating Set v1
`task_1` image. It contains one 596×596 RGBA frame and deliberately claims no
motion. Reimu, the onigiri, table, tatami, tear marks, and expression are
unchanged from `assets/reimu/eating/task_1/base.png`.

It is the visually approved source for the exact Tier1 presentation, selected
through `ReimuFoodTier` when `activeTaskCount == 1`. Approval covers the
reviewed native size, placement, static hold, and switching; it is not a
completed eating animation. Do not derive layers from this flattened image,
move the whole scene to manufacture motion, or add a second distributed
task-count threshold outside `ReimuFoodTier`.
