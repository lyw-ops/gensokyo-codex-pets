#!/usr/bin/env python3
"""Import the approved task_2 chew-v7 loop as an exact eating-frame source.

The input must be the pinned, zero-warning Sprite Harness build reviewed by the
maintainer. By default this writes only the consumer-owned source package under
``pets/reimu/animations/eating/sources``. ``--activate-base`` additionally
switches task_2's static fallback to the approved neutral frame while retaining
the preceding Eating Set v1 fallback as a byte-exact legacy PNG.

This tool never publishes animation.json or runtime frames; publication remains
the responsibility of tools/build_reimu_animations.py after validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path


EXPECTED_ANIMATION_ID = "reimu_task2_chew_v7_mother_locked_loop"
EXPECTED_PLAN_DIGEST = "sha256:247bce2b043342810add830ef11083dbd052064ee84504e7f957350c877d992f"
EXPECTED_SOURCE_SHA256 = "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe"
EXPECTED_PREVIOUS_BASE_SHA256 = "d3139f4ecc428235b4bfd3d227be760cb151d7d3da126f78cfa0923b5ec7ee4d"
EXPECTED_MOTHER_SHA256 = "761fa75b07b7f2af9a9b16988d9b8596df726e2bd6dd56ef98d194f9db1d84d1"
EXPECTED_FRAME_SHA256 = (
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
    "792e359604168a60a4c759144fecd7cc28770280b31c1bf476e1993ff9fe24af",
    "547501f124f1d993bc7149b927fb71a97f7550ed6e1b5b18d81ca2dc68c21278",
    "b9174427f6d0675353270e0a56c6c26175c64b3c520e9a8b766dd3535d59574b",
    "547501f124f1d993bc7149b927fb71a97f7550ed6e1b5b18d81ca2dc68c21278",
    "792e359604168a60a4c759144fecd7cc28770280b31c1bf476e1993ff9fe24af",
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
    "792e359604168a60a4c759144fecd7cc28770280b31c1bf476e1993ff9fe24af",
    "547501f124f1d993bc7149b927fb71a97f7550ed6e1b5b18d81ca2dc68c21278",
    "b9174427f6d0675353270e0a56c6c26175c64b3c520e9a8b766dd3535d59574b",
    "547501f124f1d993bc7149b927fb71a97f7550ed6e1b5b18d81ca2dc68c21278",
    "792e359604168a60a4c759144fecd7cc28770280b31c1bf476e1993ff9fe24af",
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
)
LEVELS = (0, 0, 1, 2, 3, 2, 1, 0, 1, 2, 3, 2, 1, 0, 0, 0)
CANVAS = {"width": 596, "height": 596}
FPS = 10
FRAME_DURATION_MS = 100
LEGACY_NAME = "base-eating-set-v1-legacy.png"


class ImportErrorDetail(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ImportErrorDetail(f"cannot read JSON {path}: {error}") from error


def verify_harness_build(build: Path) -> list[Path]:
    frame_plan = read_json(build / "frame-plan.json")
    qa = read_json(build / "qa" / "frames.qa.json")
    if frame_plan.get("animation_id") != EXPECTED_ANIMATION_ID:
        raise ImportErrorDetail("Harness animation_id is not the approved task_2 loop")
    if frame_plan.get("plan_digest") != EXPECTED_PLAN_DIGEST:
        raise ImportErrorDetail("Harness plan digest is not the approved task_2 loop")
    if (frame_plan.get("source") or {}).get("sha256") != f"sha256:{EXPECTED_SOURCE_SHA256}":
        raise ImportErrorDetail("Harness source is not the approved mother-locked neutral")
    if frame_plan.get("canvas") != {**CANVAS, "background": "transparent"}:
        raise ImportErrorDetail("Harness canvas contract changed")
    playback = frame_plan.get("playback") or {}
    if playback != {"fps": 10.0, "frame_count": 16, "loop": True}:
        raise ImportErrorDetail("Harness playback contract changed")
    if qa.get("valid") is not True or qa.get("errors") != [] or qa.get("warnings") != []:
        raise ImportErrorDetail("Harness frame QA is not valid with zero errors/warnings")

    paths = [build / "frames" / f"frame_{index:03d}.png" for index in range(16)]
    for index, (path, expected) in enumerate(zip(paths, EXPECTED_FRAME_SHA256, strict=True)):
        if not path.is_file() or sha256(path) != expected:
            raise ImportErrorDetail(f"Harness frame {index} is missing or digest-mismatched")
    if paths[0].read_bytes() != paths[-1].read_bytes():
        raise ImportErrorDetail("approved loop endpoints are not byte-identical neutral frames")
    return paths


def make_manifest() -> dict:
    return {
        "exact_frame_source_version": 1,
        "character": "reimu",
        "state_set": "eating",
        "state": "task_2",
        "prototype": "chew-v7-mother-locked",
        "canvas": CANVAS,
        "playback": {"fps": FPS, "frame_count": 16, "loop": True},
        "base": {"file": "base.png", "sha256": EXPECTED_SOURCE_SHA256},
        "frames": [
            {
                "file": f"frames/frame_{index:03d}.png",
                "sha256": digest,
                "duration_ms": FRAME_DURATION_MS,
                "chew_level": LEVELS[index],
            }
            for index, digest in enumerate(EXPECTED_FRAME_SHA256)
        ],
        "approval": {
            "source_image": "maintainer selected and confirmed",
            "keyframes": "maintainer confirmed",
            "loop": "maintainer confirmed",
            "consumer_work": "maintainer authorized 2026-09-04",
        },
        "provenance": {
            "mother_sha256": EXPECTED_MOTHER_SHA256,
            "harness_animation_id": EXPECTED_ANIMATION_ID,
            "harness_plan_digest": EXPECTED_PLAN_DIGEST,
            "harness_source_sha256": EXPECTED_SOURCE_SHA256,
            "harness_version": "0.7.0",
            "pixel_policy": "exact 596x596 approved Harness frames; no resampling or repaint in consumer",
        },
        "motion": {
            "description": "two restrained one-sided jaw/cheek chewing pulses",
            "dynamic_bbox_exclusive": [314, 269, 347, 280],
            "static": [
                "rice ball", "hands", "sleeves", "body", "hair", "neck",
                "collar", "table", "eyes", "mouth", "mole",
            ],
        },
    }


def import_source(build: Path, destination: Path) -> dict:
    frames = verify_harness_build(build)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.import-", dir=destination.parent))
    try:
        (staging / "frames").mkdir()
        shutil.copyfile(frames[0], staging / "base.png")
        for index, source in enumerate(frames):
            shutil.copyfile(source, staging / "frames" / f"frame_{index:03d}.png")
        manifest = make_manifest()
        (staging / "source.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        expected = {"base.png", "source.json", *(f"frames/frame_{i:03d}.png" for i in range(16))}
        if destination.exists():
            actual = {
                str(path.relative_to(destination))
                for path in destination.rglob("*") if path.is_file()
            }
            if actual != expected:
                raise ImportErrorDetail(f"existing source package has a different file set: {destination}")
            for relative in expected:
                if (destination / relative).read_bytes() != (staging / relative).read_bytes():
                    raise ImportErrorDetail(f"existing source package differs: {destination / relative}")
            return manifest

        os.rename(staging, destination)
        staging = None
        return manifest
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)


def activate_base(source_dir: Path, runtime_state_dir: Path) -> None:
    approved = source_dir / "base.png"
    if sha256(approved) != EXPECTED_SOURCE_SHA256:
        raise ImportErrorDetail("imported source base is not the approved neutral")
    runtime_base = runtime_state_dir / "base.png"
    if not runtime_base.is_file():
        raise ImportErrorDetail(f"runtime base is missing: {runtime_base}")
    current_sha = sha256(runtime_base)
    if current_sha not in (EXPECTED_PREVIOUS_BASE_SHA256, EXPECTED_SOURCE_SHA256):
        raise ImportErrorDetail(f"refusing to replace an unknown task_2 base: {current_sha}")

    legacy = runtime_state_dir / LEGACY_NAME
    if legacy.exists() and sha256(legacy) != EXPECTED_PREVIOUS_BASE_SHA256:
        raise ImportErrorDetail(f"legacy base exists with unexpected bytes: {legacy}")
    if current_sha == EXPECTED_PREVIOUS_BASE_SHA256 and not legacy.exists():
        shutil.copyfile(runtime_base, legacy)
    if current_sha != EXPECTED_SOURCE_SHA256:
        temporary = runtime_state_dir / ".base-chew-v7-activation.png"
        shutil.copyfile(approved, temporary)
        if sha256(temporary) != EXPECTED_SOURCE_SHA256:
            temporary.unlink(missing_ok=True)
            raise ImportErrorDetail("staged runtime base digest mismatch")
        os.replace(temporary, runtime_base)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--harness-build", type=Path, required=True)
    parser.add_argument(
        "--destination", type=Path,
        default=Path("pets/reimu/animations/eating/sources/task_2-chew-v7"),
    )
    parser.add_argument("--activate-base", action="store_true")
    parser.add_argument(
        "--runtime-state-dir", type=Path,
        default=Path("assets/reimu/eating/task_2"),
    )
    args = parser.parse_args()
    try:
        manifest = import_source(args.harness_build.resolve(), args.destination.resolve())
        if args.activate_base:
            activate_base(args.destination.resolve(), args.runtime_state_dir.resolve())
        print(json.dumps({
            "status": "READY",
            "destination": str(args.destination),
            "frames": len(manifest["frames"]),
            "base_activated": args.activate_base,
        }, indent=2))
        return 0
    except ImportErrorDetail as error:
        print(f"error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
