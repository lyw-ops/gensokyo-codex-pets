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
  docs/workload-food-system.md
  docs/references.md
  docs/roadmap.md
  pets/reimu/README.md
  pets/reimu/design/visual-spec.md
  pets/reimu/sprites/README.md
  pets/reimu/metadata/README.md
  pets/reimu/metadata/pet.v2.example.json
)

for path in "${required_files[@]}"; do
  if [[ ! -s "$path" ]]; then
    echo "missing or empty required file: $path" >&2
    exit 1
  fi
done

python3 -m json.tool pets/reimu/metadata/pet.v2.example.json >/dev/null

if find pets/reimu/sprites -type f ! -name README.md -print -quit | grep -q .; then
  echo "Milestone 0 must not contain unreviewed Reimu sprite assets" >&2
  exit 1
fi

echo "repository scaffold checks passed"
