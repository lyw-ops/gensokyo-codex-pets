#!/usr/bin/env python3
"""Tests for the Sprite Harness consumer build pipeline.

Run from the repository root:

    python3 -m unittest tools.test_build_reimu_animations -v

PNG intake tests require Pillow. The integration test drives the real
sprite-harness CLI end to end and is skipped (loudly) when the executable is
not available via --harness conventions (SPRITE_HARNESS_BIN or PATH).
"""

from __future__ import annotations

import json
import contextlib
import io
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_reimu_animations as build  # noqa: E402
import check_reimu_layer_assets as intake  # noqa: E402
import check_reimu_pose_geometry as geometry  # noqa: E402

try:
    import PIL  # noqa: F401
    HAVE_PILLOW = True
except ImportError:
    HAVE_PILLOW = False

EATING_LAYER_SET = "pets/reimu/layers/eating/layer-set.json"


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


def make_exact_frame_package(root: Path, state: str = "pilot", frame_count: int = 3
                             ) -> tuple[dict, Path]:
    package = root / "exact" / state
    write_rgba_png(package / "base.png", width=16, height=16)
    (package / "frames").mkdir()
    frames = []
    for index in range(frame_count):
        path = package / "frames" / f"frame_{index:03d}.png"
        shutil.copyfile(package / "base.png", path) if index == 0 else write_rgba_png(
            path, width=16, height=16)
        frames.append({
            "file": f"frames/frame_{index:03d}.png",
            "sha256": build.sha256_file(path),
            "duration_ms": 100,
        })
    manifest = {
        "exact_frame_source_version": 1,
        "character": "reimu",
        "state_set": "eating",
        "state": state,
        "canvas": {"width": 16, "height": 16},
        "playback": {"fps": 10, "frame_count": frame_count, "loop": True},
        "base": {"file": "base.png", "sha256": build.sha256_file(package / "base.png")},
        "frames": frames,
    }
    manifest_path = package / "source.json"
    manifest_path.write_text(json.dumps(manifest))
    return manifest, manifest_path


class ExactFrameSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.config = make_test_config(self.tmp)
        self.config["states"]["pilot"] = {
            "source_mode": "exact_frames",
            "frame_source": "exact/pilot/source.json",
            "playback": {"fps": 10, "frame_count": 3, "loop": True},
        }
        self.manifest, self.path = make_exact_frame_package(self.tmp)

    def load(self):
        return build.load_exact_frame_source(self.config, "pilot", self.tmp)

    def test_exact_source_is_bound_and_consumer_keys_do_not_reach_plan(self):
        source = self.load()
        self.assertEqual(len(source["frame_paths"]), 3)
        self.assertEqual(source["base_path"].read_bytes(), source["frame_paths"][0].read_bytes())
        plan = build.compose_plan_spec(self.config, "pilot")
        self.assertNotIn("source_mode", plan)
        self.assertNotIn("frame_source", plan)
        self.assertEqual(plan["playback"], self.manifest["playback"])

    def test_exact_source_digest_tamper_fails(self):
        self.manifest["frames"][1]["sha256"] = "0" * 64
        self.path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(build.BuildError, "digest-mismatched"):
            self.load()

    def test_exact_source_semantic_mismatch_fails(self):
        self.manifest["state"] = "task_2"
        self.path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(build.BuildError, "binding mismatch"):
            self.load()

    def test_exact_source_undeclared_file_fails(self):
        write_rgba_png(self.path.parent / "unexpected.png")
        with self.assertRaisesRegex(build.BuildError, "undeclared/missing"):
            self.load()

    def test_exact_source_requires_neutral_loop_endpoints(self):
        from PIL import Image
        final = self.path.parent / self.manifest["frames"][-1]["file"]
        with Image.open(final) as opened:
            changed = opened.convert("RGBA")
        changed.putpixel((2, 2), (1, 2, 3, 255))
        changed.save(final)
        self.manifest["frames"][-1]["sha256"] = build.sha256_file(final)
        self.path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(build.BuildError, "endpoints"):
            self.load()

    def test_exact_source_rejects_wrong_png_dimensions(self):
        frame = self.path.parent / self.manifest["frames"][1]["file"]
        write_rgba_png(frame, width=12, height=12)
        self.manifest["frames"][1]["sha256"] = build.sha256_file(frame)
        self.path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(build.BuildError, "dimensions"):
            self.load()


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


class BuildPathIsolationTests(unittest.TestCase):
    """The disposable build area must never alias/overlap protected paths.

    build_state deletes `build_dir / state_id` before building, so every
    aliasing arrangement must be rejected *before* any destructive operation
    starts. These tests never need the harness: the isolation check raises
    first, so a dummy executable name is passed.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.config = make_test_config(self.tmp)
        self.source_root = self.tmp / "assets"
        self.base_png = self.source_root / "idle" / "base.png"
        write_rgba_png(self.base_png)
        self.base_bytes = self.base_png.read_bytes()
        self.publish_root = self.tmp / "publish"
        self.publish_root.mkdir()

    def expect_rejected(self, build_dir: Path, publish_root: Path | None = None):
        with self.assertRaises(build.BuildError) as ctx:
            build.build_state("harness-never-invoked", self.config, "idle",
                              build_dir, self.source_root,
                              publish_root=publish_root or self.publish_root)
        self.assertIn("unsafe build directory", str(ctx.exception))
        # Fail closed: the source sprite and its directory are untouched.
        self.assertEqual(self.base_png.read_bytes(), self.base_bytes)
        self.assertTrue((self.source_root / "idle").is_dir())

    def test_build_dir_equals_source_root(self):
        self.expect_rejected(self.source_root)

    def test_build_dir_equals_publish_root(self):
        self.expect_rejected(self.publish_root)

    def test_build_dir_inside_source_root(self):
        self.expect_rejected(self.source_root / "build")

    def test_source_root_inside_build_dir(self):
        self.expect_rejected(self.tmp)  # source_root == tmp/assets is inside tmp

    def test_build_dir_inside_publish_root(self):
        self.expect_rejected(self.publish_root / "build")

    def test_publish_root_inside_build_dir(self):
        nested_publish = self.tmp / "work" / "publish"
        nested_publish.mkdir(parents=True)
        self.expect_rejected(self.tmp / "work", publish_root=nested_publish)

    def test_relative_path_alias_is_rejected(self):
        alias = self.source_root / ".." / self.source_root.name
        self.expect_rejected(alias)

    def test_symlink_alias_is_rejected(self):
        link = self.tmp / "innocent-build-dir"
        os.symlink(self.source_root, link)
        self.expect_rejected(link)

    def test_symlinked_source_root_is_still_protected(self):
        # The *source* is reached through a symlink; the raw strings differ
        # but the resolved paths alias.
        link = self.tmp / "assets-link"
        os.symlink(self.source_root, link)
        with self.assertRaises(build.BuildError):
            build.build_state("harness-never-invoked", self.config, "idle",
                              self.source_root, link, publish_root=self.publish_root)
        self.assertEqual(self.base_png.read_bytes(), self.base_bytes)

    def test_malicious_build_dir_never_starts_destruction(self):
        # build_dir == source_root would make the rmtree target the very
        # directory that holds base.png. The bytes must survive untouched.
        self.expect_rejected(self.source_root)
        self.assertEqual(self.base_png.read_bytes(), self.base_bytes)

    def test_disjoint_layout_is_accepted(self):
        build.assert_build_isolation(
            self.tmp / "build",
            {"source_root": self.source_root, "publish_root": self.publish_root},
        )  # must not raise


class SetPublishTransactionTests(unittest.TestCase):
    """All states publish as one logical generation, or none do."""

    STATES = ["idle", "task_1", "task_2"]

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.config = make_test_config(self.tmp)
        self.publish_root = self.tmp / "publish"
        self.base_shas = {}
        for state in self.STATES:
            write_rgba_png(self.publish_root / state / "base.png")
            self.base_shas[state] = build.sha256_file(self.publish_root / state / "base.png")
        # Establish a complete "old" generation first.
        build.publish_set(self.make_generation("old", width=6), self.publish_root, "base.png")
        self.old_snapshot = self.snapshot()

    def make_generation(self, tag: str, width: int) -> list:
        publications = []
        for state in self.STATES:
            build_path = self.tmp / f"build-{tag}" / state
            write_rgba_png(build_path / "frames" / "frame_000.png", width=width)
            facts = {
                "state": state,
                "source_mode": "flattened",
                "build_path": build_path,
                "source_sha256": self.base_shas[state],
                "plan_spec": {"animation_id": f"reimu_eating_{state}"},
                "plan_digest": "sha256:" + "a" * 64,
                "render_mode": "full",
                "playback": {"fps": 8, "frame_count": 1, "loop": True},
                "reduced_motion_mode": "hold_first_frame",
                "frame_files": ["frames/frame_000.png"],
            }
            manifest = build.make_manifest(facts, "0.7.0", self.config)
            publications.append((facts, manifest))
        return publications

    def snapshot(self) -> dict:
        result = {}
        for state in self.STATES:
            state_dir = self.publish_root / state
            result[state] = (
                build.sha256_file(state_dir / "animation.json"),
                build.sha256_file(state_dir / "frames" / "frame_000.png"),
            )
        return result

    def assert_no_leftovers(self):
        for state in self.STATES:
            state_dir = self.publish_root / state
            leftovers = [p.name for p in state_dir.iterdir()
                         if p.name.startswith(".publish-")]
            self.assertEqual(leftovers, [], f"unexpected leftovers in {state}")

    def assert_bases_untouched(self):
        for state in self.STATES:
            self.assertEqual(
                build.sha256_file(self.publish_root / state / "base.png"),
                self.base_shas[state], f"base.png changed for {state}")

    def patch_fs(self, rename_predicate=None, replace_predicate=None):
        """Inject failures into os.rename/os.replace; restored on cleanup."""
        real_rename, real_replace = os.rename, os.replace

        def make(fn, predicate):
            def wrapper(src, dst):
                if predicate and predicate(str(src), str(dst)):
                    raise OSError(f"injected failure: {src} -> {dst}")
                return fn(src, dst)
            return wrapper

        os.rename = make(real_rename, rename_predicate)
        os.replace = make(real_replace, replace_predicate)
        self.addCleanup(setattr, os, "rename", real_rename)
        self.addCleanup(setattr, os, "replace", real_replace)

    def test_success_publishes_all_states_as_one_generation(self):
        build.publish_set(self.make_generation("new", width=8), self.publish_root, "base.png")
        new_snapshot = self.snapshot()
        for state in self.STATES:
            self.assertNotEqual(new_snapshot[state], self.old_snapshot[state])
        self.assert_no_leftovers()
        self.assert_bases_untouched()

    def test_stage_failure_before_first_publish_leaves_all_old(self):
        publications = self.make_generation("new", width=8)
        # The final state's build facts do not match its base.png: staging
        # fails before any destructive commit begins.
        publications[-1][0]["source_sha256"] = "0" * 64
        with self.assertRaises(build.BuildError):
            build.publish_set(publications, self.publish_root, "base.png")
        self.assertEqual(self.snapshot(), self.old_snapshot)
        self.assert_no_leftovers()
        self.assert_bases_untouched()

    def test_frame_rename_failure_on_first_state_leaves_all_old(self):
        self.patch_fs(rename_predicate=lambda src, dst: (
            dst.endswith(os.path.join("idle", "frames")) and src.endswith(os.sep + "frames")))
        with self.assertRaises(OSError):
            build.publish_set(self.make_generation("new", width=8), self.publish_root, "base.png")
        self.assertEqual(self.snapshot(), self.old_snapshot)
        self.assert_no_leftovers()
        self.assert_bases_untouched()

    def test_manifest_replace_failure_in_middle_state_rolls_back_all(self):
        self.patch_fs(replace_predicate=lambda src, dst: (
            dst.endswith(os.path.join("task_1", "animation.json"))))
        with self.assertRaises(OSError):
            build.publish_set(self.make_generation("new", width=8), self.publish_root, "base.png")
        self.assertEqual(self.snapshot(), self.old_snapshot)
        self.assert_no_leftovers()
        self.assert_bases_untouched()

    def test_frame_rename_failure_on_final_state_rolls_back_all(self):
        self.patch_fs(rename_predicate=lambda src, dst: (
            dst.endswith(os.path.join("task_2", "frames")) and src.endswith(os.sep + "frames")))
        with self.assertRaises(OSError):
            build.publish_set(self.make_generation("new", width=8), self.publish_root, "base.png")
        self.assertEqual(self.snapshot(), self.old_snapshot)
        self.assert_no_leftovers()
        self.assert_bases_untouched()

    def test_rollback_failure_is_visible_and_leaves_recovery_marker(self):
        # Commit fails on the final state; while rolling back, restoring the
        # first state's previous manifest also fails. The transaction must
        # not claim success or clean failure: it raises a BuildError naming
        # the broken state, writes a recovery marker, and preserves staging.
        def rename_predicate(src, dst):
            if dst.endswith(os.path.join("task_2", "frames")) and src.endswith(os.sep + "frames"):
                return True  # commit failure on the final state
            if src.endswith(os.path.join("idle", "animation.json")) and \
                    dst.endswith(os.sep + "animation.json"):
                return True  # rollback failure for the first state
            return False

        self.patch_fs(rename_predicate=rename_predicate)
        with self.assertRaises(build.BuildError) as ctx:
            build.publish_set(self.make_generation("new", width=8), self.publish_root, "base.png")
        message = str(ctx.exception)
        self.assertIn("rollback failed", message)
        self.assertIn("idle", message)

        # Recovery marker and staging are preserved for the broken state.
        idle_dir = self.publish_root / "idle"
        marker = idle_dir / build.RECOVERY_MARKER_NAME
        self.assertTrue(marker.is_file())
        recovery = json.loads(marker.read_text())
        self.assertEqual(recovery["state"], "idle")
        staging_dirs = [p for p in idle_dir.iterdir()
                        if p.name.startswith(".publish-staging")]
        self.assertEqual(len(staging_dirs), 1)
        self.assertEqual(recovery["staging_dir"], staging_dirs[0].name)
        # The previous generation is still recoverable from staging.
        self.assertTrue((staging_dirs[0] / build.OLD_MANIFEST_NAME).is_file())

        # States whose rollback succeeded are back on the old generation.
        current = self.snapshot()
        self.assertEqual(current["task_1"], self.old_snapshot["task_1"])
        self.assertEqual(current["task_2"], self.old_snapshot["task_2"])
        self.assert_bases_untouched()


def make_layer_set(asset_root: Path) -> dict:
    return {
        "layer_set_version": 1,
        "character": "reimu",
        "state_set": "eating",
        "reference_canvas": {"width": 16, "height": 16},
        "asset_root": str(asset_root),
        "layers": [
            {"id": "marker", "scope": "state", "image": "{state}/marker.png",
             "anchor": {"type": "center"}, "position": {"x": 8, "y": 5}, "z": 10},
            {"id": "panel", "scope": "shared", "image": "shared/panel.png",
             "anchor": {"type": "center"}, "position": {"x": 8, "y": 8}, "z": 0},
            {"id": "effects", "scope": "state", "image": "{state}/effects.png",
             "anchor": {"type": "center"}, "position": {"x": 8, "y": 3}, "z": 20,
             "required": False},
        ],
    }


def paint(path: Path, size: int, pixels: dict) -> None:
    """Write an RGBA PNG from {(x, y): (r, g, b, a)}; everything else transparent."""
    from PIL import Image
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for (x, y), value in pixels.items():
        image.putpixel((x, y), value)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


@unittest.skipUnless(HAVE_PILLOW, "Pillow required")
class LayerVisibilityTests(unittest.TestCase):
    """Exactly one member of a visibility group may ever be composited."""

    def setUp(self):
        self.layer_set = {
            "layer_set_version": 1, "character": "reimu", "state_set": "slouch",
            "reference_canvas": {"width": 16, "height": 16}, "asset_root": "layers",
            "layers": [
                {"id": "head", "scope": "state", "image": "{state}/head.png",
                 "anchor": {"type": "center"}, "position": {"x": 0, "y": 0}, "z": 10},
                {"id": "eyes_open", "scope": "state", "image": "{state}/eyes_open.png",
                 "anchor": {"type": "center"}, "position": {"x": 0, "y": 0}, "z": 20,
                 "visibility_group": "eyes"},
                {"id": "eyes_closed", "scope": "state", "image": "{state}/eyes_closed.png",
                 "anchor": {"type": "center"}, "position": {"x": 0, "y": 0}, "z": 21,
                 "visibility_group": "eyes"},
            ],
        }
        self.present = {"head", "eyes_open", "eyes_closed"}

    def resolve(self, spec, frames=1):
        config = {"states": {"pose": {"layer_visibility": spec} if spec is not None else {}}}
        return build.resolve_visibility(self.layer_set, config, "pose", self.present, frames)

    def test_an_undeclared_group_fails_closed_instead_of_stacking(self):
        with self.assertRaises(build.BuildError) as caught:
            self.resolve(None)
        self.assertIn("stacked instead of exclusive", str(caught.exception))

    def test_constant_visibility_drops_the_hidden_layer_and_needs_no_track(self):
        excluded, tracks = self.resolve({"eyes": {"default": "eyes_open"}})
        self.assertEqual(excluded, {"eyes_closed"})
        self.assertEqual(tracks, [])

    def test_time_varying_visibility_emits_hold_keyframes_only_at_transitions(self):
        excluded, tracks = self.resolve(
            {"eyes": {"default": "eyes_open", "frames": {"eyes_closed": [2, 3]}}}, frames=5)
        self.assertEqual(excluded, set())
        by_target = {track["target"]: track for track in tracks}
        self.assertEqual(sorted(by_target), ["eyes_closed", "eyes_open"])
        for track in tracks:
            self.assertEqual((track["motion"], track["unit"]), ("opacity", "ratio"))
            self.assertEqual(track["keyframes"][0]["at"], 0)  # the harness requires this
            self.assertTrue(all(0 <= key["at"] < 1 for key in track["keyframes"]))
            self.assertTrue(all(key["interpolation"] == "hold" for key in track["keyframes"]))
        # Visible 0-1, hidden 2-3, visible 4 again: three segments, no per-frame spam.
        self.assertEqual([(k["at"], k["value"]) for k in by_target["eyes_open"]["keyframes"]],
                         [(0.0, 0.0), (0.4, -1.0), (0.8, 0.0)])
        self.assertEqual([(k["at"], k["value"]) for k in by_target["eyes_closed"]["keyframes"]],
                         [(0.0, -1.0), (0.4, 0.0), (0.8, -1.0)])

    def test_two_members_cannot_claim_the_same_frame(self):
        with self.assertRaises(build.BuildError) as caught:
            self.resolve({"eyes": {"default": "eyes_open",
                                   "frames": {"eyes_closed": [1], "eyes_open": [1]}}}, frames=3)
        self.assertIn("claimed by both", str(caught.exception))

    def test_frames_outside_the_state_are_refused(self):
        with self.assertRaises(build.BuildError) as caught:
            self.resolve({"eyes": {"default": "eyes_open", "frames": {"eyes_closed": [9]}}}, frames=3)
        self.assertIn("outside the state", str(caught.exception))

    def test_default_must_name_a_present_member(self):
        with self.assertRaises(build.BuildError) as caught:
            self.resolve({"eyes": {"default": "mouth"}})
        self.assertIn("is not one of", str(caught.exception))

    def test_unknown_group_is_refused(self):
        with self.assertRaises(build.BuildError) as caught:
            self.resolve({"hands": {"default": "eyes_open"}})
        self.assertIn("unknown or absent group", str(caught.exception))

    def test_a_group_whose_other_member_is_absent_needs_no_declaration(self):
        excluded, tracks = build.resolve_visibility(
            self.layer_set, {"states": {"pose": {}}}, "pose", {"head", "eyes_open"}, 1)
        self.assertEqual((excluded, tracks), (set(), []))

    def test_an_authored_track_may_not_also_drive_a_grouped_layer(self):
        config = {"character": "reimu", "state_set": "slouch",
                  "animation_id_prefix": "reimu_slouch",
                  "defaults": {"playback": {"fps": 8, "frame_count": 5, "loop": True},
                               "tracks": [{"track_id": "fade", "target": "eyes_open",
                                           "motion": "opacity", "unit": "ratio",
                                           "curve": "sine", "amplitude": 0.5, "cycles": 1}]},
                  "states": {"pose": {"source_mode": "layered"}}}
        _, tracks = self.resolve(
            {"eyes": {"default": "eyes_open", "frames": {"eyes_closed": [2]}}}, frames=5)
        with self.assertRaises(build.BuildError) as caught:
            build.compose_plan_spec(config, "pose", layered_source={"layers": []},
                                    visibility_tracks=tracks)
        self.assertIn("already drives the opacity", str(caught.exception))


class PoseGeometryTests(unittest.TestCase):
    """Each check must actually fire; a gate that cannot fail is not a gate."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def solid(self, name, box, colour=(120, 70, 50, 255)):
        path = self.tmp / name
        x0, y0, x1, y1 = box
        paint(path, 64, {(x, y): colour for x in range(x0, x1) for y in range(y0, y1)})
        return path

    def test_support_edge_reports_a_pose_that_floats(self):
        paths = {"body": self.solid("body.png", (10, 10, 20, 30))}
        rule = {"layer": "body", "y": 29, "tolerance": 0}
        self.assertEqual(geometry.check_support_edge(paths, rule), [])
        rule = {"layer": "body", "y": 40, "tolerance": 2}
        self.assertIn("support edge is y=29", geometry.check_support_edge(paths, rule)[0])

    def test_palette_measures_presence_not_dominance(self):
        approved = (247, 224, 216)
        on_model = self.solid("on_model.png", (10, 10, 40, 40), colour=approved + (255,))
        drifted = self.solid("drifted.png", (10, 10, 40, 40), colour=(244, 196, 164, 255))
        rule = {"tolerance": 18,
                "references": {"skin": {"colour": list(approved), "min_fraction": 0.08}},
                "layers": {"head": "skin"}}
        self.assertEqual(geometry.check_palette({"head": on_model}, rule), [])
        failure = geometry.check_palette({"head": drifted}, rule)[0]
        self.assertIn("off-palette", failure)

    def test_palette_is_not_fooled_by_a_more_numerous_other_colour(self):
        # A dominant-colour test would pick the white lace; presence must not.
        mixed = self.tmp / "mixed.png"
        pixels = {(x, y): (255, 255, 255, 255) for x in range(0, 50) for y in range(0, 40)}
        pixels.update({(x, y): (247, 224, 216, 255) for x in range(0, 50) for y in range(40, 50)})
        paint(mixed, 64, pixels)
        rule = {"tolerance": 18,
                "references": {"skin": {"colour": [247, 224, 216], "min_fraction": 0.08}},
                "layers": {"head": "skin"}}
        self.assertEqual(geometry.check_palette({"head": mixed}, rule), [])

    def test_alpha_hygiene_accepts_soft_edges_and_rejects_scattered_noise(self):
        feathered = self.tmp / "feathered.png"
        pixels = {(x, y): (120, 70, 50, 255) for x in range(20, 40) for y in range(20, 40)}
        for x in range(18, 42):  # a three-pixel feather around the shape
            for y in range(18, 42):
                pixels.setdefault((x, y), (120, 70, 50, 4))
        paint(feathered, 64, pixels)
        rule = {"speckle_alpha_below": 8, "isolation_radius": 7, "max_speckle_px": 8}
        self.assertEqual(geometry.check_alpha_hygiene({"body": feathered}, rule), [])
        noisy = self.tmp / "noisy.png"
        scattered = dict(pixels)
        for index in range(40):
            scattered[(index + 2, 60 - (index % 3))] = (255, 255, 255, 3)
        paint(noisy, 64, scattered)
        failure = geometry.check_alpha_hygiene({"body": noisy}, rule)[0]
        self.assertIn("isolated pixel", failure)


class SecondStateSetTests(unittest.TestCase):
    """A state set other than `eating` must work end to end with no hardwired paths."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.layer_root = self.tmp / "assets/reimu/layered/slouch"
        self.layer_set = make_layer_set(self.layer_root)
        self.layer_set.update(state_set="slouch", canvas_policy="full_canvas")
        self.layer_set["reference_canvas"] = {"width": 16, "height": 16}
        self.spec = "pets/reimu/animations/slouch/animation-set.json"
        self.config = make_test_config(self.tmp)
        self.config.update(state_set="slouch", source_root="assets/reimu/slouch",
                           publish_root="assets/reimu/slouch",
                           animation_id_prefix="reimu_slouch",
                           layer_set="pets/reimu/layers/slouch/layer-set.json",
                           states={"pose_prop": {"source_mode": "layered"}})

    def write(self, layers=("shared/panel.png", "pose_prop/marker.png")):
        for relative in layers:
            write_rgba_png(self.layer_root / relative, 16, 16)
        contract = self.tmp / self.config["layer_set"]
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text(json.dumps(self.layer_set))
        config_path = self.tmp / self.spec
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(self.config))

    def run_intake(self, state="pose_prop"):
        output = io.StringIO()
        with mock.patch.object(build, "REPO_ROOT", self.tmp), contextlib.redirect_stdout(output):
            code = intake.main(["--config", self.spec, "--state", state])
        return code, output.getvalue()

    def test_second_state_set_passes_intake(self):
        self.write()
        code, output = self.run_intake()
        self.assertEqual(code, 0, output)
        self.assertTrue(output.startswith("READY\n"), output)
        self.assertIn(self.spec, output)

    def test_missing_layers_are_listed_as_a_shopping_list(self):
        self.write(layers=("shared/panel.png",))
        code, output = self.run_intake()
        self.assertEqual(code, 1)
        self.assertTrue(output.startswith("ART ASSET REQUIRED\n"), output)
        self.assertIn("pose_prop/marker.png", output)

    def test_layer_set_bound_to_another_state_set_is_refused(self):
        self.layer_set["state_set"] = "eating"
        self.write()
        code, output = self.run_intake()
        self.assertEqual(code, 1)
        self.assertIn("layer set binding mismatch", output)

    def test_unknown_state_names_the_declared_states(self):
        self.write()
        code, output = self.run_intake(state="task_2")
        self.assertEqual(code, 1)
        self.assertIn("pose_prop", output)

    def test_plan_and_manifest_name_their_own_animation_set(self):
        path = self._written_config()
        with mock.patch.object(build, "REPO_ROOT", self.tmp):
            loaded = build.load_config(path)
        self.assertEqual(build.config_spec_path(loaded), self.spec)
        plan = build.compose_plan_spec(loaded, "pose_prop", layered_source={
            "mode": "layered", "layer_set": loaded["layer_set"], "layers": []})
        self.assertEqual(plan["metadata"]["spec"], self.spec)
        self.assertEqual(plan["metadata"]["state_set"], "slouch")
        self.assertEqual(plan["animation_id"], "reimu_slouch_pose_prop")

    def _written_config(self):
        self.write()
        return self.tmp / self.spec

    def test_in_memory_config_falls_back_to_the_layout_convention(self):
        self.assertEqual(build.config_spec_path(self.config), self.spec)

    def test_each_state_set_builds_in_its_own_directory(self):
        eating = make_test_config(self.tmp)
        self.assertNotEqual(build.default_build_dir(eating), build.default_build_dir(self.config))
        self.assertTrue(str(build.default_build_dir(self.config)).endswith("reimu/slouch"))

    def test_config_outside_the_repository_is_refused(self):
        self.write()
        with self.assertRaises(build.BuildError) as caught:
            build.load_config(self.tmp / self.spec)
        self.assertIn("inside the repository", str(caught.exception))


class LayeredSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.layer_root = self.tmp / "layers"
        self.plan_dir = self.tmp / "build" / "pilot"
        self.plan_dir.mkdir(parents=True)
        self.layer_set = make_layer_set(self.layer_root)
        write_rgba_png(self.layer_root / "shared" / "panel.png", width=8, height=8)
        write_rgba_png(self.layer_root / "pilot" / "marker.png")

    def compose(self, state="pilot"):
        return build.compose_layered_source(self.layer_set, state, self.layer_root, self.plan_dir)

    def test_layers_are_ordered_back_to_front_by_z(self):
        source, layer_files = self.compose()
        self.assertEqual([l["target"] for l in source["layers"]], ["panel", "marker"])
        self.assertEqual(source["reference_canvas"], {"width": 16, "height": 16})
        self.assertEqual([lid for lid, _, _ in layer_files], ["panel", "marker"])

    def test_state_placeholder_is_substituted(self):
        source, _ = self.compose()
        marker = next(l for l in source["layers"] if l["target"] == "marker")
        resolved = (self.plan_dir / marker["image"]).resolve()
        self.assertEqual(resolved, (self.layer_root / "pilot" / "marker.png").resolve())

    def test_missing_optional_layer_is_skipped(self):
        source, _ = self.compose()
        self.assertNotIn("effects", [l["target"] for l in source["layers"]])

    def test_missing_required_layer_is_an_art_asset_error(self):
        (self.layer_root / "pilot" / "marker.png").unlink()
        with self.assertRaises(build.BuildError) as ctx:
            self.compose()
        self.assertIn("ART ASSET REQUIRED", str(ctx.exception))
        self.assertIn("marker", str(ctx.exception))

    def test_duplicate_z_is_rejected(self):
        self.layer_set["layers"][0]["z"] = 0  # collides with panel
        with self.assertRaises(build.BuildError):
            self.compose()

    def test_states_restriction_filters_layers(self):
        self.layer_set["layers"][0]["states"] = ["other_state"]
        source, _ = self.compose()
        self.assertEqual([l["target"] for l in source["layers"]], ["panel"])

    def test_layered_plan_spec_is_version_2_without_consumer_keys(self):
        config = make_test_config(self.tmp)
        config["states"]["pilot"] = {"source_mode": "layered"}
        source, _ = self.compose()
        plan = build.compose_plan_spec(config, "pilot", layered_source=source)
        self.assertEqual(plan["plan_version"], 2)
        self.assertEqual(plan["source"], source)
        self.assertNotIn("source_mode", plan)

    def test_layered_state_without_source_is_an_error(self):
        config = make_test_config(self.tmp)
        config["states"]["pilot"] = {"source_mode": "layered"}
        with self.assertRaises(build.BuildError):
            build.compose_plan_spec(config, "pilot")

    def test_layer_set_shape_is_validated(self):
        bad = dict(self.layer_set)
        del bad["reference_canvas"]
        path = self.tmp / "bad-layer-set.json"
        path.write_text(json.dumps(bad))
        with self.assertRaises(build.BuildError):
            build.load_layer_set(path)

    def test_duplicate_layer_ids_are_rejected(self):
        bad = json.loads(json.dumps(self.layer_set))
        bad["layers"].append(dict(bad["layers"][0]))
        path = self.tmp / "dup-layer-set.json"
        path.write_text(json.dumps(bad))
        with self.assertRaises(build.BuildError):
            build.load_layer_set(path)


class LayerRootProtectionTests(unittest.TestCase):
    """Exercise main's config loading while all six states remain flattened."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.layer_root = self.tmp / "work" / "layers"
        self.layer_png = self.layer_root / "idle" / "marker.png"
        write_rgba_png(self.layer_png)
        self.base = self.tmp / "sources" / "idle" / "base.png"
        write_rgba_png(self.base)
        self.config = make_test_config(self.tmp)
        self.config.update(source_root="sources", publish_root="published", layer_set="layers.json")
        self.config["states"] = {s: {} for s in ["idle", "task_1", "task_2", "task_3", "task_4", "task_5"]}
        (self.tmp / "config.json").write_text(json.dumps(self.config))
        self.layer_set = make_layer_set(self.layer_root)
        (self.tmp / "layers.json").write_text(json.dumps(self.layer_set))

    def expect_rejected(self, build_dir):
        before = {p: p.read_bytes() for p in (self.base, self.layer_png)}
        errors = io.StringIO()
        with mock.patch.object(build, "REPO_ROOT", self.tmp), \
                mock.patch.object(build, "find_harness", return_value="never-run"), \
                mock.patch.object(build, "harness_version") as version, \
                mock.patch.object(build, "build_state") as build_state, \
                mock.patch.object(build.shutil, "rmtree") as delete, \
                contextlib.redirect_stderr(errors):
            result = build.main(["--config", str(self.tmp / "config.json"),
                                 "--build-dir", str(build_dir)])
        self.assertEqual(result, 1)
        self.assertIn("layer_root", errors.getvalue())
        self.assertIn("unsafe build directory", errors.getvalue())
        version.assert_not_called()
        build_state.assert_not_called()
        delete.assert_not_called()
        self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_build_dir_equal_layer_root_fails_even_when_no_layered_state_enabled(self):
        self.expect_rejected(self.layer_root)

    def test_build_dir_inside_layer_root_fails(self):
        self.expect_rejected(self.layer_root / "build")

    def test_layer_root_inside_build_dir_fails(self):
        self.expect_rejected(self.layer_root.parent)

    def test_layer_root_symlink_alias_fails(self):
        alias = self.tmp / "harmless"
        alias.symlink_to(self.layer_root, target_is_directory=True)
        self.expect_rejected(alias)
        # The contract itself can also reach the protected root through an alias.
        self.layer_set["asset_root"] = str(alias)
        (self.tmp / "layers.json").write_text(json.dumps(self.layer_set))
        self.expect_rejected(self.layer_root)


class RepositorySourceGateTests(unittest.TestCase):
    """Run the actual repository script against mixed-mode disposable fixtures."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "repo"
        shutil.copytree(build.REPO_ROOT, self.repo,
                        ignore=shutil.ignore_patterns(".git", "build", ".venv", "__pycache__"))
        self.layer_set = build.load_layer_set(self.repo / EATING_LAYER_SET)
        self.layer_root = self.repo / self.layer_set["asset_root"]
        # These tests author their own exact required/optional layer set. Do
        # not let unrelated real working-tree PNGs copied into the disposable
        # fixture change which optionals are considered present.
        for path in self.layer_root.rglob("*.png"):
            path.unlink()
        self.manifest_path = self.repo / "assets/reimu/eating/task_2/animation.json"
        self.manifest = json.loads(self.manifest_path.read_text())

    def authored_layers(self):
        entries = []
        for layer in sorted(self.layer_set["layers"], key=lambda item: item["z"]):
            if not layer.get("required", True):
                continue
            path = self.layer_root / layer["image"].replace("{state}", "task_2")
            write_rgba_png(path, width=596, height=596)
            entries.append({"id": layer["id"], "sha256": build.sha256_file(path)})
        self.manifest["source"] = {"mode": "layered", "layer_set": EATING_LAYER_SET,
                                   "layers": entries}

    def run_check(self, expected=0, message=None):
        self.manifest_path.write_text(json.dumps(self.manifest))
        pngs = list(self.repo.glob("assets/reimu/eating/*/base.png")) + list(self.layer_root.rglob("*.png"))
        before = {p: p.read_bytes() for p in pngs}
        env = dict(os.environ, PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"])
        result = subprocess.run(["bash", "scripts/check-repository.sh"], cwd=self.repo,
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        if message:
            self.assertIn(message, result.stderr)
        self.assertEqual({p: p.read_bytes() for p in before}, before,
                         "repository check must leave layer PNG and base.png bytes unchanged")

    def test_check_repository_accepts_flattened_manifest(self):
        self.run_check()

    def test_flattened_wrong_sha_fails(self):
        self.manifest["source"]["sha256"] = "0" * 64
        self.run_check(1, "does not match base.png")

    def test_check_repository_accepts_layered_manifest(self):
        self.authored_layers()  # Other five manifests remain flattened.
        self.run_check()

    def test_layered_manifest_wrong_layer_set_fails(self):
        self.authored_layers()
        self.manifest["source"]["layer_set"] = "wrong.json"
        self.run_check(1, "wrong layer_set")

    def test_layered_manifest_missing_required_layer_fails(self):
        self.authored_layers()
        self.manifest["source"]["layers"].pop()
        self.run_check(1, "layer ids mismatch")

    def test_layered_required_png_missing_fails(self):
        self.authored_layers()
        (self.layer_root / "shared/body.png").unlink()
        self.run_check(1, "missing required layer body")

    def test_layered_manifest_wrong_sha_fails(self):
        self.authored_layers()
        self.manifest["source"]["layers"][0]["sha256"] = "0" * 64
        self.run_check(1, "SHA-256 mismatch")

    def test_layered_manifest_unknown_layer_fails(self):
        self.authored_layers()
        self.manifest["source"]["layers"].append({"id": "unknown", "sha256": "0" * 64})
        self.run_check(1, "layer ids mismatch")

    def test_layered_manifest_duplicate_layer_fails(self):
        self.authored_layers()
        self.manifest["source"]["layers"].append(self.manifest["source"]["layers"][0])
        self.run_check(1, "duplicate layer id")

    def test_present_optional_layer_must_be_bound(self):
        self.authored_layers()
        path = self.layer_root / "task_2/effects.png"
        write_rgba_png(path, width=596, height=596)
        self.run_check(1, "layer ids mismatch")
        self.manifest["source"]["layers"].append({"id": "effects", "sha256": build.sha256_file(path)})
        self.run_check()

    def test_absent_optional_layer_must_not_be_bound(self):
        self.authored_layers()
        self.manifest["source"]["layers"].append({"id": "effects", "sha256": "0" * 64})
        self.run_check(1, "layer ids mismatch")

    def test_undeclared_authored_png_fails(self):
        self.authored_layers()
        write_rgba_png(self.layer_root / "task_2/unknown.png")
        self.run_check(1, "unexpected authored PNG")

    def test_layered_png_invalid_format_or_dimensions_fails(self):
        self.authored_layers()
        from PIL import Image
        path = self.layer_root / "shared/body.png"
        for mode, size, expected in [("RGB", (596, 596), "expected RGBA"),
                                     ("RGBA", (597, 596), "dimensions")]:
            with self.subTest(mode=mode, size=size):
                Image.new(mode, size).save(path)
                self.run_check(1, expected)


class LayerIntakeTests(unittest.TestCase):
    """Tiny synthetic PNGs exercise intake; none are production artwork."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.layer_root = self.tmp / "layers"
        self.layer_set = make_layer_set(self.layer_root)
        self.layer_set["canvas_policy"] = "full_canvas"
        self.layer = self.layer_set["layers"][0]
        self.marker = self.layer_root / "task_2/marker.png"
        self.panel = self.layer_root / "shared/panel.png"
        write_rgba_png(self.marker, 16, 16)
        write_rgba_png(self.panel, 16, 16)

    def inspect(self):
        before = {p: p.read_bytes() for p in self.layer_root.rglob("*.png") if p.is_file()}
        result = intake.inspect_assets(self.layer_set, "task_2", self.layer_root)
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        return result

    def run_intake(self):
        contract = self.tmp / EATING_LAYER_SET
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text(json.dumps(self.layer_set))
        config_path = self.tmp / "pets/reimu/animations/eating/animation-set.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config = make_test_config(self.tmp)
        config.update(layer_set=EATING_LAYER_SET, states={"task_2": {}})
        config_path.write_text(json.dumps(config))
        output = io.StringIO()
        with mock.patch.object(build, "REPO_ROOT", self.tmp), contextlib.redirect_stdout(output):
            code = intake.main([])
        return code, output.getvalue()

    def test_intake_ready_without_optional_layers(self):
        code, output = self.run_intake()
        self.assertEqual(code, 0, output)
        self.assertTrue(output.startswith("READY\n"))
        self.assertIn("Optional layers absent (not blockers)", output)

    def test_intake_lists_every_missing_required_file(self):
        self.marker.unlink()
        self.panel.unlink()
        code, output = self.run_intake()
        self.assertEqual(code, 1)
        self.assertTrue(output.startswith("ART ASSET REQUIRED\n"))
        self.assertIn("layers/task_2/marker.png", output)
        self.assertIn("layers/shared/panel.png", output)

    def test_intake_rejects_invalid_png_rgba_alpha_and_dimensions(self):
        from PIL import Image
        cases = [("RGBA", (16, 16), (0, 0, 0, 0), "fully transparent"),
                 ("RGBA", (16, 16), (0, 0, 0, 255), "no transparent pixels"),
                 ("RGB", (16, 16), (0, 0, 0), "expected RGBA"),
                 ("LA", (16, 16), (0, 0), "expected RGBA"),
                 ("RGBA", (8, 8), (0, 0, 0, 0), "dimensions")]
        for mode, size, color, expected in cases:
            with self.subTest(mode=mode, size=size, color=color):
                Image.new(mode, size, color).save(self.marker)
                self.assertIn(expected, "\n".join(self.inspect()[1]))
        self.marker.write_bytes(b"not a PNG")
        self.assertIn("unreadable PNG", "\n".join(self.inspect()[1]))
        write_rgba_png(self.marker, 16, 16)
        self.marker.write_bytes(self.marker.read_bytes()[:40])
        self.assertIn("unreadable PNG", "\n".join(self.inspect()[1]))

    def test_intake_rejects_path_escape_and_symlink_escape(self):
        outside = self.tmp / "marker.png"
        write_rgba_png(outside, 16, 16)
        self.layer["image"] = "../marker.png"
        self.assertIn("outside asset_root", "\n".join(self.inspect()[1]))
        self.layer["image"] = "{state}/marker.png"
        self.marker.unlink()
        self.marker.symlink_to(outside)
        self.assertIn("outside asset_root", "\n".join(self.inspect()[1]))
        with self.assertRaisesRegex(build.BuildError, "outside asset_root"):
            build.compose_layered_source(self.layer_set, "task_2", self.layer_root, self.tmp / "build")

    def test_intake_rejects_filename_id_mismatch(self):
        self.layer["image"] = "{state}/different.png"
        self.assertIn("filename must match layer id", "\n".join(self.inspect()[1]))

    def test_intake_rejects_unexpected_png(self):
        write_rgba_png(self.layer_root / "task_2/unknown.png")
        code, output = self.run_intake()
        self.assertEqual(code, 1)
        self.assertIn("unexpected authored PNG", output)

    def test_intake_filters_state_restrictions_like_builder(self):
        self.layer["states"] = ["task_1"]
        records, failures, _ = self.inspect()
        self.assertFalse(failures)
        self.assertEqual([entry["id"] for entry in records], ["panel"])
        source, _ = build.compose_layered_source(self.layer_set, "task_2", self.layer_root, self.tmp / "build")
        self.assertEqual([entry["target"] for entry in source["layers"]], ["panel"])


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

    def test_layered_v2_pipeline_end_to_end(self):
        """Animation Plan v2 with local motion: synthetic authored layers →
        plan → render → validate → publish, all via the public CLI."""
        layer_root = self.tmp / "layers"
        write_rgba_png(layer_root / "shared" / "panel.png", width=8, height=8)
        write_rgba_png(layer_root / "pilot" / "marker.png")
        layer_set = make_layer_set(layer_root)

        config = make_test_config(self.tmp)
        config["layer_set"] = "pets/reimu/layers/eating/layer-set.json"
        config["expected_validation_warnings"] = []
        config["states"]["pilot"] = {
            "source_mode": "layered",
            "playback": {"fps": 8, "frame_count": 4, "loop": True},
            "tracks": [{
                "track_id": "marker_bob", "target": "marker", "motion": "translate_y",
                "amplitude": 1.0, "unit": "px", "curve": "sine", "cycles": 1, "phase": 0.0,
            }],
        }

        facts = build.build_state(self.harness, config, "pilot", self.tmp / "build-l",
                                  self.source_root, layer_set=layer_set,
                                  layer_root=layer_root)
        self.assertEqual(facts["source_mode"], "layered")
        self.assertEqual(len(facts["frame_files"]), 4)
        self.assertEqual([lid for lid, _, _ in facts["layer_files"]], ["panel", "marker"])

        # Local motion is real: not every frame is byte-identical.
        frame_shas = {build.sha256_file(facts["build_path"] / f) for f in facts["frame_files"]}
        self.assertGreater(len(frame_shas), 1)

        # Publish: base.png stays the fallback; the manifest binds the layers.
        publish_root = self.tmp / "publish-l"
        write_rgba_png(publish_root / "pilot" / "base.png", width=16, height=16)
        version = build.harness_version(self.harness)
        manifest = build.make_manifest(facts, version, config)
        self.assertEqual(manifest["source"]["mode"], "layered")
        self.assertEqual([l["id"] for l in manifest["source"]["layers"]], ["panel", "marker"])
        build.publish_state(facts, manifest, publish_root, "base.png")
        self.assertTrue((publish_root / "pilot" / "frames" / "frame_003.png").is_file())

        # Determinism: an independent rebuild yields the same digest and frames.
        facts_b = build.build_state(self.harness, config, "pilot", self.tmp / "build-l2",
                                    self.source_root, layer_set=layer_set,
                                    layer_root=layer_root)
        self.assertEqual(facts["plan_digest"], facts_b["plan_digest"])
        for f in facts["frame_files"]:
            self.assertEqual(build.sha256_file(facts["build_path"] / f),
                             build.sha256_file(facts_b["build_path"] / f))

    def test_layered_state_without_authored_assets_fails_closed(self):
        layer_root = self.tmp / "layers-missing"
        layer_set = make_layer_set(layer_root)
        config = make_test_config(self.tmp)
        config["states"]["pilot"] = {"source_mode": "layered"}
        with self.assertRaises(build.BuildError) as ctx:
            build.build_state(self.harness, config, "pilot", self.tmp / "build-m",
                              self.source_root, layer_set=layer_set, layer_root=layer_root)
        self.assertIn("ART ASSET REQUIRED", str(ctx.exception))

    def test_exact_frame_pipeline_validates_external_pixels_and_publishes(self):
        config = make_test_config(self.tmp)
        config["states"]["pilot"] = {
            "source_mode": "exact_frames",
            "frame_source": "exact/pilot/source.json",
            "playback": {"fps": 10, "frame_count": 3, "loop": True},
            "tracks": [],
        }
        _manifest, _path = make_exact_frame_package(self.tmp)
        exact = build.load_exact_frame_source(config, "pilot", self.tmp)
        (self.source_root / "pilot").mkdir(parents=True)
        shutil.copyfile(exact["base_path"], self.source_root / "pilot" / "base.png")

        facts = build.build_state(
            self.harness, config, "pilot", self.tmp / "build-exact", self.source_root,
            exact_source=exact,
        )
        self.assertEqual(facts["source_mode"], "exact_frames")
        self.assertEqual(facts["render_mode"], "external")
        self.assertEqual(len(facts["frame_files"]), 3)
        self.assertFalse((facts["build_path"] / "render.json").exists())
        for built_name, source_path in zip(facts["frame_files"], exact["frame_paths"], strict=True):
            self.assertEqual(
                (facts["build_path"] / built_name).read_bytes(), source_path.read_bytes())

        runtime = self.tmp / "publish-exact" / "pilot"
        runtime.mkdir(parents=True)
        shutil.copyfile(exact["base_path"], runtime / "base.png")
        manifest = build.make_manifest(facts, build.harness_version(self.harness), config)
        self.assertEqual([frame["duration_ms"] for frame in manifest["frames"]], [100, 100, 100])
        self.assertEqual(manifest["source"], {
            "file": "base.png", "sha256": exact["base_sha256"],
        })
        self.assertEqual(manifest["provenance"]["source_mode"], "approved_exact_frames")
        build.publish_state(facts, manifest, runtime.parent, "base.png")
        self.assertTrue((runtime / "frames" / "frame_002.png").is_file())

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
