#!/usr/bin/env python3
"""Read-only checks for authored Reimu layers and runtime source bindings."""

from __future__ import annotations

import argparse
from pathlib import Path

if __package__:
    from . import build_reimu_animations as build
else:
    import build_reimu_animations as build

DEFAULT_CONFIG = "pets/reimu/animations/eating/animation-set.json"


def inspect_png(path: Path, layer: dict, canvas: dict, policy: str | None) -> None:
    try:
        from PIL import Image
    except ImportError:
        raise build.BuildError("PNG inspection requires Pillow; use the Sprite Harness "
                               "venv's Python or install Pillow in your Python environment")
    try:
        with Image.open(path) as image:
            if image.format != "PNG":
                raise build.BuildError(f"{path}: expected a readable PNG")
            image.verify()
        with Image.open(path) as image:
            image.load()
            if image.mode != "RGBA":
                raise build.BuildError(f"{path}: expected RGBA with alpha, got {image.mode}")
            expected = (canvas["width"], canvas["height"])
            if (policy == "full_canvas" and image.size != expected) or not (
                    0 < image.width <= expected[0] and 0 < image.height <= expected[1]):
                raise build.BuildError(f"{path}: dimensions {image.size} incompatible with "
                                       f"{policy or 'cropped'} canvas {expected}")
            low, high = image.getchannel("A").getextrema()
            if low == 255:
                raise build.BuildError(f"{path}: alpha has no transparent pixels")
            if layer.get("required", True) and high == 0:
                raise build.BuildError(f"{path}: required layer is fully transparent")
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as error:
        raise build.BuildError(f"{path}: unreadable PNG: {error}") from error


def inspect_assets(layer_set: dict, state: str, layer_root: Path
                   ) -> tuple[list[dict], list[str], list[str]]:
    """Inspect the exact layers the builder would use, including present optionals."""
    records, failures, absent_optional = [], [], []
    for layer in build.applicable_layers(layer_set, state):
        try:
            path = build.layer_image_path(layer, state, layer_root)
            if not path.exists() and not path.is_symlink():
                if layer.get("required", True):
                    failures.append(f"missing required layer {layer['id']}: {path}")
                else:
                    absent_optional.append(str(path))
                continue
            if not path.is_file():
                raise build.BuildError(f"layer {layer['id']}: expected PNG file: {path}")
            inspect_png(path, layer, layer_set["reference_canvas"],
                        layer_set.get("canvas_policy"))
            records.append({"id": layer["id"], "sha256": build.sha256_file(path)})
        except build.BuildError as error:
            failures.append(str(error))
    return records, failures, absent_optional


def unexpected_layer_pngs(layer_set: dict, layer_root: Path, states: list[str]) -> list[str]:
    """Other states' declared assets are allowed, but no undeclared authored PNGs."""
    allowed = {build.layer_image_path(layer, state, layer_root)
               for state in states for layer in build.applicable_layers(layer_set, state)}
    failures = []
    for path in sorted(layer_root.rglob("*")):
        if path.is_symlink() and not path.resolve().is_relative_to(layer_root.resolve()):
            failures.append(f"source file outside asset_root via symlink: {path}")
        elif path.suffix.lower() == ".png" and path not in allowed:
            failures.append(f"unexpected authored PNG: {path}")
    return failures


def validate_runtime_source(source: dict, state: str, repo_root: Path,
                            config: dict | None = None) -> list[str]:
    """Recompute a published state's source binding from current authored inputs."""
    if not isinstance(source, dict):
        return ["manifest source must be an object"]
    if config is None:
        config = build.load_config(repo_root / DEFAULT_CONFIG)
    source_file = config["source_file"]
    if source.get("mode") != "layered":
        base = repo_root / config["source_root"] / state / source_file
        if source.get("file") != source_file or source.get("sha256") != build.sha256_file(base):
            return [f"manifest source binding does not match {source_file}"]
        return []
    expected_layer_set = config.get("layer_set")
    if expected_layer_set is None:
        return [f"animation set {build.config_spec_path(config)} declares no layer_set"]
    if source.get("layer_set") != expected_layer_set:
        return [f"wrong layer_set: expected {expected_layer_set}"]
    try:
        layer_set = build.load_layer_set(repo_root / expected_layer_set)
        build.assert_layer_set_binding(layer_set, config)
        layer_root = (repo_root / layer_set["asset_root"]).resolve()
        records, failures, _ = inspect_assets(layer_set, state, layer_root)
        failures += unexpected_layer_pngs(layer_set, layer_root, list(config["states"]))
        declared = source.get("layers")
        if not isinstance(declared, list) or any(
                not isinstance(entry, dict) or set(entry) != {"id", "sha256"}
                or not isinstance(entry["id"], str) for entry in declared):
            return failures + ["manifest source.layers must contain id/sha256 entries"]
        ids = [entry["id"] for entry in declared]
        expected_ids = [entry["id"] for entry in records]
        if len(set(ids)) != len(ids):
            failures.append("duplicate layer id in manifest source")
        if ids != expected_ids:
            failures.append(f"layer ids mismatch: declared {ids}; currently applicable authored "
                            f"layers {expected_ids} (missing, unknown, absent optional or out of order)")
        current = {entry["id"]: entry["sha256"] for entry in records}
        for entry in declared:
            if entry["id"] in current and entry["sha256"] != current[entry["id"]]:
                failures.append(f"layer {entry['id']}: SHA-256 mismatch")
        return failures
    except (build.BuildError, OSError, KeyError, TypeError, ValueError) as error:
        return [f"layered source check failed: {error}"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check authored PNG intake; never renders or publishes.")
    parser.add_argument("--config", default=DEFAULT_CONFIG,
                        help="animation set config, repo-relative (default: %(default)s)")
    parser.add_argument("--state", default="task_2", help="state to inspect (default: task_2)")
    args = parser.parse_args(argv)
    root = build.REPO_ROOT
    records, failures, optional = [], [], []
    try:
        config = build.load_config(root / args.config)
        if args.state not in config["states"]:
            raise build.BuildError(
                f"unknown state {args.state!r} in {build.config_spec_path(config)}; "
                f"declared states: {', '.join(config['states'])}")
        layer_set_path = config.get("layer_set")
        if layer_set_path is None:
            raise build.BuildError(
                f"animation set {build.config_spec_path(config)} declares no layer_set")
        layer_set = build.load_layer_set(root / layer_set_path)
        build.assert_layer_set_binding(layer_set, config)
        layer_root = (root / layer_set["asset_root"]).resolve()
        records, failures, optional = inspect_assets(layer_set, args.state, layer_root)
        failures += unexpected_layer_pngs(layer_set, layer_root, list(config["states"]))
    except (build.BuildError, OSError, KeyError, TypeError, ValueError) as error:
        failures.append(str(error))
    print("ART ASSET REQUIRED" if failures else "READY")
    print(f"{args.config} :: {args.state}: {len(records)} valid authored layer PNG(s)")
    for failure in failures:
        print("- " + failure.replace(str(root) + "/", ""))
    if optional:
        print("Optional layers absent (not blockers):")
        for path in optional:
            print("- " + path.replace(str(root) + "/", ""))
    print("Intake checks only; alignment, static reconstruction and visual QA still require review.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
