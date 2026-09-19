#!/usr/bin/env python3
"""Import the approved review-v1 exact frames as a Codex v2 review-row source.

The input must be the confirmed Sprite Harness build. The importer pins its
identity and all six 596px frame digests, converts with nearest-neighbor
sampling, and writes six 192x208 RGBA cells plus provenance. It never edits
the eating runtime, builds a full atlas, or installs a pet.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from PIL import Image

try:
    from tools.import_reimu_chew_v7_running import (
        ImportErrorDetail,
        cell_from_source,
        read_json,
        sha256,
    )
except ModuleNotFoundError:  # Direct execution: python tools/import_reimu_review_v1.py
    from import_reimu_chew_v7_running import (
        ImportErrorDetail,
        cell_from_source,
        read_json,
        sha256,
    )


EXPECTED_ANIMATION_ID = "reimu_codex_v2_review_v1_focused_brow_loop"
EXPECTED_PLAN_DIGEST = "sha256:38e04c4b925ea0c6b836f8d7a31688a317c639ac0d1044a0c88abe4e8a66bb09"
EXPECTED_SOURCE_SHA256 = "sha256:0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe"
EXPECTED_FRAME_SHA256 = (
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
    "725dc00103ec506a94363946469a35b805614eb772bdfc578d3c75f50e4ab2e3",
    "ecfcbad61af77382d6a00fcfe8ad76dec9c9c06da49c6615c3e843851e0c94b7",
    "ecfcbad61af77382d6a00fcfe8ad76dec9c9c06da49c6615c3e843851e0c94b7",
    "725dc00103ec506a94363946469a35b805614eb772bdfc578d3c75f50e4ab2e3",
    "0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe",
)
SOURCE_LEVELS = (0, 1, 2, 2, 1, 0)
REVIEW_DURATIONS_MS = (150, 150, 150, 150, 150, 280)


def verify_harness_build(build: Path) -> list[Path]:
    frame_plan = read_json(build / "frame-plan.json")
    qa = read_json(build / "qa" / "frames.qa.json")
    if frame_plan.get("animation_id") != EXPECTED_ANIMATION_ID:
        raise ImportErrorDetail("Harness animation_id is not the approved review-v1 loop")
    if frame_plan.get("plan_digest") != EXPECTED_PLAN_DIGEST:
        raise ImportErrorDetail("Harness plan digest is not the approved review-v1 loop")
    if (frame_plan.get("source") or {}).get("sha256") != EXPECTED_SOURCE_SHA256:
        raise ImportErrorDetail("Harness source digest is not the approved mother-locked source")
    playback = frame_plan.get("playback") or {}
    if playback.get("frame_count") != 6 or playback.get("fps") != 6.0 or playback.get("loop") is not True:
        raise ImportErrorDetail("Harness review playback contract changed")
    if qa.get("valid") is not True or qa.get("errors") != [] or qa.get("warnings") != []:
        raise ImportErrorDetail("Harness frame QA is not valid with zero errors/warnings")

    frames = [build / "frames" / f"frame_{index:03d}.png" for index in range(6)]
    for index, (path, expected) in enumerate(zip(frames, EXPECTED_FRAME_SHA256, strict=True)):
        if not path.is_file():
            raise ImportErrorDetail(f"missing Harness source frame {index}: {path}")
        actual = sha256(path)
        if actual != expected:
            raise ImportErrorDetail(f"Harness source frame {index} digest changed: {actual}")
    return frames


def source_manifest(frame_entries: list[dict]) -> dict:
    return {
        "row_source_version": 1,
        "character": "reimu",
        "codex_contract": {
            "sprite_version": 2,
            "row": "review",
            "row_index": 8,
            "cell": {"width": 192, "height": 208},
            "columns": 8,
            "used_columns": 6,
            "durations_ms": list(REVIEW_DURATIONS_MS),
        },
        "action": "review_task_slip",
        "prototype": "review-v1-mother-locked-focused-brow",
        "approval": {
            "keyframes": "maintainer confirmed 2026-09-04 after residual-line correction",
            "loop": "maintainer confirmed 2026-09-04",
            "consumer_integration": "maintainer authorized 2026-09-04",
        },
        "provenance": {
            "source_kind": "maintainer-provided source image; confirmed and authorized for this project",
            "harness_animation_id": EXPECTED_ANIMATION_ID,
            "harness_plan_digest": EXPECTED_PLAN_DIGEST,
            "harness_source_sha256": EXPECTED_SOURCE_SHA256.removeprefix("sha256:"),
            "harness_version": "0.7.0",
            "pixel_policy": "nearest-neighbor 596x596 to 192x192; bottom-aligned at (0,16) in a transparent 192x208 cell",
        },
        "motion": {
            "source_frame_indices": list(range(6)),
            "source_levels": list(SOURCE_LEVELS),
            "description": "fixed seated eating pose; only the complete image-right eyebrow and its immediate skin band lower uniformly by 1-2px and return; the original brow position is fully cleared with source skin so no residual line remains; eye interiors, eyelids, lashes, food, hands, body, tea, table and tatami remain fixed",
        },
        "frames": frame_entries,
        "limitations": [
            "This is one approved Codex standard row, not a complete or installable pet atlas.",
            "The current review pilot communicates focused inspection with the eyebrow micro-loop only; the earlier task-slip reading and nod remain future design-layer options.",
            "The source does not replace assets/reimu/eating or modify the task-count runtime.",
        ],
    }


def import_frames(build: Path, destination: Path) -> dict:
    source_paths = verify_harness_build(build)
    destination_parent = destination.parent
    destination_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.import-", dir=destination_parent))
    try:
        source_images = [Image.open(path).convert("RGBA") for path in source_paths]
        source_palette = {
            pixel
            for image in source_images
            for pixel in image.get_flattened_data()
            if pixel[3] > 0
        }
        frame_entries = []
        for index, (image, level, duration_ms) in enumerate(
            zip(source_images, SOURCE_LEVELS, REVIEW_DURATIONS_MS, strict=True)
        ):
            cell = cell_from_source(image)
            cell_palette = {pixel for pixel in cell.get_flattened_data() if pixel[3] > 0}
            if not cell_palette.issubset(source_palette):
                raise ImportErrorDetail("nearest-neighbor conversion introduced a visible RGBA value")
            output_path = staging / f"frame_{index:03d}.png"
            cell.save(output_path, format="PNG", optimize=False)
            frame_entries.append(
                {
                    "file": output_path.name,
                    "sha256": sha256(output_path),
                    "duration_ms": duration_ms,
                    "source_frame": index,
                    "brow_lower_level": level,
                }
            )

        if (staging / "frame_000.png").read_bytes() != (staging / "frame_005.png").read_bytes():
            raise ImportErrorDetail("review row endpoints are not pixel-identical neutral frames")
        if (staging / "frame_001.png").read_bytes() != (staging / "frame_004.png").read_bytes():
            raise ImportErrorDetail("review row intermediate brow frames are not symmetric")
        if (staging / "frame_002.png").read_bytes() != (staging / "frame_003.png").read_bytes():
            raise ImportErrorDetail("review row peak brow frames are not held pixel-identically")

        manifest = source_manifest(frame_entries)
        (staging / "source.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        expected_files = {"source.json", *(entry["file"] for entry in frame_entries)}
        if destination.exists():
            actual_files = {path.name for path in destination.iterdir() if path.is_file()}
            if actual_files != expected_files:
                raise ImportErrorDetail(f"destination already exists with a different file set: {destination}")
            for name in expected_files:
                if (destination / name).read_bytes() != (staging / name).read_bytes():
                    raise ImportErrorDetail(f"destination already exists with different bytes: {destination / name}")
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
        "--destination",
        type=Path,
        default=Path("pets/reimu/sprites/codex-v2/rows/review"),
    )
    args = parser.parse_args()
    try:
        manifest = import_frames(args.harness_build.resolve(), args.destination.resolve())
        print(json.dumps({"status": "READY", "destination": str(args.destination), "frames": len(manifest["frames"])}, indent=2))
        return 0
    except ImportErrorDetail as error:
        print(f"error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
