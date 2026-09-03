#!/usr/bin/env python3
"""Build and publish validated Reimu eating-state animations via Sprite Harness.

This is the consumer-side entry point of the animation pipeline:

    animation-set.json (consumer spec)
        -> one Sprite Harness Animation Plan per state
           (source_mode "flattened": plan v1 bound to the immutable base.png;
            source_mode "layered":   plan v2 composed from the explicitly
            authored layer PNGs declared in the layer set, see
            docs/reimu-layered-assets-v1.md)
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
DEFAULT_BUILD_DIR = REPO_ROOT / "build" / "animations" / "reimu" / "eating"

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
CONSUMER_STATE_KEYS = {"source_mode"}


def state_source_mode(config: dict, state_id: str) -> str:
    """The source mode for one state: 'flattened' (v1) or 'layered' (v2)."""
    if state_id not in config["states"]:
        raise BuildError(f"unknown state: {state_id}")
    mode = (config["states"][state_id] or {}).get("source_mode", "flattened")
    if mode not in ("flattened", "layered"):
        raise BuildError(f"unsupported source_mode for {state_id}: {mode!r}")
    return mode


def compose_plan_spec(config: dict, state_id: str, layered_source: dict | None = None) -> dict:
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
    plan["animation_id"] = f"{config['animation_id_prefix']}_{state_id}"
    metadata = dict(plan.get("metadata") or {})
    metadata.update(
        {
            "character": config["character"],
            "state_set": config["state_set"],
            "state": state_id,
            "consumer": config.get("consumer", "gensokyo-codex-pets"),
            "spec": "pets/reimu/animations/eating/animation-set.json",
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
    applicable = []
    for layer in layer_set["layers"]:
        states = layer.get("states")
        if states is not None and state_id not in states:
            continue
        applicable.append(layer)
    if not applicable:
        raise BuildError(f"layer set declares no layers applicable to state {state_id}")
    zs = [layer["z"] for layer in applicable]
    if len(set(zs)) != len(zs):
        raise BuildError(f"duplicate z-order among layers applicable to {state_id}")
    applicable.sort(key=lambda layer: layer["z"])

    source_layers = []
    layer_files: list[tuple[str, Path, str]] = []
    missing = []
    for layer in applicable:
        image_rel = layer["image"].replace("{state}", state_id)
        image_path = layer_root / image_rel
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
                layer_set: dict | None = None, layer_root: Path | None = None) -> dict:
    """Run the full harness pipeline for one state; return build facts.

    A state's `source_mode` selects the input contract: "flattened" (default)
    binds the single immutable base sprite to an Animation Plan v1;
    "layered" composes an Animation Plan v2 inline `source` from the layer
    set's explicitly authored PNGs. Both modes share the same downstream
    pipeline (render → validate → preview → contact-sheet → report).
    """
    source_mode = state_source_mode(config, state_id)
    source = source_root / state_id / config["source_file"]
    protected = {"source_root": source_root, f"source sprite ({state_id})": source}
    if publish_root is not None:
        protected["publish_root"] = publish_root
    if layer_root is not None:
        protected["layer_root"] = layer_root
    assert_build_isolation(build_dir, protected)

    source_sha_before = None
    if source_mode == "flattened":
        if not source.is_file():
            raise BuildError(f"source sprite not found: {source}")
        source_sha_before = sha256_file(source)
    elif layer_set is None or layer_root is None:
        raise BuildError(f"state {state_id} is layered but no layer set / layer root was provided")

    state_build = build_dir / state_id
    if state_build.exists():
        shutil.rmtree(state_build)
    state_build.mkdir(parents=True)

    layered_source = None
    layer_files: list[tuple[str, Path, str]] = []
    if source_mode == "layered":
        layered_source, layer_files = compose_layered_source(
            layer_set, state_id, layer_root, state_build)

    plan_spec = compose_plan_spec(config, state_id, layered_source=layered_source)
    spec_path = state_build / "plan-spec.json"
    with open(spec_path, "w", encoding="utf-8") as handle:
        json.dump(plan_spec, handle, indent=2, sort_keys=True)
        handle.write("\n")

    build_path = state_build / "build"
    plan_args = ["plan", "--spec", str(spec_path), "--output", str(build_path)]
    if source_mode == "flattened":
        # --source with a layered plan is a harness error (SOURCE_MODE_CONFLICT);
        # layered plans carry their inputs in the inline source object.
        plan_args[3:3] = ["--source", str(source)]
    plan_result = run_harness(harness, plan_args, step=f"plan [{state_id}]")
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

    if source_mode == "flattened":
        if sha256_file(source) != source_sha_before:
            raise BuildError(f"source sprite changed during build: {source}")
    else:
        for layer_id, layer_path, layer_sha in layer_files:
            if sha256_file(layer_path) != layer_sha:
                raise BuildError(
                    f"layer source changed during build: {layer_id} ({layer_path})")

    with open(build_path / "frame-plan.json", "r", encoding="utf-8") as handle:
        frame_plan = json.load(handle)
    with open(build_path / "render.json", "r", encoding="utf-8") as handle:
        render_manifest = json.load(handle)
    frame_files = [frame["file"] for frame in frame_plan["frames"]]
    if not frame_files:
        raise BuildError(f"frame plan declares no frames for {state_id}")

    return {
        "state": state_id,
        "source_mode": source_mode,
        "build_path": build_path,
        "source": source if source_mode == "flattened" else None,
        "source_sha256": source_sha_before,
        "layer_files": [(lid, str(p), sha) for lid, p, sha in layer_files],
        "plan_spec": plan_spec,
        "plan_digest": render_manifest["plan_digest"],
        "render_mode": render_manifest["mode"],
        "playback": frame_plan["playback"],
        "reduced_motion_mode": frame_plan["reduced_motion"]["mode"],
        "frame_files": frame_files,
        "plan_warnings": [w.get("code") for w in plan_result.get("warnings", [])],
        "validate_warnings": [w.get("code") for w in validate_result.get("warnings", [])],
    }


def make_manifest(build: dict, harness_ver: str, config: dict) -> dict:
    """Compose the deterministic consumer runtime manifest for one state."""
    fps = build["playback"]["fps"]
    duration_ms = round(1000.0 / fps)
    frames = []
    for file_name in build["frame_files"]:
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
        "provenance": {
            "pipeline": "sprite-harness",
            "harness_version": harness_ver,
            "plan_digest": build["plan_digest"],
            "render_mode": build["render_mode"],
            "spec": "pets/reimu/animations/eating/animation-set.json",
            "builder": "tools/build_reimu_animations.py",
        },
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
    if build.get("source_mode", "flattened") == "flattened" and base_sha != build["source_sha256"]:
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
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR,
                        help="working directory for harness builds (default: %(default)s)")
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
        source_root = (REPO_ROOT / config["source_root"]).resolve()
        publish_root = (args.publish_root or (REPO_ROOT / config["publish_root"])).resolve()
        state_ids = args.states or list(config["states"])

        # Layered states (Animation Plan v2) need the authored layer contract.
        layered_states = [s for s in state_ids if state_source_mode(config, s) == "layered"]
        layer_set = None
        layer_root = None
        if layered_states:
            if "layer_set" not in config:
                raise BuildError(
                    f"states {layered_states} declare source_mode 'layered' but the "
                    "config has no 'layer_set' path")
            layer_set = load_layer_set(REPO_ROOT / config["layer_set"])
            layer_root = (REPO_ROOT / layer_set["asset_root"]).resolve()

        # Fail closed before any build: the disposable build area must not
        # alias or overlap the source tree, the publish tree, or any input.
        protected = {"source_root": source_root, "publish_root": publish_root}
        if layer_root is not None:
            protected["layer_root"] = layer_root
        for state_id in state_ids:
            protected[f"source sprite ({state_id})"] = (
                source_root / state_id / config["source_file"])
        assert_build_isolation(args.build_dir, protected)

        harness_ver = harness_version(harness)
        print(f"sprite-harness: {harness} (version {harness_ver})")
        print(f"states: {', '.join(state_ids)}")

        builds = []
        for state_id in state_ids:
            print(f"[{state_id}] plan -> render -> validate -> preview -> contact-sheet -> report")
            build = build_state(harness, config, state_id, args.build_dir, source_root,
                                publish_root=publish_root,
                                layer_set=layer_set, layer_root=layer_root)
            builds.append(build)
            print(f"[{state_id}] validated: {len(build['frame_files'])} frame(s), "
                  f"plan_digest {build['plan_digest'][:23]}…, "
                  f"warnings {build['validate_warnings'] or 'none'}")

        if args.no_publish:
            print("publish skipped (--no-publish); validated builds remain under", args.build_dir)
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
