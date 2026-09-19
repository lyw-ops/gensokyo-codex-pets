#!/usr/bin/env python3
"""Regression tests for the guarded task_2 chew-v9 source importer."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import import_reimu_task2_chew_v9 as importer


REPO_ROOT = Path(__file__).resolve().parents[1]
PINNED_SOURCE = REPO_ROOT / "pets/reimu/animations/eating/sources/task_2-chew-v9"


class Task2ChewV9ImporterTests(unittest.TestCase):
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

    def test_fake_pinned_harness_build_is_accepted(self):
        frames = importer.verify_harness_build(self.fake_harness_build())
        self.assertEqual(len(frames), 16)
        self.assertEqual(importer.sha256(frames[0]), importer.EXPECTED_SOURCE_SHA256)

    def test_harness_frame_tamper_is_rejected(self):
        build = self.fake_harness_build()
        (build / "frames/frame_004.png").write_bytes(b"tampered")
        with self.assertRaisesRegex(importer.ImportErrorDetail, "digest-mismatched"):
            importer.verify_harness_build(build)

    def test_harness_warning_is_rejected(self):
        build = self.fake_harness_build()
        (build / "qa/frames.qa.json").write_text(json.dumps({
            "valid": True,
            "errors": [],
            "warnings": [{"code": "UNEXPECTED_WARNING"}],
        }))
        with self.assertRaisesRegex(importer.ImportErrorDetail, "zero errors/warnings"):
            importer.verify_harness_build(build)

    def test_import_is_deterministic_and_idempotent(self):
        destination = self.tmp / "source"
        harness_build = self.fake_harness_build()
        importer.import_source(harness_build, destination)
        first = {
            path.relative_to(destination): path.read_bytes()
            for path in destination.rglob("*") if path.is_file()
        }
        importer.import_source(harness_build, destination)
        second = {
            path.relative_to(destination): path.read_bytes()
            for path in destination.rglob("*") if path.is_file()
        }
        self.assertEqual(first, second)

    def test_source_manifest_matches_pinned_package(self):
        expected = importer.make_manifest()
        actual = json.loads((PINNED_SOURCE / "source.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)
        self.assertEqual(
            importer.sha256(PINNED_SOURCE / "base.png"),
            importer.EXPECTED_SOURCE_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
