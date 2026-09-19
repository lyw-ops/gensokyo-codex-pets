#!/usr/bin/env python3
"""Build and validate Reimu's approved Codex v2 waiting-row source.

The tool follows the same public Sprite Harness workflow as the existing row
pilots and produces only a validated 1536x208 row strip under build/. It never
creates a placeholder full atlas, pet manifest, or installation.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

try:
    from tools.build_reimu_codex_running_row import (
        BuildError,
        find_harness,
        read_json,
        run_harness,
        sha256,
        write_json,
    )
except ModuleNotFoundError:  # Direct execution: python tools/build_reimu_codex_waiting_row.py
    from build_reimu_codex_running_row import (
        BuildError,
        find_harness,
        read_json,
        run_harness,
        sha256,
        write_json,
    )


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "pets/reimu/sprites/codex-v2/rows/waiting"
DEFAULT_BUILD = REPO_ROOT / "build/codex-v2/reimu-waiting-row"
EXPECTED_DURATIONS = [150, 150, 150, 150, 150, 260]


def validate_source(source_dir: Path) -> dict:
    manifest = read_json(source_dir / "source.json")
    contract = manifest.get("codex_contract") or {}
    if manifest.get("row_source_version") != 1:
        raise BuildError("unsupported row_source_version")
    if manifest.get("character") != "reimu" or contract.get("row") != "waiting":
        raise BuildError("source semantic binding must be reimu/waiting")
    if contract.get("sprite_version") != 2 or contract.get("row_index") != 6:
        raise BuildError("source is not bound to Codex v2 row 6")
    if contract.get("cell") != {"width": 192, "height": 208}:
        raise BuildError("source cell contract changed")
    if contract.get("columns") != 8 or contract.get("used_columns") != 6:
        raise BuildError("source row column contract changed")
    if contract.get("durations_ms") != EXPECTED_DURATIONS:
        raise BuildError("source waiting-row durations changed")
    frames = manifest.get("frames") or []
    if len(frames) != 6:
        raise BuildError("waiting row must declare six source frames")

    declared = set()
    for index, frame in enumerate(frames):
        expected_name = f"frame_{index:03d}.png"
        if frame.get("file") != expected_name:
            raise BuildError(f"source frame {index} is not {expected_name}")
        if frame.get("duration_ms") != EXPECTED_DURATIONS[index]:
            raise BuildError(f"source frame {index} duration changed")
        path = source_dir / expected_name
        if not path.is_file() or sha256(path) != frame.get("sha256"):
            raise BuildError(f"source frame {index} missing or digest-mismatched")
        with Image.open(path) as image:
            if image.size != (192, 208) or image.mode != "RGBA":
                raise BuildError(f"source frame {index} must be 192x208 RGBA")
            alpha = image.getchannel("A")
            if alpha.getbbox() is None or alpha.getextrema()[0] != 0:
                raise BuildError(f"source frame {index} must have visible content and transparency")
        declared.add(expected_name)
    actual = {path.name for path in source_dir.glob("*.png")}
    if actual != declared:
        raise BuildError(f"undeclared PNGs in waiting source: {sorted(actual - declared)}")
    if (source_dir / "frame_000.png").read_bytes() != (source_dir / "frame_005.png").read_bytes():
        raise BuildError("waiting row endpoints must be pixel-identical neutral frames")
    if (source_dir / "frame_001.png").read_bytes() != (source_dir / "frame_004.png").read_bytes():
        raise BuildError("waiting row intermediate brow frames must be pixel-identical")
    if (source_dir / "frame_002.png").read_bytes() != (source_dir / "frame_003.png").read_bytes():
        raise BuildError("waiting row peak brow frames must be pixel-identical")
    return manifest


def plan_spec() -> dict:
    return {
        "plan_version": 1,
        "animation_id": "reimu_codex_v2_waiting_attentive_brow_v1",
        "canvas": {"width": 192, "height": 208, "background": "transparent"},
        "playback": {"fps": 5.9405940594059405, "frame_count": 6, "loop": True},
        "anchor": {"type": "custom", "x": 0.5, "y": 1.0},
        "reduced_motion": {"mode": "hold_first_frame"},
        "tracks": [],
        "events": [
            {
                "event_id": "attentive_brow_peak",
                "type": "pose_phase",
                "target": "image_right_eyebrow",
                "frames": [2, 3],
            }
        ],
        "metadata": {
            "character": "reimu",
            "consumer": "gensokyo-codex-pets",
            "codex_row": "waiting",
            "prototype": "waiting-v1-mother-locked-attentive-brow",
            "source_mode": "approved_exact_frames",
            "codex_durations_ms": EXPECTED_DURATIONS,
        },
    }


def export_spec() -> dict:
    return {
        "export_version": 1,
        "clips": [{"id": "waiting", "build": "build"}],
        "grid": {
            "cell_width": 192,
            "cell_height": 208,
            "columns": 8,
            "rows": 1,
            "padding": 0,
        },
    }


def verify_row_atlas(atlas_path: Path, source_dir: Path) -> dict:
    with Image.open(atlas_path) as opened:
        atlas = opened.convert("RGBA")
    if atlas.size != (1536, 208):
        raise BuildError(f"row atlas size is {atlas.size}, want 1536x208")
    for index in range(6):
        with Image.open(source_dir / f"frame_{index:03d}.png") as opened:
            expected = opened.convert("RGBA")
        actual = atlas.crop((index * 192, 0, (index + 1) * 192, 208))
        if actual.tobytes() != expected.tobytes():
            raise BuildError(f"row atlas cell {index} differs from source")
    unused = atlas.crop((6 * 192, 0, 8 * 192, 208))
    if unused.getchannel("A").getbbox() is not None:
        raise BuildError("unused waiting-row cells are not fully transparent")
    return {
        "path": "row-atlas/atlas.png",
        "sha256": sha256(atlas_path),
        "size": [1536, 208],
        "used_cells_exact": True,
        "unused_cells_fully_transparent": True,
    }


def build_waiting_row(harness: str, source_dir: Path, output_dir: Path) -> dict:
    source_manifest = validate_source(source_dir)
    output_parent = output_dir.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_parent))
    backup = output_parent / f".{output_dir.name}.backup"
    if backup.exists():
        raise BuildError(f"stale build backup exists: {backup}")
    try:
        write_json(staging / "plan-spec.json", plan_spec())
        build_dir = staging / "build"
        plan_result = run_harness(
            harness,
            [
                "plan",
                "--spec",
                str(staging / "plan-spec.json"),
                "--source",
                str(source_dir / "frame_000.png"),
                "--output",
                str(build_dir),
            ],
            "plan",
        )
        frames_dir = build_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        for index in range(6):
            shutil.copyfile(source_dir / f"frame_{index:03d}.png", frames_dir / f"frame_{index:03d}.png")

        validate_result = run_harness(harness, ["validate", str(build_dir), "--write-qa"], "validate")
        if validate_result.get("valid") is not True:
            raise BuildError("Harness frame validation did not return valid:true")
        run_harness(harness, ["preview", str(build_dir)], "preview")
        run_harness(harness, ["contact-sheet", str(build_dir)], "contact-sheet")
        frame_report = run_harness(harness, ["report", str(build_dir)], "frame report")

        write_json(staging / "export-spec.json", export_spec())
        row_atlas_dir = staging / "row-atlas"
        export_result = run_harness(
            harness,
            ["export", "--spec", str(staging / "export-spec.json"), "--output", str(row_atlas_dir)],
            "export",
        )
        export_validation = run_harness(harness, ["validate-export", str(row_atlas_dir)], "validate-export")
        if export_validation.get("valid") is not True:
            raise BuildError("Harness export validation did not return valid:true")
        export_report = run_harness(harness, ["report", str(row_atlas_dir)], "export report")

        atlas_qa = verify_row_atlas(row_atlas_dir / "atlas.png", source_dir)
        harness_version = subprocess.run(
            [harness, "--version"], capture_output=True, text=True, check=True
        ).stdout.strip()
        qa = {
            "status": "PASS",
            "character": "reimu",
            "codex_row": "waiting",
            "row_index": 6,
            "prototype": source_manifest["prototype"],
            "harness_version": harness_version,
            "source_manifest_sha256": sha256(source_dir / "source.json"),
            "frame_validation": {
                "valid": True,
                "errors": [],
                "warnings": [],
                "checks": validate_result.get("checks"),
            },
            "export_validation": {
                "valid": True,
                "errors": [],
                "warnings": [],
                "checks": export_validation.get("checks"),
            },
            "row_atlas": atlas_qa,
            "frame_report_stage": frame_report.get("stage"),
            "export_report_stage": export_report.get("stage"),
            "plan_warnings": plan_result.get("warnings", []),
            "export_warnings": export_result.get("warnings", []),
            "installable_pet_created": False,
            "full_atlas_created": False,
            "consumer_eating_runtime_modified": False,
        }
        write_json(staging / "qa.json", qa)

        if output_dir.exists():
            os.rename(output_dir, backup)
        try:
            os.rename(staging, output_dir)
            staging = None
        except BaseException:
            if backup.exists() and not output_dir.exists():
                os.rename(backup, output_dir)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        return qa
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD)
    parser.add_argument("--harness")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    try:
        source_dir = args.source_dir.resolve()
        validate_source(source_dir)
        if args.check_only:
            print(json.dumps({"status": "READY", "source": str(source_dir), "frames": 6}, indent=2))
            return 0
        harness = find_harness(args.harness)
        qa = build_waiting_row(harness, source_dir, args.build_dir.resolve())
        print(json.dumps(qa, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (BuildError, subprocess.CalledProcessError) as error:
        print(f"error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
