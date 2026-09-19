# task_5 static native source

This package is a byte-exact runtime binding of the existing Eating Set v1
`task_5` image. It contains one 596×596 RGBA frame and deliberately claims no
motion. Reimu, ramen, rice balls, side dishes, tea, table, tatami, steam,
sparkles, droplets, and heart marks are unchanged from
`assets/reimu/eating/task_5/base.png`.

It is the visually approved source for the capped Tier 5 presentation,
selected when `activeTaskCount >= 5`. Approval covers the reviewed native
size, placement, static hold, and switching; it is not a completed eating
animation. Do not derive layers from this flattened image, move the whole
scene to manufacture motion, or add a second distributed task-count threshold
outside `ReimuFoodTier`.
