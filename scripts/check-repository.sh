#!/usr/bin/env bash
set -euo pipefail

required_files=(
  README.md
  HANDOFF.md
  LICENSE-or-NOTICE.md
  AGENTS.md
  docs/vision.md
  docs/codex-pet-format.md
  docs/reimu-design.md
  docs/reimu-action-system.md
  docs/workload-food-system.md
  docs/references.md
  docs/roadmap.md
  pets/reimu/README.md
  pets/reimu/design/visual-spec.md
  pets/reimu/sprites/README.md
  pets/reimu/metadata/README.md
  pets/reimu/metadata/pet.v2.example.json
  pets/reimu/metadata/actions.json
  docs/reference/reimu/eating_set_v1/README.md
  docs/reference/reimu/eating_set_v1/eating-set-v1-sheet.png
  assets/reimu/eating/README.md
  app/index.html
  app/main.js
  app/characters.js
  app/task-state-mapping.js
  app/README.md
  tools/split_eating_sheet.py
)

for state in idle task_1 task_2 task_3 task_4 task_5; do
  required_files+=("assets/reimu/eating/${state}/base.png")
done

for path in "${required_files[@]}"; do
  if [[ ! -s "$path" ]]; then
    echo "missing or empty required file: $path" >&2
    exit 1
  fi
done

python3 -m json.tool pets/reimu/metadata/pet.v2.example.json >/dev/null
python3 -m json.tool pets/reimu/metadata/actions.json >/dev/null

if ! grep -q "project-internal behavior specification" pets/reimu/metadata/actions.json; then
  echo "actions.json must declare itself a project-internal behavior specification" >&2
  exit 1
fi

if find pets/reimu/sprites -type f ! -name README.md -print -quit | grep -q .; then
  echo "pets/reimu/sprites is reserved for the reviewed Codex atlas pipeline" >&2
  exit 1
fi

# Eating Set v1 runtime sprites: 596x596 RGBA PNGs.
for state in idle task_1 task_2 task_3 task_4 task_5; do
  png="assets/reimu/eating/${state}/base.png"
  header=$(python3 - "$png" <<'PY'
import struct, sys
with open(sys.argv[1], 'rb') as f:
    data = f.read(33)
w, h = struct.unpack('>II', data[16:24])
color_type = data[25]
print(w, h, color_type)
PY
)
  if [[ "$header" != "596 596 6" ]]; then
    echo "unexpected sprite format for ${png}: ${header} (want 596 596 6 = RGBA)" >&2
    exit 1
  fi
done

echo "repository scaffold checks passed"
