# Reimu sprite assets

Four reviewed Codex v2 row sources now exist under `codex-v2/`: the confirmed
loose-hair settle for standard `idle`, the attentive eyebrow loop for standard
`waiting`, the fixed-pose chewing loop for standard `running`, and the focused
single-brow loop for standard `review`. They are validated partial row sources, not a complete
sprite atlas or installable pet.

When art begins, keep editable source files separate from exported row strips and the assembled atlas. Use descriptive state names matching `docs/codex-pet-format.md`; do not use commercial game filenames or imported commercial sprite data.

A final local package candidate must include a transparent 1536×2288 PNG or WebP atlas, pass deterministic validation, and receive visual QA at actual pet size. Generated intermediates and QA renders belong in ignored build/QA directories unless maintainers explicitly decide to preserve them. Until the remaining standard rows and all 16 look directions are approved, each row builder must stop at its validated 1536×208 row strip.
