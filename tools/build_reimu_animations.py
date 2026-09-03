#!/usr/bin/env python3
"""Build and publish validated Reimu eating-state animations via Sprite Harness.

This is the consumer-side entry point of the animation pipeline:

    animation-set.json (consumer spec)
        -> one Sprite Harness Animation Plan per state
        -> sprite-harness plan / render / validate --write-qa / preview /
           contact-sheet / report        (public CLI, JSON mode, exit codes)
        -> publish validated frames + a runtime animation.json manifest
           next to each state's immutable base.png

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


def compose_plan_spec(config: dict, state_id: str) -> dict:
    """Deterministically expand one state into a legal Animation Plan spec.

    State entries may override any of the default plan sections; the merge is
    per top-level key (no deep merging inside a section, so an override is
    always a complete, reviewable section).
    """
    if state_id not in config["states"]:
        raise BuildError(f"unknown state: {state_id}")
    overrides = config["states"][state_id] or {}
    plan: dict = copy.deepcopy(config["defaults"])
    for key, value in overrides.items():
        plan[key] = copy.deepcopy(value)
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
                source_root: Path) -> dict:
    """Run the full harness pipeline for one state; return build facts."""
    source = source_root / state_id / config["source_file"]
    if not source.is_file():
        raise BuildError(f"source sprite not found: {source}")
    source_sha_before = sha256_file(source)

    state_build = build_dir / state_id
    if state_build.exists():
        shutil.rmtree(state_build)
    state_build.mkdir(parents=True)

    plan_spec = compose_plan_spec(config, state_id)
    spec_path = state_build / "plan-spec.json"
    with open(spec_path, "w", encoding="utf-8") as handle:
        json.dump(plan_spec, handle, indent=2, sort_keys=True)
        handle.write("\n")

    build_path = state_build / "build"
    plan_result = run_harness(
        harness,
        ["plan", "--spec", str(spec_path), "--source", str(source), "--output", str(build_path)],
        step=f"plan [{state_id}]",
    )
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

    if sha256_file(source) != source_sha_before:
        raise BuildError(f"source sprite changed during build: {source}")

    with open(build_path / "frame-plan.json", "r", encoding="utf-8") as handle:
        frame_plan = json.load(handle)
    with open(build_path / "render.json", "r", encoding="utf-8") as handle:
        render_manifest = json.load(handle)
    frame_files = [frame["file"] for frame in frame_plan["frames"]]
    if not frame_files:
        raise BuildError(f"frame plan declares no frames for {state_id}")

    return {
        "state": state_id,
        "build_path": build_path,
        "source": source,
        "source_sha256": source_sha_before,
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
        "source": {
            "file": config["source_file"],
            "sha256": build["source_sha256"],
        },
        "provenance": {
            "pipeline": "sprite-harness",
            "harness_version": harness_ver,
            "plan_digest": build["plan_digest"],
            "render_mode": build["render_mode"],
            "spec": "pets/reimu/animations/eating/animation-set.json",
            "builder": "tools/build_reimu_animations.py",
        },
    }


def publish_state(build: dict, manifest: dict, publish_root: Path,
                  source_file: str) -> None:
    """Atomically-as-possible publish frames + manifest next to base.png.

    Everything is staged inside the state directory first; the old frame set
    is moved aside, the new one moved in, and the manifest replaced last. On
    any failure the previous frame set is restored and staging is removed, so
    the state directory never ends up half-published.
    """
    state_dir = publish_root / build["state"]
    base_png = state_dir / source_file
    if not base_png.is_file():
        raise BuildError(f"publish target has no {source_file}: {state_dir}")
    base_sha = sha256_file(base_png)
    if base_sha != build["source_sha256"]:
        raise BuildError(f"publish target {source_file} does not match built source: {state_dir}")

    staging = state_dir / f".publish-staging-{uuid.uuid4().hex}"
    staged_frames = staging / FRAMES_DIR_NAME
    staged_frames.mkdir(parents=True)
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

        frames_dir = state_dir / FRAMES_DIR_NAME
        old_frames = staging / "old-frames"
        had_old = frames_dir.exists()
        published_frames = False
        if had_old:
            os.rename(frames_dir, old_frames)
        try:
            os.rename(staged_frames, frames_dir)
            published_frames = True
            os.replace(staged_manifest, state_dir / MANIFEST_NAME)
        except BaseException:
            # Restore the previous complete generation before dropping staging.
            if published_frames:
                os.rename(frames_dir, staged_frames)
            if had_old:
                os.rename(old_frames, frames_dir)
            raise
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    shutil.rmtree(staging)

    if sha256_file(base_png) != base_sha:
        raise BuildError(f"{source_file} changed during publish: {state_dir}")


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

        harness_ver = harness_version(harness)
        print(f"sprite-harness: {harness} (version {harness_ver})")
        print(f"states: {', '.join(state_ids)}")

        builds = []
        for state_id in state_ids:
            print(f"[{state_id}] plan -> render -> validate -> preview -> contact-sheet -> report")
            build = build_state(harness, config, state_id, args.build_dir, source_root)
            builds.append(build)
            print(f"[{state_id}] validated: {len(build['frame_files'])} frame(s), "
                  f"plan_digest {build['plan_digest'][:23]}…, "
                  f"warnings {build['validate_warnings'] or 'none'}")

        if args.no_publish:
            print("publish skipped (--no-publish); validated builds remain under", args.build_dir)
            return 0

        for build in builds:
            manifest = make_manifest(build, harness_ver, config)
            publish_state(build, manifest, publish_root, config["source_file"])
            print(f"[{build['state']}] published {len(manifest['frames'])} frame(s) + "
                  f"{MANIFEST_NAME} -> {publish_root / build['state']}")
        print("done: all requested states built, validated, and published")
        return 0
    except BuildError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
