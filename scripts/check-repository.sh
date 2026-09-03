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
  app/animations.js
  app/task-state-mapping.js
  app/README.md
  tools/split_eating_sheet.py
  tools/build_reimu_animations.py
  tools/test_build_reimu_animations.py
  pets/reimu/animations/eating/animation-set.json
  docs/sprite-harness-integration.md
)

for state in idle task_1 task_2 task_3 task_4 task_5; do
  required_files+=("assets/reimu/eating/${state}/base.png")
  required_files+=("assets/reimu/eating/${state}/animation.json")
  required_files+=("assets/reimu/eating/${state}/frames/frame_000.png")
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

# Eating Set v1 runtime sprites and published animation frames: 596x596 RGBA PNGs.
for state in idle task_1 task_2 task_3 task_4 task_5; do
  for png in "assets/reimu/eating/${state}/base.png" assets/reimu/eating/${state}/frames/*.png; do
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
done

# Consumer animation spec and published runtime manifests must be valid JSON.
python3 -m json.tool pets/reimu/animations/eating/animation-set.json >/dev/null

# Runtime manifest integrity: version, contiguous frame numbering, frame files
# present with matching digests, reduced-motion frame declared, and the
# immutable base.png digest recorded at build time still matching the file.
python3 - <<'PY'
import hashlib, json, pathlib, sys

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

failures = []
for state in ["idle", "task_1", "task_2", "task_3", "task_4", "task_5"]:
    state_dir = pathlib.Path("assets/reimu/eating") / state
    manifest = json.loads((state_dir / "animation.json").read_text())
    if manifest.get("manifest_version") != 1:
        failures.append(f"{state}: unsupported manifest_version")
        continue
    if manifest.get("state") != state:
        failures.append(f"{state}: manifest state mismatch: {manifest.get('state')}")
    frames = manifest.get("frames") or []
    if not frames:
        failures.append(f"{state}: manifest declares no frames")
        continue
    for index, frame in enumerate(frames):
        expected_name = f"frames/frame_{index:03d}.png"
        if frame.get("file") != expected_name:
            failures.append(f"{state}: frame {index} is {frame.get('file')!r}, want {expected_name!r}")
            continue
        frame_path = state_dir / frame["file"]
        if not frame_path.is_file():
            failures.append(f"{state}: missing frame file {frame['file']}")
        elif sha256(frame_path) != frame.get("sha256"):
            failures.append(f"{state}: frame digest mismatch for {frame['file']}")
        if not isinstance(frame.get("duration_ms"), int) or frame["duration_ms"] <= 0:
            failures.append(f"{state}: frame {index} has invalid duration_ms")
    declared = {frame.get("file") for frame in frames}
    actual = {f"frames/{p.name}" for p in (state_dir / "frames").glob("*.png")}
    if actual - declared:
        failures.append(f"{state}: undeclared frame files: {sorted(actual - declared)}")
    reduced = (manifest.get("reduced_motion") or {}).get("frame")
    if reduced not in declared:
        failures.append(f"{state}: reduced_motion.frame not among declared frames")
    source = manifest.get("source") or {}
    if source.get("file") != "base.png" or sha256(state_dir / "base.png") != source.get("sha256"):
        failures.append(f"{state}: manifest source binding does not match base.png")

for failure in failures:
    print(f"animation manifest check failed: {failure}", file=sys.stderr)
sys.exit(1 if failures else 0)
PY

echo "repository scaffold checks passed"
