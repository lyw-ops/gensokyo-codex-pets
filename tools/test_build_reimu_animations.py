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
