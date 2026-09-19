# task_4 static native source

This package is a byte-exact runtime binding of the existing Eating Set v1
`task_4` image. It contains one 596×596 RGBA frame and deliberately claims no
motion. Reimu, the ramen, dumplings, table, tatami, steam, and heart marks are
unchanged from `assets/reimu/eating/task_4/base.png`.

It gives native `activeTaskCount == 4` an honest distinct visual identity while
multi-frame or explicitly authored layered art remains absent. Do not derive
layers from this flattened image, move the whole scene to manufacture motion,
or select it for five or more tasks.

The user approved the isolated 1.11/build 13 native review on 2026-09-20, so
production-identity packaging is allowed for this exact static source. That
approval does not turn the one-frame hold into a completed ramen-eating
animation.
