#!/usr/bin/env python3
"""Build and publish validated Reimu animation sets via Sprite Harness.

This is the consumer-side entry point of the animation pipeline:

    animation-set.json (consumer spec)
        -> one Sprite Harness Animation Plan per state
           (source_mode "flattened":   plan v1 rendered from immutable base.png;
            source_mode "layered":     plan v2 composed from explicitly authored
                                        layer PNGs;
            source_mode "exact_frames": plan v1 bound to base.png with a pinned,
                                         pre-reviewed external frame sequence)
        -> sprite-harness plan / render / validate --write-qa / preview /
           contact-sheet / report        (public CLI, JSON mode, exit codes)
        -> publish validated frames + a runtime animation.json manifest
           next to each state's immutable base.png
           (set-level transaction: all states commit as one generation or
            every changed state is rolled back)

Sprite Harness is used strictly through its public CLI/JSON contract
(https://github.com/lyw-ops/Spirite-harness, HARNESS.md). No harness module is
imported and no private artifact format is re-implemented here. Source sprites
are immutable input: this tool verifies their SHA-256 is unchanged after every
build and never overwrites base.png.

Usage:
    python3 tools/build_reimu_animations.py [--states idle task_3]
        [--config PATH] [--build-dir PATH] [--harness BIN]
        [--publish-root PATH] [--no-publish]

The harness executable is located from --harness, then the SPRITE_HARNESS_BIN
environment variable, then PATH. Validation failures abort publication for the
whole run: either every requested state validates or nothing is published.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "pets" / "reimu" / "animations" / "eating" / "animation-set.json"
BUILD_ROOT = REPO_ROOT / "build" / "animations"


def default_build_dir(config: dict) -> Path:
    """Each animation set gets its own disposable build area, so two sets that
    happen to share a state name can never overwrite each other's builds."""
    return BUILD_ROOT / config["character"] / config["state_set"]

MANIFEST_VERSION = 1
MANIFEST_NAME = "animation.json"
FRAMES_DIR_NAME = "frames"

INSTALL_HINT = """\
sprite-harness executable not found.

Install Sprite Harness (https://github.com/lyw-ops/Spirite-harness):

    git clone https://github.com/lyw-ops/Spirite-harness
    cd Spirite-harness
    python3 -m venv .venv
    .venv/bin/pip install .

Then either put its bin directory on PATH, set SPRITE_HARNESS_BIN to the
executable, or pass --harness /path/to/sprite-harness. This tool never falls
back to a private renderer: without the harness there is no validated build.\
"""


class BuildError(RuntimeError):
    """A pipeline step failed; the message is user-facing."""


def assert_build_isolation(build_dir: Path, protected: dict[str, Path]) -> None:
    """Refuse a destructive build path that aliases or overlaps protected paths.

    The build directory is disposable: `build_state` deletes and recreates its
    per-state subdirectories. Before any deletion it must be provably disjoint
    from the immutable source tree, the publish tree, and every individual
    source sprite. Comparison uses fully resolved paths (`os.path.realpath`),
    so relative aliases, `..` segments, and symlinks cannot smuggle the build
    directory into a protected tree. Fails closed: any equality or containment
    relationship in either direction is an error.
    """
    build_real = Path(os.path.realpath(build_dir))
    for name, path in protected.items():
        real = Path(os.path.realpath(path))
        if build_real == real:
            raise BuildError(
                f"unsafe build directory: {build_dir} resolves to the same path as "
                f"{name} ({real}); the build directory is disposable and must never "
                "alias source or publish assets")
        if real in build_real.parents:
            raise BuildError(
                f"unsafe build directory: {build_dir} is inside {name} ({real}); "
                "destructive build operations must stay outside protected trees")
        if build_real in real.parents:
            raise BuildError(
                f"unsafe build directory: {name} ({real}) is inside the build "
                f"directory {build_dir}; deleting build state would destroy it")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_harness(explicit: str | None = None) -> str:
    """Locate the sprite-harness executable; raise BuildError with install help."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    env = os.environ.get("SPRITE_HARNESS_BIN")
    if env:
        candidates.append(env)
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
        located = shutil.which(candidate)
        if located:
            return located
        raise BuildError(f"harness executable not usable: {candidate}\n\n{INSTALL_HINT}")
    located = shutil.which("sprite-harness")
    if located:
        return located
    raise BuildError(INSTALL_HINT)


def load_config(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
    except FileNotFoundError:
        raise BuildError(f"animation set config not found: {path}")
    except json.JSONDecodeError as error:
        raise BuildError(f"animation set config is not valid JSON: {path}: {error}")
    if "spec_path" in config:
        raise BuildError("animation set config must not declare the derived key 'spec_path'")
    # Provenance must stay resolvable inside the repository, like every other root.
    relative = os.path.relpath(Path(path).resolve(), start=REPO_ROOT.resolve())
    if relative.startswith(".."):
        raise BuildError(f"animation set config must live inside the repository: {path}")
    config["spec_path"] = relative
    if config.get("set_version") != 1:
        raise BuildError(f"unsupported animation set_version: {config.get('set_version')!r}")
    for key in ("character", "state_set", "source_root", "publish_root", "source_file",
                "animation_id_prefix", "defaults", "states"):
        if key not in config:
            raise BuildError(f"animation set config missing required key: {key}")
    if not config["states"]:
        raise BuildError("animation set config declares no states")
    return config


# Consumer-only state keys: routing/config for this builder, never part of the
# generated Animation Plan (unknown plan fields are MALFORMED_SPEC).
CONSUMER_STATE_KEYS = {"source_mode", "frame_source", "layer_visibility"}


def state_source_mode(config: dict, state_id: str) -> str:
    """Return the consumer input mode for one state."""
    if state_id not in config["states"]:
        raise BuildError(f"unknown state: {state_id}")
    mode = (config["states"][state_id] or {}).get("source_mode", "flattened")
    if mode not in ("flattened", "layered", "exact_frames"):
        raise BuildError(f"unsupported source_mode for {state_id}: {mode!r}")
    return mode


def exact_frame_source_path(config: dict, state_id: str, repo_root: Path | None = None) -> Path:
    """Resolve a configured exact-frame manifest inside the repository."""
    root = (repo_root or REPO_ROOT).resolve()
    state = config["states"].get(state_id) or {}
    configured = state.get("frame_source")
    if not isinstance(configured, str) or not configured:
        raise BuildError(f"state {state_id} uses exact_frames but declares no frame_source")
    relative = Path(configured)
    path = (root / relative).resolve()
    if relative.is_absolute() or not path.is_relative_to(root):
        raise BuildError(f"state {state_id}: frame_source must stay inside the repository")
    return path


def inspect_exact_frame_png(path: Path, canvas: dict) -> None:
    """Verify the exact-source PNG contract before invoking Harness."""
    try:
        from PIL import Image
    except ImportError:
        raise BuildError("exact frame inspection requires Pillow; use the Sprite Harness venv")
    try:
        with Image.open(path) as image:
            image.load()
            if image.format != "PNG" or image.mode != "RGBA":
                raise BuildError(f"exact frame must be RGBA PNG: {path}")
            expected = (canvas["width"], canvas["height"])
            if image.size != expected:
                raise BuildError(f"exact frame dimensions {image.size}, want {expected}: {path}")
            low, high = image.getchannel("A").getextrema()
            if low == 255 or high == 0:
                raise BuildError(f"exact frame must contain visible pixels and transparency: {path}")
    except BuildError:
        raise
    except (OSError, SyntaxError, ValueError) as error:
        raise BuildError(f"exact frame is unreadable: {path}: {error}") from error


def load_exact_frame_source(config: dict, state_id: str,
                            repo_root: Path | None = None) -> dict:
    """Load and fail-closed validate one reviewed external frame package."""
    manifest_path = exact_frame_source_path(config, state_id, repo_root)
    try:
        with open(manifest_path, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except FileNotFoundError:
        raise BuildError(f"exact frame source not found: {manifest_path}")
    except json.JSONDecodeError as error:
        raise BuildError(f"exact frame source is invalid JSON: {manifest_path}: {error}")

    if manifest.get("exact_frame_source_version") != 1:
        raise BuildError("unsupported exact_frame_source_version")
    expected_binding = (config["character"], config["state_set"], state_id)
    actual_binding = (manifest.get("character"), manifest.get("state_set"), manifest.get("state"))
    if actual_binding != expected_binding:
        raise BuildError(
            f"exact frame source binding mismatch: {actual_binding}, want {expected_binding}")
    canvas = manifest.get("canvas") or {}
    if any(type(canvas.get(key)) is not int or canvas[key] <= 0 for key in ("width", "height")):
        raise BuildError("exact frame source canvas must have positive integer width/height")
    playback = manifest.get("playback") or {}
    frame_count = playback.get("frame_count")
    if (type(frame_count) is not int or frame_count <= 0
            or not isinstance(playback.get("fps"), (int, float))
            or playback["fps"] <= 0 or type(playback.get("loop")) is not bool):
        raise BuildError("exact frame source playback is malformed")

    package_root = manifest_path.parent
    base = manifest.get("base") or {}
    base_path = package_root / "base.png"
    if (base.get("file") != "base.png" or not base_path.is_file()
            or sha256_file(base_path) != base.get("sha256")):
        raise BuildError("exact frame source base.png is missing or digest-mismatched")
    inspect_exact_frame_png(base_path, canvas)

    frames = manifest.get("frames") or []
    if len(frames) != frame_count:
        raise BuildError("exact frame source count does not match playback.frame_count")
    frame_paths = []
    frame_durations = []
    expected_files = {"source.json", "base.png"}
    for index, frame in enumerate(frames):
        expected_name = f"frames/frame_{index:03d}.png"
        if not isinstance(frame, dict) or frame.get("file") != expected_name:
            raise BuildError(f"exact frame {index} must be {expected_name}")
        duration = frame.get("duration_ms")
        if type(duration) is not int or duration <= 0:
            raise BuildError(f"exact frame {index} has invalid duration_ms")
        path = package_root / expected_name
        if not path.is_file() or sha256_file(path) != frame.get("sha256"):
            raise BuildError(f"exact frame {index} is missing or digest-mismatched")
        inspect_exact_frame_png(path, canvas)
        frame_paths.append(path)
        frame_durations.append(duration)
        expected_files.add(expected_name)
    actual_files = {
        str(path.relative_to(package_root))
        for path in package_root.rglob("*") if path.is_file()
    }
    if actual_files != expected_files:
        raise BuildError(
            f"exact frame source has undeclared/missing files: {sorted(actual_files ^ expected_files)}")
    if playback["loop"] and frame_paths[0].read_bytes() != frame_paths[-1].read_bytes():
        raise BuildError("looping exact frame source endpoints must be byte-identical")
    if base_path.read_bytes() != frame_paths[0].read_bytes():
        raise BuildError("exact frame source base.png must equal frame_000.png")
    return {
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "base_path": base_path,
        "base_sha256": base["sha256"],
        "frame_paths": frame_paths,
        "frame_durations_ms": frame_durations,
    }


def visibility_groups(layer_set: dict, present: set[str]) -> dict[str, list[str]]:
    """Mutually exclusive layer groups, restricted to the layers actually present."""
    groups: dict[str, list[str]] = {}
    for layer in layer_set["layers"]:
        group = layer.get("visibility_group")
        if group and layer["id"] in present:
            groups.setdefault(group, []).append(layer["id"])
    return groups


def visibility_owners(group: str, members: list[str], spec: dict, frame_count: int) -> list[str]:
    """Resolve which member of a group owns each frame.

    A group is exclusive by construction: every frame has exactly one owner, so
    the two eye layers can never be composited on top of each other.
    """
    default = spec.get("default")
    if default not in members:
        raise BuildError(f"visibility group {group!r}: default {default!r} is not one of "
                         f"its present layers {members}")
    owners = [default] * frame_count
    claimed: dict[int, str] = {}
    for member, frames in (spec.get("frames") or {}).items():
        if member not in members:
            raise BuildError(f"visibility group {group!r}: {member!r} is not one of its "
                             f"present layers {members}")
        if not isinstance(frames, list) or any(type(index) is not int for index in frames):
            raise BuildError(f"visibility group {group!r}: {member!r} frames must be a list "
                             f"of integer frame indices")
        for index in frames:
            if not 0 <= index < frame_count:
                raise BuildError(f"visibility group {group!r}: frame {index} for {member!r} "
                                 f"is outside the state's {frame_count} frame(s)")
            if index in claimed:
                raise BuildError(f"visibility group {group!r}: frame {index} is claimed by "
                                 f"both {claimed[index]!r} and {member!r}")
            claimed[index] = member
            owners[index] = member
    return owners


def resolve_visibility(layer_set: dict, config: dict, state_id: str,
                       present: set[str], frame_count: int) -> tuple[set[str], list[dict]]:
    """Turn a state's `layer_visibility` into (layers to drop, opacity tracks).

    Visibility that never changes needs no motion at all: a layer that is hidden
    for the whole state is simply left out of the composed source, which every
    published harness version supports. Only visibility that varies over time
    needs tracks, and those use keyframes with `hold` so exactly one member of a
    group is ever composited. Without either mechanism every applicable layer is
    composited, which silently stacks the two eye layers instead of blinking.
    """
    groups = visibility_groups(layer_set, present)
    declared = (config["states"][state_id] or {}).get("layer_visibility") or {}
    for group in declared:
        if group not in groups:
            raise BuildError(f"state {state_id} declares layer_visibility for unknown or "
                             f"absent group {group!r}; present groups: {sorted(groups)}")
    excluded: set[str] = set()
    tracks: list[dict] = []
    for group, members in sorted(groups.items()):
        if group not in declared:
            if len(members) > 1:
                raise BuildError(
                    f"state {state_id}: layers {members} share visibility group {group!r} but "
                    f"the state declares no layer_visibility for it. Without it every layer is "
                    f"composited at once, so they would be stacked instead of exclusive.")
            continue
        owners = visibility_owners(group, members, declared[group], frame_count)
        for member in members:
            visible = [owner == member for owner in owners]
            if all(visible):
                continue  # Always shown: opacity is already 1, so nothing is needed.
            if not any(visible):
                excluded.add(member)  # Never shown: drop it instead of animating it to zero.
                continue
            values = [0.0 if shown else -1.0 for shown in visible]
            keyframes = [
                {"at": index / frame_count, "value": value, "interpolation": "hold"}
                for index, value in enumerate(values)
                if index == 0 or value != values[index - 1]
            ]
            tracks.append({"track_id": f"visibility_{group}_{member}", "target": member,
                           "motion": "opacity", "unit": "ratio", "keyframes": keyframes})
    return excluded, tracks


def compose_plan_spec(config: dict, state_id: str, layered_source: dict | None = None,
                      visibility_tracks: list[dict] | None = None) -> dict:
    """Deterministically expand one state into a legal Animation Plan spec.

    State entries may override any of the default plan sections; the merge is
    per top-level key (no deep merging inside a section, so an override is
    always a complete, reviewable section). A layered state (source_mode:
    "layered") becomes a plan_version 2 spec with the given inline `source`
    object; consumer-only keys never reach the plan.
    """
    if state_id not in config["states"]:
        raise BuildError(f"unknown state: {state_id}")
    overrides = config["states"][state_id] or {}
    plan: dict = copy.deepcopy(config["defaults"])
    for key, value in overrides.items():
        if key in CONSUMER_STATE_KEYS:
            continue
        plan[key] = copy.deepcopy(value)
    if state_source_mode(config, state_id) == "layered":
        if layered_source is None:
            raise BuildError(f"state {state_id} is layered but no layered source was composed")
        plan["plan_version"] = 2
        plan["source"] = copy.deepcopy(layered_source)
        generated = list(visibility_tracks or [])
        if generated:
            authored = list(plan.get("tracks") or [])
            controlled = {track["target"] for track in generated}
            generated_ids = {track["track_id"] for track in generated}
            for track in authored:
                if track.get("motion") == "opacity" and track.get("target") in controlled:
                    raise BuildError(
                        f"state {state_id}: track {track.get('track_id')!r} already drives the "
                        f"opacity of {track.get('target')!r}, which visibility groups control")
                if track.get("track_id") in generated_ids:
                    raise BuildError(f"state {state_id}: track_id {track['track_id']!r} collides "
                                     f"with a generated visibility track")
            plan["tracks"] = authored + generated
    plan["animation_id"] = f"{config['animation_id_prefix']}_{state_id}"
    metadata = dict(plan.get("metadata") or {})
    metadata.update(
        {
            "character": config["character"],
            "state_set": config["state_set"],
            "state": state_id,
            "consumer": config.get("consumer", "gensokyo-codex-pets"),
            "spec": config_spec_path(config),
        }
    )
    plan["metadata"] = metadata
    return plan


def load_layer_set(path: Path) -> dict:
    """Load and shape-check the consumer layered-source contract.

    This is consumer-side authoring metadata (see
    docs/reimu-layered-assets-v1.md), not a Sprite Harness schema: the builder
    turns it into the inline `source` object of an Animation Plan v2.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            layer_set = json.load(handle)
    except FileNotFoundError:
        raise BuildError(f"layer set not found: {path}")
    except json.JSONDecodeError as error:
        raise BuildError(f"layer set is not valid JSON: {path}: {error}")
    if layer_set.get("layer_set_version") != 1:
        raise BuildError(f"unsupported layer_set_version: {layer_set.get('layer_set_version')!r}")
    for key in ("character", "state_set", "reference_canvas", "asset_root", "layers"):
        if key not in layer_set:
            raise BuildError(f"layer set missing required key: {key}")
    canvas = layer_set["reference_canvas"]
    if not isinstance(canvas, dict) or any(type(canvas.get(key)) is not int or canvas[key] <= 0
                                           for key in ("width", "height")):
        raise BuildError("layer set reference_canvas must have positive integer dimensions")
    if layer_set.get("canvas_policy") not in (None, "full_canvas"):
        raise BuildError("unsupported layer canvas_policy; pilot requires full_canvas")
    if not layer_set["layers"]:
        raise BuildError("layer set declares no layers")
    seen_ids = set()
    for layer in layer_set["layers"]:
        for key in ("id", "scope", "image", "anchor", "position", "z"):
            if key not in layer:
                raise BuildError(f"layer entry missing required key {key!r}: {layer}")
        if layer["scope"] not in ("shared", "state"):
            raise BuildError(f"layer {layer['id']}: unsupported scope {layer['scope']!r}")
        if layer["id"] in seen_ids:
            raise BuildError(f"duplicate layer id: {layer['id']}")
        seen_ids.add(layer["id"])
    return layer_set


def config_spec_path(config: dict) -> str:
    """Repo-relative path of the animation set a plan or manifest came from.

    `load_config` records the real path it read. A config assembled in memory
    falls back to this repository's layout convention for its state set.
    """
    return config.get("spec_path") or (
        f"pets/reimu/animations/{config['state_set']}/animation-set.json")


def assert_layer_set_binding(layer_set: dict, config: dict) -> None:
    """A layer set may only be used by the animation set it declares itself part of."""
    expected = (config["character"], config["state_set"])
    found = (layer_set["character"], layer_set["state_set"])
    if found != expected:
        raise BuildError(f"layer set binding mismatch: layer set declares {found}, "
                         f"animation set {config_spec_path(config)} declares {expected}")


def applicable_layers(layer_set: dict, state_id: str) -> list[dict]:
    """The shared state filter and back-to-front order for build and intake."""
    layers = [layer for layer in layer_set["layers"]
              if layer.get("states") is None or state_id in layer["states"]]
    if not layers:
        raise BuildError(f"layer set declares no layers applicable to state {state_id}")
    zs = [layer["z"] for layer in layers]
    if len(set(zs)) != len(zs):
        raise BuildError(f"duplicate z-order among layers applicable to {state_id}")
    return sorted(layers, key=lambda layer: layer["z"])


def layer_image_path(layer: dict, state_id: str, layer_root: Path) -> Path:
    """Resolve an authored PNG without allowing paths or aliases outside its root."""
    relative = Path(layer["image"].replace("{state}", state_id))
    path = layer_root / relative
    if relative.is_absolute() or not path.resolve().is_relative_to(layer_root.resolve()):
        raise BuildError(f"layer {layer['id']}: source file outside asset_root: {path}")
    if relative.suffix != ".png" or relative.stem != layer["id"]:
        raise BuildError(f"layer {layer['id']}: PNG filename must match layer id: {relative}")
    return path


def compose_layered_source(layer_set: dict, state_id: str, layer_root: Path,
                           plan_dir: Path) -> tuple[dict, list[tuple[str, Path, str]]]:
    """Compose the Animation Plan v2 `source` object for one state.

    Layers are filtered to the state (shared layers always apply; a layer may
    restrict itself with a `states` list), ordered back-to-front by their
    unique `z`, and `{state}` in image paths is substituted. Missing required
    PNGs fail closed with an explicit ART ASSET REQUIRED error; optional
    layers (`"required": false`) are skipped when their file is absent.

    Returns the source object (image paths relative to `plan_dir`, where the
    generated plan spec is written) plus [(layer_id, absolute_path, sha256)]
    for post-build immutability verification.
    """
    applicable = applicable_layers(layer_set, state_id)

    source_layers = []
    layer_files: list[tuple[str, Path, str]] = []
    missing = []
    for layer in applicable:
        image_path = layer_image_path(layer, state_id, layer_root)
        if not image_path.is_file():
            if layer.get("required", True):
                missing.append(f"{layer['id']} -> {image_path}")
            continue
        source_layers.append(
            {
                "target": layer["id"],
                "image": os.path.relpath(image_path, start=plan_dir),
                "anchor": copy.deepcopy(layer["anchor"]),
                "position": copy.deepcopy(layer["position"]),
            }
        )
        layer_files.append((layer["id"], image_path, sha256_file(image_path)))
    if missing:
        raise BuildError(
            f"ART ASSET REQUIRED: state {state_id} is declared layered but these "
            "authored layer PNGs do not exist yet (see docs/reimu-layered-assets-v1.md "
            "for the asset specification):\n  " + "\n  ".join(missing)
        )
    if not source_layers:
        raise BuildError(f"no layer PNGs available for layered state {state_id}")
    return (
        {
            "reference_canvas": copy.deepcopy(layer_set["reference_canvas"]),
            "layers": source_layers,
        },
        layer_files,
    )


def run_harness(harness: str, args: list[str], *, step: str) -> dict:
    """Run one sprite-harness command in JSON mode and check its exit code."""
    command = [harness, *args, "--json"]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise BuildError(
            f"sprite-harness {step} failed (exit {result.returncode}):\n"
            f"  command: {' '.join(command)}\n"
            f"  stdout: {result.stdout.strip()}\n"
            f"  stderr: {result.stderr.strip()}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise BuildError(f"sprite-harness {step} returned non-JSON output: {error}\n{result.stdout}")


def harness_version(harness: str) -> str:
    result = subprocess.run([harness, "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        raise BuildError(f"sprite-harness --version failed: {result.stderr.strip()}")
    return result.stdout.strip()


def build_state(harness: str, config: dict, state_id: str, build_dir: Path,
                source_root: Path, publish_root: Path | None = None,
                layer_set: dict | None = None, layer_root: Path | None = None,
                exact_source: dict | None = None) -> dict:
    """Run the full harness pipeline for one state; return build facts.

    A state's `source_mode` selects the input contract: "flattened" (default)
    renders the immutable base sprite through Animation Plan v1; "layered"
    composes Animation Plan v2 from authored PNGs; "exact_frames" binds a
    reviewed external sequence to the same immutable base and deliberately
    skips Harness rendering. Every mode is validated, previewed and reported.
    """
    source_mode = state_source_mode(config, state_id)
    source = source_root / state_id / config["source_file"]
    protected = {"source_root": source_root, f"source sprite ({state_id})": source}
    if publish_root is not None:
        protected["publish_root"] = publish_root
    if layer_root is not None:
        protected["layer_root"] = layer_root
    if exact_source is not None:
        protected[f"exact frame source ({state_id})"] = exact_source["manifest_path"].parent
    assert_build_isolation(build_dir, protected)

    source_sha_before = None
    if source_mode in ("flattened", "exact_frames"):
        if not source.is_file():
            raise BuildError(f"source sprite not found: {source}")
        source_sha_before = sha256_file(source)
        if source_mode == "exact_frames":
            if exact_source is None:
                raise BuildError(f"state {state_id} is exact_frames but no frame source was loaded")
            if source_sha_before != exact_source["base_sha256"]:
                raise BuildError(
                    f"state {state_id}: base.png does not match exact frame source neutral")
            playback = (exact_source["manifest"].get("playback") or {})
            if plan_playback := (config["states"].get(state_id) or {}).get("playback"):
                if plan_playback != playback:
                    raise BuildError(
                        f"state {state_id}: config playback does not match exact frame source")
    elif layer_set is None or layer_root is None:
        raise BuildError(f"state {state_id} is layered but no layer set / layer root was provided")

    state_build = build_dir / state_id
    if state_build.exists():
        shutil.rmtree(state_build)
    state_build.mkdir(parents=True)

    layered_source = None
    layer_files: list[tuple[str, Path, str]] = []
    tracks = None
    if source_mode == "layered":
        layered_source, layer_files = compose_layered_source(
            layer_set, state_id, layer_root, state_build)
        frame_count = compose_plan_spec(config, state_id,
                                        layered_source=layered_source)["playback"]["frame_count"]
        present = {layer["target"] for layer in layered_source["layers"]}
        excluded, tracks = resolve_visibility(layer_set, config, state_id, present, frame_count)
        if excluded:
            # A layer hidden for the whole state is left out entirely, so no version of
            # the harness has to animate an opacity that never changes.
            layered_source["layers"] = [layer for layer in layered_source["layers"]
                                        if layer["target"] not in excluded]
            layer_files = [item for item in layer_files if item[0] not in excluded]

    plan_spec = compose_plan_spec(config, state_id, layered_source=layered_source,
                                  visibility_tracks=tracks)
    if source_mode == "exact_frames":
        if plan_spec.get("playback") != exact_source["manifest"]["playback"]:
            raise BuildError(f"state {state_id}: effective playback does not match exact frame source")
        declared_canvas = plan_spec.get("canvas")
        expected_canvas = exact_source["manifest"]["canvas"]
        if declared_canvas is not None and (
                declared_canvas.get("width"), declared_canvas.get("height")) != (
                expected_canvas["width"], expected_canvas["height"]):
            raise BuildError(f"state {state_id}: plan canvas does not match exact frame source")
    spec_path = state_build / "plan-spec.json"
    with open(spec_path, "w", encoding="utf-8") as handle:
        json.dump(plan_spec, handle, indent=2, sort_keys=True)
        handle.write("\n")

    build_path = state_build / "build"
    plan_args = ["plan", "--spec", str(spec_path), "--output", str(build_path)]
    if source_mode in ("flattened", "exact_frames"):
        # --source with a layered plan is a harness error (SOURCE_MODE_CONFLICT);
        # layered plans carry their inputs in the inline source object. Exact
        # frames still bind the approved neutral as their trusted source.
        plan_args[3:3] = ["--source", str(source)]
    plan_result = run_harness(harness, plan_args, step=f"plan [{state_id}]")
    if source_mode == "exact_frames":
        frames_dir = build_path / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        for index, frame_path in enumerate(exact_source["frame_paths"]):
            shutil.copyfile(frame_path, frames_dir / f"frame_{index:03d}.png")
    else:
        run_harness(harness, ["render", str(build_path)], step=f"render [{state_id}]")
    validate_result = run_harness(
        harness, ["validate", str(build_path), "--write-qa"], step=f"validate [{state_id}]"
    )
    if not validate_result.get("valid"):
        raise BuildError(f"validation failed for {state_id}: {validate_result.get('errors')}")
    expected = set(config.get("expected_validation_warnings", []))
    unexpected = [w for w in validate_result.get("warnings", []) if w.get("code") not in expected]
    if unexpected:
        raise BuildError(f"unexpected validation warnings for {state_id}: {unexpected}")
    run_harness(harness, ["preview", str(build_path)], step=f"preview [{state_id}]")
    run_harness(harness, ["contact-sheet", str(build_path)], step=f"contact-sheet [{state_id}]")
    report_result = run_harness(harness, ["report", str(build_path)], step=f"report [{state_id}]")
    with open(state_build / "report.json", "w", encoding="utf-8") as handle:
        json.dump(report_result, handle, indent=2, sort_keys=True)
        handle.write("\n")

    if source_mode in ("flattened", "exact_frames"):
        if sha256_file(source) != source_sha_before:
            raise BuildError(f"source sprite changed during build: {source}")
        if source_mode == "exact_frames":
            if sha256_file(exact_source["manifest_path"]) != exact_source["manifest_sha256"]:
                raise BuildError(f"exact frame manifest changed during build: {state_id}")
            for index, path in enumerate(exact_source["frame_paths"]):
                expected = exact_source["manifest"]["frames"][index]["sha256"]
                if sha256_file(path) != expected:
                    raise BuildError(f"exact frame source changed during build: {path}")
    else:
        for layer_id, layer_path, layer_sha in layer_files:
            if sha256_file(layer_path) != layer_sha:
                raise BuildError(
                    f"layer source changed during build: {layer_id} ({layer_path})")

    with open(build_path / "frame-plan.json", "r", encoding="utf-8") as handle:
        frame_plan = json.load(handle)
    frame_files = [frame["file"] for frame in frame_plan["frames"]]
    if not frame_files:
        raise BuildError(f"frame plan declares no frames for {state_id}")
    if source_mode == "exact_frames":
        plan_digest = frame_plan["plan_digest"]
        render_mode = "external"
    else:
        with open(build_path / "render.json", "r", encoding="utf-8") as handle:
            render_manifest = json.load(handle)
        plan_digest = render_manifest["plan_digest"]
        render_mode = render_manifest["mode"]

    return {
        "state": state_id,
        "source_mode": source_mode,
        "build_path": build_path,
        "source": source if source_mode in ("flattened", "exact_frames") else None,
        "source_sha256": source_sha_before,
        "layer_files": [(lid, str(p), sha) for lid, p, sha in layer_files],
        "exact_frame_source": (
            {
                "manifest_path": str(exact_source["manifest_path"]),
                "manifest_sha256": exact_source["manifest_sha256"],
                "frame_durations_ms": exact_source["frame_durations_ms"],
            }
            if source_mode == "exact_frames" else None
        ),
        "plan_spec": plan_spec,
        "plan_digest": plan_digest,
        "render_mode": render_mode,
        "playback": frame_plan["playback"],
        "reduced_motion_mode": frame_plan["reduced_motion"]["mode"],
        "frame_files": frame_files,
        "plan_warnings": [w.get("code") for w in plan_result.get("warnings", [])],
        "validate_warnings": [w.get("code") for w in validate_result.get("warnings", [])],
    }


def make_manifest(build: dict, harness_ver: str, config: dict) -> dict:
    """Compose the deterministic consumer runtime manifest for one state."""
    fps = build["playback"]["fps"]
    exact = build.get("exact_frame_source")
    durations = exact["frame_durations_ms"] if exact else [
        round(1000.0 / fps) for _ in build["frame_files"]
    ]
    frames = []
    for file_name, duration_ms in zip(build["frame_files"], durations, strict=True):
        frame_path = build["build_path"] / file_name
        frames.append(
            {
                "file": file_name,
                "duration_ms": duration_ms,
                "sha256": sha256_file(frame_path),
            }
        )
    reduced_mode = build["reduced_motion_mode"]
    if build.get("source_mode", "flattened") == "layered":
        # Layered v2: the source binding names the authored layer set and pins
        # every layer PNG; base.png stays the static runtime fallback only.
        source_section = {
            "mode": "layered",
            "layer_set": config.get("layer_set"),
            "layers": [
                {"id": layer_id, "sha256": layer_sha}
                for layer_id, _path, layer_sha in build["layer_files"]
            ],
        }
    else:
        source_section = {
            "file": config["source_file"],
            "sha256": build["source_sha256"],
        }
    provenance = {
        "pipeline": "sprite-harness",
        "harness_version": harness_ver,
        "plan_digest": build["plan_digest"],
        "render_mode": build["render_mode"],
        "spec": config_spec_path(config),
        "builder": "tools/build_reimu_animations.py",
    }
    if exact:
        provenance.update(
            {
                "source_mode": "approved_exact_frames",
                "frame_source": os.path.relpath(exact["manifest_path"], start=REPO_ROOT),
                "frame_source_sha256": exact["manifest_sha256"],
            }
        )
    return {
        "manifest_version": MANIFEST_VERSION,
        "character": config["character"],
        "state_set": config["state_set"],
        "state": build["state"],
        "animation_id": build["plan_spec"]["animation_id"],
        "playback": {
            "fps": fps,
            "loop": build["playback"]["loop"],
        },
        "frames": frames,
        "reduced_motion": {
            "mode": reduced_mode,
            "frame": frames[0]["file"],
        },
        "source": source_section,
        "provenance": provenance,
    }


OLD_FRAMES_NAME = "old-frames"
OLD_MANIFEST_NAME = "old-animation.json"
RECOVERY_MARKER_NAME = ".publish-recovery.json"


class StatePublication:
    """One state's staged publication and its commit/rollback bookkeeping.

    `base.png` is immutable source and never part of the transaction: only
    the `frames/` directory and the `animation.json` manifest are replaced.
    """

    def __init__(self, state: str, state_dir: Path, staging: Path, base_sha: str):
        self.state = state
        self.state_dir = state_dir
        self.staging = staging
        self.base_sha = base_sha
        self.moved_old_frames = False
        self.published_frames = False
        self.moved_old_manifest = False
        self.published_manifest = False


def stage_state(build: dict, manifest: dict, publish_root: Path,
                source_file: str) -> StatePublication:
    """Non-destructively stage one state's frames + manifest next to base.png."""
    state_dir = publish_root / build["state"]
    base_png = state_dir / source_file
    if not base_png.is_file():
        raise BuildError(f"publish target has no {source_file}: {state_dir}")
    base_sha = sha256_file(base_png)
    if build.get("source_mode", "flattened") != "layered" and base_sha != build["source_sha256"]:
        raise BuildError(f"publish target {source_file} does not match built source: {state_dir}")

    staging = state_dir / f".publish-staging-{uuid.uuid4().hex}"
    staged_frames = staging / FRAMES_DIR_NAME
    staged_frames.mkdir(parents=True)
    pub = StatePublication(build["state"], state_dir, staging, base_sha)
    try:
        for entry in manifest["frames"]:
            src = build["build_path"] / entry["file"]
            dst = staging / entry["file"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            if sha256_file(dst) != entry["sha256"]:
                raise BuildError(f"staged frame digest mismatch: {dst}")
        staged_manifest = staging / MANIFEST_NAME
        with open(staged_manifest, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return pub


def verify_staged_state(pub: StatePublication) -> None:
    """Re-verify a staged package before any destructive commit begins."""
    staged_manifest = pub.staging / MANIFEST_NAME
    try:
        with open(staged_manifest, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise BuildError(f"staged manifest unreadable for {pub.state}: {error}")
    for entry in manifest["frames"]:
        staged = pub.staging / entry["file"]
        if not staged.is_file() or sha256_file(staged) != entry["sha256"]:
            raise BuildError(f"staged package verification failed for {pub.state}: {entry['file']}")


def commit_state(pub: StatePublication) -> None:
    """Swap the staged generation in. Every step is recorded for rollback."""
    frames_dir = pub.state_dir / FRAMES_DIR_NAME
    manifest_path = pub.state_dir / MANIFEST_NAME
    if frames_dir.exists():
        os.rename(frames_dir, pub.staging / OLD_FRAMES_NAME)
        pub.moved_old_frames = True
    os.rename(pub.staging / FRAMES_DIR_NAME, frames_dir)
    pub.published_frames = True
    if manifest_path.exists():
        os.rename(manifest_path, pub.staging / OLD_MANIFEST_NAME)
        pub.moved_old_manifest = True
    os.replace(pub.staging / MANIFEST_NAME, manifest_path)
    pub.published_manifest = True


def rollback_state(pub: StatePublication) -> None:
    """Undo commit_state in reverse order, restoring the previous generation."""
    frames_dir = pub.state_dir / FRAMES_DIR_NAME
    manifest_path = pub.state_dir / MANIFEST_NAME
    if pub.published_manifest:
        os.rename(manifest_path, pub.staging / MANIFEST_NAME)
        pub.published_manifest = False
    if pub.moved_old_manifest:
        os.rename(pub.staging / OLD_MANIFEST_NAME, manifest_path)
        pub.moved_old_manifest = False
    if pub.published_frames:
        os.rename(frames_dir, pub.staging / FRAMES_DIR_NAME)
        pub.published_frames = False
    if pub.moved_old_frames:
        os.rename(pub.staging / OLD_FRAMES_NAME, frames_dir)
        pub.moved_old_frames = False


def write_recovery_marker(pub: StatePublication, commit_error: BaseException,
                          rollback_error: BaseException) -> Path:
    """Record an explicit recovery marker when rollback itself failed.

    The staging directory is preserved: it still holds the previous
    generation (`old-frames`/`old-animation.json`) and/or the unpublished new
    one. The marker makes the broken state discoverable instead of silently
    claiming success or clean failure.
    """
    marker = pub.state_dir / RECOVERY_MARKER_NAME
    payload = {
        "state": pub.state,
        "staging_dir": pub.staging.name,
        "published_frames": pub.published_frames,
        "moved_old_frames": pub.moved_old_frames,
        "published_manifest": pub.published_manifest,
        "moved_old_manifest": pub.moved_old_manifest,
        "commit_error": str(commit_error),
        "rollback_error": str(rollback_error),
        "recovery": (
            "Restore the previous generation by hand from the staging directory "
            f"({pub.staging.name}: {OLD_FRAMES_NAME!r} -> frames/, "
            f"{OLD_MANIFEST_NAME!r} -> animation.json), then delete the staging "
            "directory and this marker, then run scripts/check-repository.sh."
        ),
    }
    try:
        with open(marker, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except OSError:
        pass  # the preserved staging directory is still the recovery source
    return marker


def publish_set(publications: list[tuple[dict, dict]], publish_root: Path,
                source_file: str) -> None:
    """Publish all states as one logical generation.

    stage everything -> verify the staged package -> commit state by state ->
    on any failure roll back every state changed by this run. After this
    function the publish tree is either entirely the new generation or
    entirely the previous one — never mixed. If rollback itself fails, an
    explicit recovery marker is written, staging is preserved, and the error
    says so; success is never claimed.
    """
    staged: list[StatePublication] = []
    try:
        for build, manifest in publications:
            staged.append(stage_state(build, manifest, publish_root, source_file))
        for pub in staged:
            verify_staged_state(pub)
    except BaseException:
        for pub in staged:
            shutil.rmtree(pub.staging, ignore_errors=True)
        raise

    attempted: list[StatePublication] = []
    try:
        for pub in staged:
            attempted.append(pub)
            commit_state(pub)
    except BaseException as commit_error:
        rollback_failures: list[tuple[StatePublication, BaseException]] = []
        for pub in reversed(attempted):
            try:
                rollback_state(pub)
            except BaseException as rollback_error:
                rollback_failures.append((pub, rollback_error))
                write_recovery_marker(pub, commit_error, rollback_error)
        for pub in staged:
            if not any(p is pub for p, _ in rollback_failures):
                shutil.rmtree(pub.staging, ignore_errors=True)
        if rollback_failures:
            broken = ", ".join(p.state for p, _ in rollback_failures)
            details = "; ".join(f"{p.state}: {e}" for p, e in rollback_failures)
            raise BuildError(
                f"publish failed AND rollback failed for state(s) {broken}. "
                f"The publish tree may be mixed. Recovery markers "
                f"({RECOVERY_MARKER_NAME}) and staging directories were preserved "
                f"in the affected state directories. Rollback errors: {details}. "
                f"Original publish error: {commit_error}"
            ) from commit_error
        raise

    # Success path: base.png must be untouched, staging fully cleaned up.
    for pub in staged:
        if sha256_file(pub.state_dir / source_file) != pub.base_sha:
            raise BuildError(f"{source_file} changed during publish: {pub.state_dir}")
        shutil.rmtree(pub.staging)


def publish_state(build: dict, manifest: dict, publish_root: Path,
                  source_file: str) -> None:
    """Publish a single state as a one-element set transaction."""
    publish_set([(build, manifest)], publish_root, source_file)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                        help="animation set config (default: %(default)s)")
    parser.add_argument("--build-dir", type=Path,
                        help="working directory for harness builds "
                             "(default: build/animations/<character>/<state_set>)")
    parser.add_argument("--harness", help="sprite-harness executable (default: $SPRITE_HARNESS_BIN or PATH)")
    parser.add_argument("--states", nargs="+", help="subset of states to build (default: all)")
    parser.add_argument("--publish-root", type=Path,
                        help="override the publish root (default: from config, repo-relative)")
    parser.add_argument("--no-publish", action="store_true",
                        help="build and validate only; do not touch assets/")
    args = parser.parse_args(argv)

    try:
        harness = find_harness(args.harness)
        config = load_config(args.config)
        build_dir = args.build_dir or default_build_dir(config)
        source_root = (REPO_ROOT / config["source_root"]).resolve()
        publish_root = (args.publish_root or (REPO_ROOT / config["publish_root"])).resolve()
        state_ids = args.states or list(config["states"])

        # A declared layer root is immutable even while every state is flattened.
        layered_states = [s for s in state_ids if state_source_mode(config, s) == "layered"]
        layer_set = None
        layer_root = None
        if layered_states and "layer_set" not in config:
            raise BuildError(
                f"states {layered_states} declare source_mode 'layered' but the "
                "config has no 'layer_set' path")
        if "layer_set" in config:
            layer_set = load_layer_set(REPO_ROOT / config["layer_set"])
            assert_layer_set_binding(layer_set, config)
            layer_root = (REPO_ROOT / layer_set["asset_root"]).resolve()

        exact_sources = {
            state_id: load_exact_frame_source(config, state_id)
            for state_id in state_ids
            if state_source_mode(config, state_id) == "exact_frames"
        }

        # Fail closed before any build: the disposable build area must not
        # alias or overlap the source tree, the publish tree, or any input.
        protected = {"source_root": source_root, "publish_root": publish_root}
        if layer_root is not None:
            protected["layer_root"] = layer_root
        for state_id, exact in exact_sources.items():
            protected[f"exact frame source ({state_id})"] = exact["manifest_path"].parent
        for state_id in state_ids:
            protected[f"source sprite ({state_id})"] = (
                source_root / state_id / config["source_file"])
        assert_build_isolation(build_dir, protected)

        harness_ver = harness_version(harness)
        print(f"sprite-harness: {harness} (version {harness_ver})")
        print(f"states: {', '.join(state_ids)}")

        builds = []
        for state_id in state_ids:
            middle = "external-frames" if state_source_mode(config, state_id) == "exact_frames" else "render"
            print(f"[{state_id}] plan -> {middle} -> validate -> preview -> contact-sheet -> report")
            build = build_state(harness, config, state_id, build_dir, source_root,
                                publish_root=publish_root,
                                layer_set=layer_set, layer_root=layer_root,
                                exact_source=exact_sources.get(state_id))
            builds.append(build)
            print(f"[{state_id}] validated: {len(build['frame_files'])} frame(s), "
                  f"plan_digest {build['plan_digest'][:23]}…, "
                  f"warnings {build['validate_warnings'] or 'none'}")

        if args.no_publish:
            print("publish skipped (--no-publish); validated builds remain under", build_dir)
            return 0

        # All states publish together as one logical generation, or none do.
        publications = [(build, make_manifest(build, harness_ver, config)) for build in builds]
        publish_set(publications, publish_root, config["source_file"])
        for build, manifest in publications:
            print(f"[{build['state']}] published {len(manifest['frames'])} frame(s) + "
                  f"{MANIFEST_NAME} -> {publish_root / build['state']}")
        print("done: all requested states built, validated, and published as one generation")
        return 0
    except BuildError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
