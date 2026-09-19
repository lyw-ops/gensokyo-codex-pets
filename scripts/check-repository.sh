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
  tools/check_reimu_layer_assets.py
  tools/check_reimu_pose_geometry.py
  tools/test_build_reimu_animations.py
  tools/test_app_runtime.mjs
  tools/import_reimu_chew_v7_running.py
  tools/build_reimu_codex_running_row.py
  tools/test_build_reimu_codex_running_row.py
  tools/import_reimu_idle_v1.py
  tools/build_reimu_codex_idle_row.py
  tools/test_build_reimu_codex_idle_row.py
  tools/import_reimu_waiting_v1.py
  tools/build_reimu_codex_waiting_row.py
  tools/test_build_reimu_codex_waiting_row.py
  tools/import_reimu_review_v1.py
  tools/build_reimu_codex_review_row.py
  tools/test_build_reimu_codex_review_row.py
  tools/import_reimu_task2_chew_v7.py
  tools/test_import_reimu_task2_chew_v7.py
  tools/import_reimu_task2_chew_v9.py
  tools/test_import_reimu_task2_chew_v9.py
  desktop/macos/test_work_tier2.py
  desktop/macos/test_work_tier3.py
  pets/reimu/animations/eating/animation-set.json
  pets/reimu/animations/eating/sources/task_2-chew-v7/source.json
  pets/reimu/animations/eating/sources/task_2-chew-v7/base.png
  pets/reimu/animations/eating/sources/task_2-chew-v9/source.json
  pets/reimu/animations/eating/sources/task_2-chew-v9/base.png
  pets/reimu/animations/eating/sources/task_3-static-v1/source.json
  pets/reimu/animations/eating/sources/task_3-static-v1/README.md
  pets/reimu/animations/eating/sources/task_3-static-v1/base.png
  pets/reimu/animations/eating/sources/task_3-static-v1/frames/frame_000.png
  docs/sprite-harness-integration.md
  docs/reimu-layered-assets-v1.md
  docs/task-2-layer-asset-intake.md
  pets/reimu/layers/eating/layer-set.json
  pets/reimu/layers/slouch/layer-set.json
  pets/reimu/animations/slouch/animation-set.json
  assets/reimu/layered/slouch/shared/tatami.png
  assets/reimu/layered/slouch/shared/table.png
  assets/reimu/layered/eating/README.md
  assets/reimu/eating/task_2/legacy-assets.json
  pets/reimu/sprites/codex-v2/README.md
  pets/reimu/sprites/codex-v2/rows/idle/source.json
  pets/reimu/sprites/codex-v2/rows/waiting/source.json
  pets/reimu/sprites/codex-v2/rows/running/source.json
  pets/reimu/sprites/codex-v2/rows/review/source.json
)

for frame in 000 001 002 003 004 005; do
  required_files+=("pets/reimu/sprites/codex-v2/rows/idle/frame_${frame}.png")
  required_files+=("pets/reimu/sprites/codex-v2/rows/waiting/frame_${frame}.png")
  required_files+=("pets/reimu/sprites/codex-v2/rows/running/frame_${frame}.png")
  required_files+=("pets/reimu/sprites/codex-v2/rows/review/frame_${frame}.png")
done

for frame in 000 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015; do
  required_files+=("pets/reimu/animations/eating/sources/task_2-chew-v7/frames/frame_${frame}.png")
  required_files+=("pets/reimu/animations/eating/sources/task_2-chew-v9/frames/frame_${frame}.png")
done

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

# The reviewed Codex atlas source tree currently contains exactly four approved
# row sources. No full atlas or installable package may appear before every row
# passes its visual gate.
python3 - <<'PY'
import pathlib, sys

root = pathlib.Path("pets/reimu/sprites")
allowed = {
    root / "README.md",
    root / "codex-v2/README.md",
    root / "codex-v2/rows/idle/source.json",
    *(root / f"codex-v2/rows/idle/frame_{index:03d}.png" for index in range(6)),
    root / "codex-v2/rows/waiting/source.json",
    *(root / f"codex-v2/rows/waiting/frame_{index:03d}.png" for index in range(6)),
    root / "codex-v2/rows/running/source.json",
    *(root / f"codex-v2/rows/running/frame_{index:03d}.png" for index in range(6)),
    root / "codex-v2/rows/review/source.json",
    *(root / f"codex-v2/rows/review/frame_{index:03d}.png" for index in range(6)),
}
actual = {path for path in root.rglob("*") if path.is_file()}
failures = []
if actual != allowed:
    failures.append(f"unexpected/missing reviewed sprite source files: {sorted(map(str, actual ^ allowed))}")
for forbidden in (pathlib.Path("pets/reimu/pet.json"), pathlib.Path("pets/reimu/spritesheet.webp")):
    if forbidden.exists():
        failures.append(f"installable pet artifact is premature: {forbidden}")
for failure in failures:
    print(f"Codex v2 source check failed: {failure}", file=sys.stderr)
sys.exit(1 if failures else 0)
PY

python3 tools/build_reimu_codex_running_row.py --check-only >/dev/null
python3 tools/build_reimu_codex_idle_row.py --check-only >/dev/null
python3 tools/build_reimu_codex_waiting_row.py --check-only >/dev/null
python3 tools/build_reimu_codex_review_row.py --check-only >/dev/null

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

# Consumer animation spec, layered-source contract, and published runtime
# manifests must be valid JSON.
python3 -m json.tool pets/reimu/animations/eating/animation-set.json >/dev/null
python3 -m json.tool pets/reimu/layers/eating/layer-set.json >/dev/null
python3 -m json.tool assets/reimu/eating/task_2/legacy-assets.json >/dev/null

# The retired pre-chew-v7 fallback has one canonical, named copy. Its former
# Finder-style duplicate alias must not reappear in the runtime frame set.
python3 - <<'PY'
import hashlib, json, pathlib

state_dir = pathlib.Path("assets/reimu/eating/task_2")
manifest = json.loads((state_dir / "legacy-assets.json").read_text())
if manifest.get("legacy_assets_version") != 1:
    raise SystemExit("unsupported task_2 legacy_assets_version")
assets = manifest.get("assets") or []
if len(assets) != 1:
    raise SystemExit("task_2 legacy manifest must declare exactly one canonical asset")
entry = assets[0]
path = state_dir / entry.get("file", "")
if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry.get("sha256"):
    raise SystemExit("task_2 canonical legacy base is missing or digest-mismatched")
alias = state_dir / entry.get("archived_alias", "")
if alias.exists():
    raise SystemExit(f"retired task_2 legacy alias reappeared in runtime frames: {alias}")
PY

# The approved task_2 exact sequence is the published consumer source. Reuse
# the builder's fail-closed loader so digest, binding, numbering, endpoint and
# undeclared-file checks cannot drift from the production configuration.
python3 - <<'PY'
import json
from pathlib import Path
from tools import build_reimu_animations as build

config = build.load_config(Path("pets/reimu/animations/eating/animation-set.json"))
if build.state_source_mode(config, "task_2") != "exact_frames":
    raise SystemExit("production task_2 must use the approved exact_frames source")
exact = build.load_exact_frame_source(config, "task_2")
runtime = json.loads(Path("assets/reimu/eating/task_2/animation.json").read_text())
provenance = runtime.get("provenance") or {}
configured = config["states"]["task_2"]["frame_source"]
if provenance.get("source_mode") != "approved_exact_frames":
    raise SystemExit("published task_2 runtime is not bound to approved exact frames")
if provenance.get("frame_source") != configured:
    raise SystemExit("published task_2 runtime does not match the configured exact source")
if provenance.get("frame_source_sha256") != exact["manifest_sha256"]:
    raise SystemExit("published task_2 runtime exact-source manifest digest is stale")
runtime_frames = runtime.get("frames") or []
source_frames = exact["manifest"].get("frames") or []
if [frame.get("sha256") for frame in runtime_frames] != [
        frame.get("sha256") for frame in source_frames]:
    raise SystemExit("published task_2 runtime frames do not match the configured exact source")
PY

# Tier 3 is intentionally a byte-exact static source. It is a distinct native
# workload identity, not a claim that a multi-frame task_3 animation exists.
python3 - <<'PY'
import hashlib, json
from pathlib import Path

root = Path("pets/reimu/animations/eating/sources/task_3-static-v1")
manifest = json.loads((root / "source.json").read_text())
expected = "45c212c88bd39053bb351d5f7bdf8da5d1a95ca743c532232290288927a2a9ff"
if manifest.get("state_set") != "eating" or manifest.get("state") != "task_3":
    raise SystemExit("task_3 static source identity mismatch")
if manifest.get("playback") != {"fps": 8, "frame_count": 1, "loop": True}:
    raise SystemExit("task_3 static source playback mismatch")
for relative in ("base.png", "frames/frame_000.png"):
    if hashlib.sha256((root / relative).read_bytes()).hexdigest() != expected:
        raise SystemExit(f"task_3 static source digest mismatch: {relative}")
if hashlib.sha256(Path("assets/reimu/eating/task_3/base.png").read_bytes()).hexdigest() != expected:
    raise SystemExit("task_3 static source drifted from the existing Eating Set asset")
PY

node --experimental-default-type=module tools/test_app_runtime.mjs >/dev/null
python3 -m unittest tools.test_import_reimu_task2_chew_v7 >/dev/null
python3 -m unittest tools.test_import_reimu_task2_chew_v9 >/dev/null

# Layered sources are authored, never generated at runtime: the layered tree
# may contain only PNGs (plus documentation), and layer-set layer ids must be
# unique with unique z-order.
python3 - <<'PY'
import json, pathlib, sys

layer_set = json.loads(pathlib.Path("pets/reimu/layers/eating/layer-set.json").read_text())
ids = [layer["id"] for layer in layer_set["layers"]]
zs = [layer["z"] for layer in layer_set["layers"]]
failures = []
if len(set(ids)) != len(ids):
    failures.append("layer-set has duplicate layer ids")
if len(set(zs)) != len(zs):
    failures.append("layer-set has duplicate z-order values")
if layer_set.get("reference_canvas") != {"width": 596, "height": 596}:
    failures.append("layer-set reference_canvas must stay 596x596")
for path in pathlib.Path("assets/reimu/layered").rglob("*"):
    if path.is_file() and path.suffix not in (".png",) and path.name not in ("README.md", ".gitkeep"):
        failures.append(f"unexpected file in layered source tree: {path}")
for failure in failures:
    print(f"layered contract check failed: {failure}", file=sys.stderr)
sys.exit(1 if failures else 0)
PY

# Runtime manifest integrity: version, contiguous frame numbering, frame files
# present with matching digests, reduced-motion frame declared, and the
# immutable source binding (base.png or the state's authored layer PNGs).
python3 - <<'PY'
import hashlib, json, pathlib, sys
from tools.check_reimu_layer_assets import validate_runtime_source

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
    if manifest.get("character") != "reimu" or manifest.get("state_set") != "eating":
        failures.append(f"{state}: manifest character/state_set binding mismatch")
    if (state_dir / ".publish-recovery.json").exists():
        failures.append(f"{state}: unresolved publish recovery marker present")
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
    failures.extend(f"{state}: {error}" for error in
                    validate_runtime_source(source, state, pathlib.Path.cwd()))

for failure in failures:
    print(f"animation manifest check failed: {failure}", file=sys.stderr)
sys.exit(1 if failures else 0)
PY

echo "repository scaffold checks passed"
