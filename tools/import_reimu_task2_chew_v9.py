#!/usr/bin/env python3
"""Import the approved task_2 chew-v9 loop as an exact eating-frame source.

The input must be the pinned, zero-warning Sprite Harness build reviewed by the
maintainer. This writes only the consumer-owned source package under
``pets/reimu/animations/eating/sources``. It never changes the production
animation configuration, runtime animation.json, base.png, or runtime frames;
activation and publication remain separate, explicitly reviewed steps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path


EXPECTED_ANIMATION_ID = "reimu_task2_chew_v9_asymmetric_cheeks_loop"
EXPECTED_PLAN_DIGEST = "sha256:cfe76138b8a10ed738554946f174e5706b485a0cd3ec4edc78bfd75a2e8d39f8"
EXPECTED_SOURCE_SHA256 = "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe"
EXPECTED_MOTHER_SHA256 = "761fa75b07b7f2af9a9b16988d9b8596df726e2bd6dd56ef98d194f9db1d84d1"
EXPECTED_FRAME_SHA256 = (
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
    "9f68dafa729b7923d1d3b536c16b2ce1524c1ecff3816cf8e5030badd4811144",
    "57bf28a96b1680972ace09066f199f22b9d56a6e978cc7f190d6861ecaf6ada8",
    "e203b7adf1064621fab836ec7db7e36ece1523f087fef53f7b03c819b7109d74",
    "5ba18281cae838f0ac899318611fe241fbf7b8ae3942a56724d14e852e58c228",
    "196d1d9e81a442f957c8f6071591df74bbe19d77082bc2af551cc1823e047cdc",
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
    "9f68dafa729b7923d1d3b536c16b2ce1524c1ecff3816cf8e5030badd4811144",
    "57bf28a96b1680972ace09066f199f22b9d56a6e978cc7f190d6861ecaf6ada8",
    "e203b7adf1064621fab836ec7db7e36ece1523f087fef53f7b03c819b7109d74",
    "5ba18281cae838f0ac899318611fe241fbf7b8ae3942a56724d14e852e58c228",
    "196d1d9e81a442f957c8f6071591df74bbe19d77082bc2af551cc1823e047cdc",
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
)
CHEW_PHASES = (
    "neutral", "compress_half", "compress", "cross_mid",
    "puff", "puff_half", "neutral", "neutral",
    "compress_half", "compress", "cross_mid", "puff",
    "puff_half", "neutral", "neutral", "neutral",
)
CANVAS = {"width": 596, "height": 596}
FPS = 10
FRAME_DURATION_MS = 100


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
        raise ImportErrorDetail("Harness animation_id is not the approved task_2 v9 loop")
    if frame_plan.get("plan_digest") != EXPECTED_PLAN_DIGEST:
        raise ImportErrorDetail("Harness plan digest is not the approved task_2 v9 loop")
    if (frame_plan.get("source") or {}).get("sha256") != f"sha256:{EXPECTED_SOURCE_SHA256}":
        raise ImportErrorDetail("Harness source is not the approved mother-locked neutral")
    if frame_plan.get("canvas") != {**CANVAS, "background": "transparent"}:
        raise ImportErrorDetail("Harness canvas contract changed")
    if frame_plan.get("playback") != {"fps": 10.0, "frame_count": 16, "loop": True}:
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
        "prototype": "chew-v9-asymmetric-cheeks",
        "canvas": CANVAS,
        "playback": {"fps": FPS, "frame_count": 16, "loop": True},
        "base": {"file": "base.png", "sha256": EXPECTED_SOURCE_SHA256},
        "frames": [
            {
                "file": f"frames/frame_{index:03d}.png",
                "sha256": digest,
                "duration_ms": FRAME_DURATION_MS,
                "chew_phase": CHEW_PHASES[index],
            }
            for index, digest in enumerate(EXPECTED_FRAME_SHA256)
        ],
        "approval": {
            "source_image": "maintainer selected and confirmed",
            "keyframes": "maintainer confirmed",
            "loop": "maintainer confirmed 2026-09-05",
            "consumer_preflight": "maintainer authorized 2026-09-05",
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
            "description": (
                "two asymmetric closed-mouth compress/puff chewing beats with a "
                "spatially tapered near-cheek contour and smaller far-cheek response"
            ),
            "dynamic_bbox_exclusive": [218, 255, 353, 280],
            "static": [
                "rice ball core", "hands", "sleeves", "body", "hair mass",
                "neck", "collar", "table", "tatami", "eyes", "eyebrows",
                "mouth", "mole", "central face",
            ],
            "pixel_checks": {
                "dynamic_union_pixels": 1071,
                "protected_overlap_pixels": 0,
                "new_rgba_values": 0,
            },
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--harness-build", type=Path, required=True)
    parser.add_argument(
        "--destination", type=Path,
        default=Path("pets/reimu/animations/eating/sources/task_2-chew-v9"),
    )
    args = parser.parse_args()
    try:
        manifest = import_source(args.harness_build.resolve(), args.destination.resolve())
        print(json.dumps({
            "status": "READY_FOR_PREFLIGHT",
            "destination": str(args.destination),
            "frames": len(manifest["frames"]),
            "production_changed": False,
        }, indent=2))
        return 0
    except ImportErrorDetail as error:
        print(f"error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
