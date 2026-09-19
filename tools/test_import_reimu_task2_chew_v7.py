#!/usr/bin/env python3
"""Regression tests for the guarded task_2 chew-v7 source importer."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import import_reimu_task2_chew_v7 as importer


REPO_ROOT = Path(__file__).resolve().parents[1]
PINNED_SOURCE = REPO_ROOT / "pets/reimu/animations/eating/sources/task_2-chew-v7"


class Task2ChewV7ImporterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def fake_harness_build(self) -> Path:
        build = self.tmp / "harness-build"
        (build / "frames").mkdir(parents=True)
        (build / "qa").mkdir()
        for index in range(16):
            shutil.copyfile(
                PINNED_SOURCE / "frames" / f"frame_{index:03d}.png",
                build / "frames" / f"frame_{index:03d}.png",
            )
        (build / "frame-plan.json").write_text(json.dumps({
            "animation_id": importer.EXPECTED_ANIMATION_ID,
            "plan_digest": importer.EXPECTED_PLAN_DIGEST,
            "source": {"sha256": f"sha256:{importer.EXPECTED_SOURCE_SHA256}"},
            "canvas": {**importer.CANVAS, "background": "transparent"},
            "playback": {"fps": 10.0, "frame_count": 16, "loop": True},
        }))
        (build / "qa/frames.qa.json").write_text(json.dumps({
            "valid": True, "errors": [], "warnings": [],
        }))
        return build

    def previous_base(self) -> Path:
        runtime = REPO_ROOT / "assets/reimu/eating/task_2"
        for candidate in (runtime / "base.png", runtime / importer.LEGACY_NAME):
            if candidate.is_file() and importer.sha256(candidate) == importer.EXPECTED_PREVIOUS_BASE_SHA256:
                return candidate
        self.fail("byte-exact previous task_2 base is not preserved")

    def test_fake_pinned_harness_build_is_accepted(self):
        frames = importer.verify_harness_build(self.fake_harness_build())
        self.assertEqual(len(frames), 16)
        self.assertEqual(importer.sha256(frames[0]), importer.EXPECTED_SOURCE_SHA256)

    def test_harness_frame_tamper_is_rejected(self):
        build = self.fake_harness_build()
        (build / "frames/frame_004.png").write_bytes(b"tampered")
        with self.assertRaisesRegex(importer.ImportErrorDetail, "digest-mismatched"):
            importer.verify_harness_build(build)

    def test_import_is_deterministic_and_idempotent(self):
        destination = self.tmp / "source"
        harness_build = self.fake_harness_build()
        importer.import_source(harness_build, destination)
        first = {path.relative_to(destination): path.read_bytes()
                 for path in destination.rglob("*") if path.is_file()}
        importer.import_source(harness_build, destination)
        second = {path.relative_to(destination): path.read_bytes()
                  for path in destination.rglob("*") if path.is_file()}
        self.assertEqual(first, second)

    def test_activation_preserves_previous_base_and_is_idempotent(self):
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        shutil.copyfile(self.previous_base(), runtime / "base.png")
        importer.activate_base(PINNED_SOURCE, runtime)
        self.assertEqual(importer.sha256(runtime / "base.png"), importer.EXPECTED_SOURCE_SHA256)
        self.assertEqual(
            importer.sha256(runtime / importer.LEGACY_NAME),
            importer.EXPECTED_PREVIOUS_BASE_SHA256,
        )
        importer.activate_base(PINNED_SOURCE, runtime)
        self.assertEqual(importer.sha256(runtime / "base.png"), importer.EXPECTED_SOURCE_SHA256)

    def test_activation_rejects_unknown_runtime_base(self):
        runtime = self.tmp / "runtime"
        runtime.mkdir()
        (runtime / "base.png").write_bytes(b"unknown")
        with self.assertRaisesRegex(importer.ImportErrorDetail, "unknown task_2 base"):
            importer.activate_base(PINNED_SOURCE, runtime)


if __name__ == "__main__":
    unittest.main()
