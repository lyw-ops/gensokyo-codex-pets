"""Regression tests for the approved Reimu Codex v2 waiting-row source."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.build_reimu_codex_waiting_row import (
    DEFAULT_SOURCE,
    BuildError,
    build_waiting_row,
    sha256,
    validate_source,
)


def harness_binary() -> str | None:
    return os.environ.get("SPRITE_HARNESS_BIN") or shutil.which("sprite-harness")


class WaitingRowSourceTests(unittest.TestCase):
    def test_checked_in_source_is_valid(self) -> None:
        manifest = validate_source(DEFAULT_SOURCE)
        self.assertEqual(manifest["codex_contract"]["row_index"], 6)
        self.assertEqual(manifest["codex_contract"]["durations_ms"], [150, 150, 150, 150, 150, 260])
        self.assertEqual(len(manifest["frames"]), 6)

    def test_digest_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            copied = Path(temporary) / "waiting"
            shutil.copytree(DEFAULT_SOURCE, copied)
            manifest_path = copied / "source.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["frames"][3]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(BuildError, "digest-mismatched"):
                validate_source(copied)

    def test_wrong_cell_size_is_rejected_even_with_updated_digest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            copied = Path(temporary) / "waiting"
            shutil.copytree(DEFAULT_SOURCE, copied)
            frame_path = copied / "frame_001.png"
            with Image.open(frame_path) as opened:
                opened.convert("RGBA").crop((0, 0, 191, 208)).save(frame_path)
            manifest_path = copied / "source.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["frames"][1]["sha256"] = sha256(frame_path)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(BuildError, "192x208 RGBA"):
                validate_source(copied)

    def test_undeclared_png_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            copied = Path(temporary) / "waiting"
            shutil.copytree(DEFAULT_SOURCE, copied)
            shutil.copyfile(copied / "frame_000.png", copied / "extra.png")
            with self.assertRaisesRegex(BuildError, "undeclared PNGs"):
                validate_source(copied)


class WaitingRowHarnessIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(harness_binary(), "sprite-harness is not available")
    def test_build_export_validate_and_repeat_deterministically(self) -> None:
        harness = harness_binary()
        assert harness is not None
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            output = Path(temporary) / "waiting-row"
            first = build_waiting_row(harness, DEFAULT_SOURCE, output)
            first_atlas = (output / "row-atlas" / "atlas.png").read_bytes()
            first_qa = (output / "qa.json").read_bytes()

            second = build_waiting_row(harness, DEFAULT_SOURCE, output)
            self.assertEqual(first, second)
            self.assertEqual(first_atlas, (output / "row-atlas" / "atlas.png").read_bytes())
            self.assertEqual(first_qa, (output / "qa.json").read_bytes())
            self.assertTrue(second["frame_validation"]["valid"])
            self.assertTrue(second["export_validation"]["valid"])
            self.assertTrue(second["row_atlas"]["unused_cells_fully_transparent"])
            self.assertFalse(second["full_atlas_created"])
            self.assertFalse(second["installable_pet_created"])


if __name__ == "__main__":
    unittest.main()
