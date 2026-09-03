#!/usr/bin/env python3
"""Tests for the Sprite Harness consumer build pipeline.

Run from the repository root:

    python3 -m unittest tools.test_build_reimu_animations -v

Unit tests are dependency-free. The integration test drives the real
sprite-harness CLI end to end and is skipped (loudly) when the executable is
not available via --harness conventions (SPRITE_HARNESS_BIN or PATH).
"""

from __future__ import annotations

import json
import os
import shutil
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_reimu_animations as build  # noqa: E402


def make_test_config(tmp: Path) -> dict:
    return {
        "set_version": 1,
        "character": "reimu",
        "state_set": "eating",
        "consumer": "gensokyo-codex-pets",
        "source_root": "assets/reimu/eating",
        "publish_root": "assets/reimu/eating",
        "source_file": "base.png",
        "animation_id_prefix": "reimu_eating",
        "expected_validation_warnings": ["ZERO_MOTION"],
        "defaults": {
            "plan_version": 1,
            "playback": {"fps": 8, "frame_count": 1, "loop": True},
            "anchor": {"type": "bottom_center"},
            "constraints": {"max_displacement_px": 1, "max_frame_delta_px": 1},
            "reduced_motion": {"mode": "hold_first_frame"},
            "tracks": [],
            "events": [],
        },
        "states": {
            "idle": {},
            "task_1": {"playback": {"fps": 4, "frame_count": 1, "loop": False}},
        },
    }


def write_rgba_png(path: Path, width: int = 4, height: int = 4) -> None:
    """Write a minimal valid RGBA PNG (transparent 1px border) without
    third-party libraries. The border keeps visible content off the canvas
    edge so the harness's CONTENT_TOUCHES_EDGE warning does not fire."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    opaque, clear = b"\x80\x40\x20\xff", b"\x00\x00\x00\x00"
    rows = []
    for y in range(height):
        pixels = b"".join(
            opaque if 0 < x < width - 1 and 0 < y < height - 1 else clear
            for x in range(width)
        )
        rows.append(b"\x00" + pixels)
    raw = b"".join(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n")
        handle.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
        handle.write(chunk(b"IDAT", zlib.compress(raw)))
        handle.write(chunk(b"IEND", b""))


class ComposePlanSpecTests(unittest.TestCase):
    def setUp(self):
        self.config = make_test_config(Path("."))

    def test_defaults_are_used(self):
        plan = build.compose_plan_spec(self.config, "idle")
        self.assertEqual(plan["plan_version"], 1)
        self.assertEqual(plan["animation_id"], "reimu_eating_idle")
        self.assertEqual(plan["playback"], {"fps": 8, "frame_count": 1, "loop": True})
        self.assertEqual(plan["anchor"], {"type": "bottom_center"})
        self.assertEqual(plan["reduced_motion"], {"mode": "hold_first_frame"})
        self.assertEqual(plan["metadata"]["state"], "idle")
        self.assertEqual(plan["metadata"]["character"], "reimu")
        self.assertEqual(plan["metadata"]["consumer"], "gensokyo-codex-pets")

    def test_state_override_replaces_whole_section(self):
        plan = build.compose_plan_spec(self.config, "task_1")
        self.assertEqual(plan["playback"], {"fps": 4, "frame_count": 1, "loop": False})
        # Non-overridden sections keep the defaults.
        self.assertEqual(plan["anchor"], {"type": "bottom_center"})

    def test_defaults_are_not_mutated_across_states(self):
        build.compose_plan_spec(self.config, "task_1")
        plan = build.compose_plan_spec(self.config, "idle")
        self.assertEqual(plan["playback"]["fps"], 8)

    def test_unknown_state_is_an_error(self):
        with self.assertRaises(build.BuildError):
            build.compose_plan_spec(self.config, "task_9")


class FindHarnessTests(unittest.TestCase):
    def test_missing_harness_gives_install_instructions(self):
        env_backup = os.environ.pop("SPRITE_HARNESS_BIN", None)
        path_backup = os.environ.get("PATH", "")
        try:
            os.environ["PATH"] = ""
            with self.assertRaises(build.BuildError) as ctx:
                build.find_harness()
            self.assertIn("sprite-harness executable not found", str(ctx.exception))
            self.assertIn("pip install", str(ctx.exception))
        finally:
            os.environ["PATH"] = path_backup
            if env_backup is not None:
                os.environ["SPRITE_HARNESS_BIN"] = env_backup

    def test_explicit_bad_path_is_an_error(self):
        with self.assertRaises(build.BuildError):
            build.find_harness("/nonexistent/sprite-harness")


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.config = make_test_config(self.tmp)
        build_path = self.tmp / "build"
        write_rgba_png(build_path / "frames" / "frame_000.png")
        self.build_facts = {
            "state": "idle",
            "build_path": build_path,
            "source_sha256": "f" * 64,
            "plan_spec": {"animation_id": "reimu_eating_idle"},
            "plan_digest": "sha256:" + "a" * 64,
            "render_mode": "full",
            "playback": {"fps": 8, "frame_count": 1, "loop": True},
            "reduced_motion_mode": "hold_first_frame",
            "frame_files": ["frames/frame_000.png"],
        }

    def test_manifest_shape(self):
        manifest = build.make_manifest(self.build_facts, "0.7.0", self.config)
        self.assertEqual(manifest["manifest_version"], 1)
        self.assertEqual(manifest["state"], "idle")
        self.assertEqual(manifest["playback"], {"fps": 8, "loop": True})
        self.assertEqual(len(manifest["frames"]), 1)
        self.assertEqual(manifest["frames"][0]["file"], "frames/frame_000.png")
        self.assertEqual(manifest["frames"][0]["duration_ms"], 125)
        self.assertEqual(len(manifest["frames"][0]["sha256"]), 64)
        self.assertEqual(manifest["reduced_motion"],
                         {"mode": "hold_first_frame", "frame": "frames/frame_000.png"})
        self.assertEqual(manifest["source"], {"file": "base.png", "sha256": "f" * 64})
        self.assertEqual(manifest["provenance"]["pipeline"], "sprite-harness")
        self.assertEqual(manifest["provenance"]["harness_version"], "0.7.0")
        self.assertEqual(manifest["provenance"]["plan_digest"], "sha256:" + "a" * 64)

    def test_manifest_is_deterministic(self):
        a = build.make_manifest(self.build_facts, "0.7.0", self.config)
        b = build.make_manifest(self.build_facts, "0.7.0", self.config)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.config = make_test_config(self.tmp)
        self.publish_root = self.tmp / "assets"
        self.state_dir = self.publish_root / "idle"
        write_rgba_png(self.state_dir / "base.png")
        self.base_sha = build.sha256_file(self.state_dir / "base.png")

        build_path = self.tmp / "build"
        write_rgba_png(build_path / "frames" / "frame_000.png", width=6)
        self.build_facts = {
            "state": "idle",
            "build_path": build_path,
            "source_sha256": self.base_sha,
            "plan_spec": {"animation_id": "reimu_eating_idle"},
            "plan_digest": "sha256:" + "a" * 64,
            "render_mode": "full",
            "playback": {"fps": 8, "frame_count": 1, "loop": True},
            "reduced_motion_mode": "hold_first_frame",
            "frame_files": ["frames/frame_000.png"],
        }
        self.manifest = build.make_manifest(self.build_facts, "0.7.0", self.config)

    def publish(self):
        build.publish_state(self.build_facts, self.manifest, self.publish_root, "base.png")

    def test_publish_writes_frames_and_manifest(self):
        self.publish()
        self.assertTrue((self.state_dir / "frames" / "frame_000.png").is_file())
        with open(self.state_dir / "animation.json", encoding="utf-8") as handle:
            published = json.load(handle)
        self.assertEqual(published, json.loads(json.dumps(self.manifest)))
        # base.png is untouched.
        self.assertEqual(build.sha256_file(self.state_dir / "base.png"), self.base_sha)
        # No staging remnants.
        leftovers = [p for p in self.state_dir.iterdir() if p.name.startswith(".publish-staging")]
        self.assertEqual(leftovers, [])

    def test_republish_is_idempotent(self):
        self.publish()
        first = build.sha256_file(self.state_dir / "animation.json")
        self.publish()
        self.assertEqual(build.sha256_file(self.state_dir / "animation.json"), first)

    def test_base_png_mismatch_refuses_publish(self):
        self.build_facts = dict(self.build_facts, source_sha256="0" * 64)
        with self.assertRaises(build.BuildError):
            self.publish()
        self.assertFalse((self.state_dir / "animation.json").exists())

    def test_failed_manifest_replace_restores_previous_generation(self):
        self.publish()
        old_frame_sha = build.sha256_file(self.state_dir / "frames" / "frame_000.png")
        old_manifest_sha = build.sha256_file(self.state_dir / "animation.json")

        real_replace = os.replace

        def failing_replace(src, dst):
            if str(dst).endswith("animation.json"):
                raise OSError("simulated failure")
            return real_replace(src, dst)

        os.replace = failing_replace
        try:
            with self.assertRaises(OSError):
                self.publish()
        finally:
            os.replace = real_replace

        # The previous complete generation is intact and staging is gone.
        self.assertEqual(build.sha256_file(self.state_dir / "frames" / "frame_000.png"), old_frame_sha)
        self.assertEqual(build.sha256_file(self.state_dir / "animation.json"), old_manifest_sha)
        leftovers = [p for p in self.state_dir.iterdir() if p.name.startswith(".publish-staging")]
        self.assertEqual(leftovers, [])


def harness_available() -> bool:
    try:
        build.find_harness()
        return True
    except build.BuildError:
        return False


@unittest.skipUnless(harness_available(), "sprite-harness CLI not available")
class IntegrationTests(unittest.TestCase):
    """End-to-end pipeline against the real sprite-harness CLI."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.harness = build.find_harness()
        self.config = make_test_config(self.tmp)
        self.source_root = self.tmp / "sources"
        write_rgba_png(self.source_root / "idle" / "base.png", width=16, height=16)

    def run_build(self, build_dir: Path) -> dict:
        facts = build.build_state(self.harness, self.config, "idle", build_dir, self.source_root)
        return facts

    def test_full_pipeline_and_determinism(self):
        facts_a = self.run_build(self.tmp / "build-a")
        facts_b = self.run_build(self.tmp / "build-b")
        self.assertEqual(facts_a["plan_digest"], facts_b["plan_digest"])
        frame_a = facts_a["build_path"] / "frames" / "frame_000.png"
        frame_b = facts_b["build_path"] / "frames" / "frame_000.png"
        self.assertEqual(build.sha256_file(frame_a), build.sha256_file(frame_b))
        # Source is unchanged and the QA report exists.
        self.assertTrue((facts_a["build_path"] / "qa" / "frames.qa.json").is_file())
        self.assertTrue((facts_a["build_path"] / "preview.gif").is_file())
        self.assertTrue((facts_a["build_path"] / "contact-sheet.png").is_file())

        # Publish twice: byte-identical runtime output for identical input.
        publish_root = self.tmp / "publish"
        state_dir = publish_root / "idle"
        state_dir.mkdir(parents=True)
        shutil.copyfile(self.source_root / "idle" / "base.png", state_dir / "base.png")
        version = build.harness_version(self.harness)
        manifest = build.make_manifest(facts_a, version, self.config)
        build.publish_state(facts_a, manifest, publish_root, "base.png")
        first = build.sha256_file(state_dir / "animation.json")
        manifest_b = build.make_manifest(facts_b, version, self.config)
        build.publish_state(facts_b, manifest_b, publish_root, "base.png")
        self.assertEqual(build.sha256_file(state_dir / "animation.json"), first)

    def test_validation_failure_blocks_the_pipeline(self):
        # A plan that violates its own displacement budget must fail at the
        # plan stage, long before anything could be published.
        bad_config = json.loads(json.dumps(self.config))
        bad_config["states"]["idle"] = {
            "playback": {"fps": 8, "frame_count": 8, "loop": True},
            "tracks": [{
                "track_id": "too_far", "target": "sprite", "motion": "translate_y",
                "amplitude": 50.0, "unit": "px", "curve": "sine", "cycles": 1, "phase": 0.0,
            }],
        }
        with self.assertRaises(build.BuildError):
            build.build_state(self.harness, bad_config, "idle", self.tmp / "build-bad", self.source_root)


if __name__ == "__main__":
    unittest.main()
