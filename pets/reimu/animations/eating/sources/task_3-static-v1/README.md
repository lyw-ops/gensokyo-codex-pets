# task_3 static native source

This package is a byte-exact runtime binding of the existing Eating Set v1
`task_3` image. It contains one 596×596 RGBA frame and deliberately claims no
motion. The character, bowl, table food, table, tatami, steam, and expression
marks are unchanged from `assets/reimu/eating/task_3/base.png`.

Its purpose is to give native `activeTaskCount == 3` an honest distinct visual
identity while multi-frame or explicitly authored layered art remains absent.
Do not derive layers from this flattened image, synthesize motion by moving the
whole scene, or describe the package as a completed tier-3 animation.

The user approved the isolated 1.10/build 12 native review on 2026-09-20, so
production-identity packaging is allowed for this exact static source. That
approval does not turn the one-frame hold into a completed animation.
