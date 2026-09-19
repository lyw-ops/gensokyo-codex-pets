#!/usr/bin/env python3
"""Import the approved chew-v7 exact frames as a Codex v2 running-row source.

The input is a validated Sprite Harness external build. The importer verifies
the approved animation identity and every source-frame digest, selects six
confirmed phases, converts them to 192x208 cells with nearest-neighbor
sampling, and writes a self-contained source manifest plus PNGs.

This tool never edits assets/reimu/eating, never builds a full atlas, and never
installs a pet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from PIL import Image


EXPECTED_ANIMATION_ID = "reimu_task2_chew_v7_mother_locked_loop"
EXPECTED_PLAN_DIGEST = "sha256:247bce2b043342810add830ef11083dbd052064ee84504e7f957350c877d992f"
EXPECTED_SOURCE_SHA256 = "sha256:0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe"
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
SOURCE_LEVELS = (0, 0, 1, 2, 3, 2, 1, 0, 1, 2, 3, 2, 1, 0, 0, 0)
SELECTED_SOURCE_FRAMES = (0, 2, 4, 6, 7, 7)
RUNNING_DURATIONS_MS = (120, 120, 120, 120, 120, 220)
SOURCE_SIZE = (596, 596)
CELL_SIZE = (192, 208)


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


def cell_from_source(frame: Image.Image) -> Image.Image:
    rgba = frame.convert("RGBA")
    if rgba.size != SOURCE_SIZE:
        raise ImportErrorDetail(f"source frame size is {rgba.size}, want {SOURCE_SIZE}")
    scaled = rgba.resize((192, 192), Image.Resampling.NEAREST)
    cell = Image.new("RGBA", CELL_SIZE, (0, 0, 0, 0))
    cell.alpha_composite(scaled, (0, 16))
    return cell


def verify_harness_build(build: Path) -> list[Path]:
    frame_plan = read_json(build / "frame-plan.json")
    qa = read_json(build / "qa" / "frames.qa.json")
    if frame_plan.get("animation_id") != EXPECTED_ANIMATION_ID:
        raise ImportErrorDetail("Harness animation_id is not the approved chew-v7 loop")
    if frame_plan.get("plan_digest") != EXPECTED_PLAN_DIGEST:
        raise ImportErrorDetail("Harness plan digest is not the approved chew-v7 loop")
    if (frame_plan.get("source") or {}).get("sha256") != EXPECTED_SOURCE_SHA256:
        raise ImportErrorDetail("Harness source digest is not the approved mother-locked source")
    playback = frame_plan.get("playback") or {}
    if playback.get("frame_count") != 16 or playback.get("fps") != 10.0 or playback.get("loop") is not True:
        raise ImportErrorDetail("Harness playback contract changed")
    if qa.get("valid") is not True or qa.get("errors") != [] or qa.get("warnings") != []:
        raise ImportErrorDetail("Harness frame QA is not valid with zero errors/warnings")

    frames = [build / "frames" / f"frame_{index:03d}.png" for index in range(16)]
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
            "row": "running",
            "row_index": 7,
            "cell": {"width": 192, "height": 208},
            "columns": 8,
            "used_columns": 6,
            "durations_ms": list(RUNNING_DURATIONS_MS),
        },
        "action": "work_eating",
        "prototype": "chew-v7-mother-locked",
        "approval": {
            "keyframes": "maintainer confirmed",
            "loop": "maintainer confirmed",
            "consumer_integration": "maintainer authorized 2026-09-04",
        },
        "provenance": {
            "source_kind": "maintainer-provided source image; maintainer confirmed and authorized its use for this project",
            "mother_sha256": EXPECTED_MOTHER_SHA256,
            "harness_animation_id": EXPECTED_ANIMATION_ID,
            "harness_plan_digest": EXPECTED_PLAN_DIGEST,
            "harness_source_sha256": EXPECTED_SOURCE_SHA256.removeprefix("sha256:"),
            "harness_version": "0.7.0",
            "pixel_policy": "nearest-neighbor 596x596 to 192x192; bottom-aligned at (0,16) in a transparent 192x208 cell",
        },
        "motion": {
            "source_frame_indices": list(SELECTED_SOURCE_FRAMES),
            "source_levels": [SOURCE_LEVELS[index] for index in SELECTED_SOURCE_FRAMES],
            "description": "fixed pose; one restrained neutral-to-puff-to-neutral cheek/jaw chew; food, hands, body, eyes, table and tatami remain fixed",
        },
        "frames": frame_entries,
        "limitations": [
            "This is one approved Codex standard row, not a complete or installable pet atlas.",
            "Codex selects the running row for working activity; the current custom-pet manifest exposes no active-task count and cannot select task_2.",
            "The source does not replace assets/reimu/eating/task_2/base.png or its runtime animation.",
        ],
    }


def import_frames(build: Path, destination: Path) -> dict:
    source_paths = verify_harness_build(build)
    destination_parent = destination.parent
    destination_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.import-", dir=destination_parent))
    try:
        frame_entries = []
        source_palette = set()
        source_images = []
        for path in source_paths:
            image = Image.open(path).convert("RGBA")
            source_images.append(image)
            source_palette.update(pixel for pixel in image.get_flattened_data() if pixel[3] > 0)

        for output_index, (source_index, duration_ms) in enumerate(
            zip(SELECTED_SOURCE_FRAMES, RUNNING_DURATIONS_MS, strict=True)
        ):
            cell = cell_from_source(source_images[source_index])
            cell_palette = {pixel for pixel in cell.get_flattened_data() if pixel[3] > 0}
            if not cell_palette.issubset(source_palette):
                raise ImportErrorDetail("nearest-neighbor conversion introduced a visible RGBA value")
            output_path = staging / f"frame_{output_index:03d}.png"
            cell.save(output_path, format="PNG", optimize=False)
            frame_entries.append(
                {
                    "file": output_path.name,
                    "sha256": sha256(output_path),
                    "duration_ms": duration_ms,
                    "source_frame": source_index,
                    "chew_level": SOURCE_LEVELS[source_index],
                }
            )

        if (staging / "frame_000.png").read_bytes() != (staging / "frame_004.png").read_bytes():
            raise ImportErrorDetail("running row does not return to the neutral source")
        if (staging / "frame_000.png").read_bytes() != (staging / "frame_005.png").read_bytes():
            raise ImportErrorDetail("running row endpoint is not the neutral source")

        manifest = source_manifest(frame_entries)
        (staging / "source.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        expected_files = {"source.json", *(entry["file"] for entry in frame_entries)}
        if destination.exists():
            actual_files = {path.name for path in destination.iterdir() if path.is_file()}
            if actual_files != expected_files:
                raise ImportErrorDetail(
                    f"destination already exists with a different file set: {destination}"
                )
            for name in expected_files:
                if (destination / name).read_bytes() != (staging / name).read_bytes():
                    raise ImportErrorDetail(
                        f"destination already exists with different bytes: {destination / name}"
                    )
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
        default=Path("pets/reimu/sprites/codex-v2/rows/running"),
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
