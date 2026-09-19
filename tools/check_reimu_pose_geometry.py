#!/usr/bin/env python3
"""Read-only geometry checks for an authored pose family.

`check_reimu_layer_assets.py` proves the right PNGs exist and are well-formed
canvases. This tool checks the three defect classes that actually caused rework
in this repository and that a file-level check cannot see:

1. a support edge that does not sit on the contracted ground line, which makes
   the pose float or sink when the app aligns it with the standing shoe line;
2. palette drift, which passes every geometric check while quietly turning the
   character into a different one;
3. alpha noise from exporting antialiased edges over white.

An `eye_cover` check (closed eyes must cover the open-eye footprint) was also
removed. It assumed the head layer had eye rendering baked into it, so a closed
layer had to hide it. The approved head's sockets are plain skin, so the closed
layer only draws lashes and correctly covers 4301 fewer pixels than the open one.
The check failed working artwork. Both it and `clean_sockets` came from taking a
written description of a defect as fact instead of measuring the pixels first.

The constraints live in the layer set's `geometry` block, not in this file, so a
new pose family declares its own numbers. Nothing is rendered or published.
"""

from __future__ import annotations

import argparse
from pathlib import Path

if __package__:
    from . import build_reimu_animations as build
    from . import check_reimu_layer_assets as intake
else:
    import build_reimu_animations as build
    import check_reimu_layer_assets as intake


def load_mask(path: Path, threshold: int = 128):
    from PIL import Image
    with Image.open(path) as image:
        image.load()
        rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    return rgba, alpha.point(lambda v: 255 if v >= threshold else 0)


def check_support_edge(paths: dict[str, Path], rule: dict) -> list[str]:
    layer = rule["layer"]
    if layer not in paths:
        return []
    _, mask = load_mask(paths[layer])
    box = mask.getbbox()
    if box is None:
        return [f"{layer}: layer is empty, cannot measure a support edge"]
    bottom = box[3] - 1
    want, tolerance = rule["y"], rule.get("tolerance", 0)
    if abs(bottom - want) > tolerance:
        return [f"{layer}: support edge is y={bottom}, contract says y={want} "
                f"(tolerance {tolerance}); the pose will float or sink against the standing pose"]
    return []


def check_palette(paths: dict[str, Path], rule: dict) -> list[str]:
    """Each layer must actually contain the approved colour of its material.

    Measured as the share of the layer's opaque pixels lying within `tolerance`
    of a reference sampled from the approved eating rig. Presence, not dominance:
    a dominant-colour test picks whichever shade happens to be most numerous — the
    bow's white lace, or a shadow red — and cannot tell drift from shading.

    This replaced a `clean_sockets` check that looked for near-white pixels inside
    the eye-socket box. That test was wrong for this artwork: the approved face
    skin has a mean of 229 and the bow's lace is pure white, so no luma threshold
    separates sclera from skin or frills. It reported 434 defects in artwork that
    has none, while the drift that actually failed review went unnoticed.
    """
    from PIL import Image
    references = rule.get("references") or {}
    tolerance = rule.get("tolerance", 18)
    failures = []
    for layer_id, expected in sorted((rule.get("layers") or {}).items()):
        if layer_id not in paths:
            continue
        reference = references.get(expected)
        if reference is None:
            failures.append(f"{layer_id}: unknown palette reference {expected!r}")
            continue
        colour = reference["colour"]
        floor = reference.get("min_fraction", 0.05)
        with Image.open(paths[layer_id]) as image:
            image.load()
            pixels = list(image.convert("RGBA").getdata())
        opaque = [p for p in pixels if p[3] >= 200]
        if not opaque:
            failures.append(f"{layer_id}: layer has no opaque pixels to check")
            continue
        matching = sum(1 for red, green, blue, _ in opaque
                       if max(abs(red - colour[0]), abs(green - colour[1]),
                              abs(blue - colour[2])) <= tolerance)
        share = matching / len(opaque)
        if share < floor:
            failures.append(
                f"{layer_id}: only {share:.1%} of its opaque pixels are the approved "
                f"{expected} {tuple(colour)} (within {tolerance}); the contract requires "
                f"at least {floor:.0%}. The material is off-palette")
    return failures


def isolated_speckles(path: Path, below: int, radius: int = 7) -> int:
    """Faint pixels further than `radius` from anything solid.

    A soft edge is faint but hugs the shape it belongs to, so it is not counted;
    this repository's approved layers feather up to about three pixels wide.
    Export noise is faint and floats far from any shape, which is the defect.
    """
    from PIL import Image, ImageChops, ImageFilter
    with Image.open(path) as image:
        image.load()
        alpha = image.convert("RGBA").getchannel("A")
    faint = alpha.point(lambda v: 255 if 0 < v < below else 0)
    solid = alpha.point(lambda v: 255 if v >= 128 else 0)
    near_solid = solid.filter(ImageFilter.MaxFilter(radius))
    return sum(1 for v in ImageChops.subtract(faint, near_solid).getdata() if v)


def check_alpha_hygiene(paths: dict[str, Path], rule: dict) -> list[str]:
    below = rule.get("speckle_alpha_below", 8)
    limit = rule.get("max_speckle_px", 0)
    radius = rule.get("isolation_radius", 7)
    failures = []
    for layer_id, path in sorted(paths.items()):
        speckles = isolated_speckles(path, below, radius)
        if speckles > limit:
            failures.append(f"{layer_id}: {speckles} isolated pixel(s) with alpha in "
                            f"1..{below - 1} more than {radius // 2}px from anything solid "
                            f"(limit {limit}); "
                            f"export real transparency, not antialiasing over white")
    return failures


def composite(order: list, paths: dict[str, Path], exclude: set, background: tuple):
    from PIL import Image
    canvas = None
    for layer_id in order:
        if layer_id in exclude or layer_id not in paths:
            continue
        with Image.open(paths[layer_id]) as image:
            image.load()
            rgba = image.convert("RGBA")
        if canvas is None:
            canvas = Image.new("RGBA", rgba.size, tuple(background) + (255,))
        canvas.alpha_composite(rgba)
    return canvas


def check_legible_at(paths: dict[str, Path], rule: dict, order: list | None = None) -> list[str]:
    """A layer that carries the pose's meaning must survive the real display size.

    The pet is shown at 160 px, where a small limb can vanish entirely. Each named
    layer is removed from the composite and the two versions are downscaled; if too
    few pixels move, the layer is not readable at that size and the pose does not
    communicate what it is supposed to.
    """
    if order is None:
        return []
    from PIL import Image
    size = rule.get("size", 160)
    floor = rule.get("min_changed_px", 100)
    delta = rule.get("min_channel_delta", 12)
    exclude = set(rule.get("exclude", []))
    background = rule.get("background", [250, 248, 245])
    failures = []
    for layer_id in rule.get("layers", []):
        if layer_id not in paths:
            continue
        full = composite(order, paths, exclude, background)
        without = composite(order, paths, exclude | {layer_id}, background)
        if full is None or without is None:
            continue
        a = full.convert("RGB").resize((size, size), Image.LANCZOS).getdata()
        b = without.convert("RGB").resize((size, size), Image.LANCZOS).getdata()
        moved = sum(1 for x, y in zip(a, b)
                    if max(abs(x[0] - y[0]), abs(x[1] - y[1]), abs(x[2] - y[2])) >= delta)
        if moved < floor:
            failures.append(f"{layer_id}: changes only {moved} pixel(s) at {size}px "
                            f"(floor {floor}); it is invisible at the size the pet is "
                            f"actually displayed, so the pose does not read")
    return failures


def check_joins(paths: dict[str, Path], rule: dict) -> list[str]:
    """Limbs must actually meet. A forearm that stops short of its hand reads as broken."""
    from PIL import ImageFilter
    failures = []
    for pair in rule.get("pairs", []):
        first, second = pair["a"], pair["b"]
        if first not in paths or second not in paths:
            continue
        _, mask_a = load_mask(paths[first])
        _, mask_b = load_mask(paths[second])
        grown = mask_a.filter(ImageFilter.MaxFilter(pair.get("radius", 3)))
        shared = sum(1 for x, y in zip(grown.getdata(), mask_b.getdata()) if x and y)
        floor = pair.get("min_px", rule.get("min_px", 600))
        if shared < floor:
            failures.append(f"{first} and {second} share only {shared} adjacent pixel(s) "
                            f"(floor {floor}); the limb does not connect")
    return failures


CHECKS = {
    "support_edge": check_support_edge,
    "palette": check_palette,
    "alpha_hygiene": check_alpha_hygiene,
    "joins": check_joins,
}
# Needs the z-order, so it is dispatched separately from the pairwise checks.
ORDERED_CHECKS = {"legible_at": check_legible_at}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default=intake.DEFAULT_CONFIG,
                        help="animation set config, repo-relative (default: %(default)s)")
    parser.add_argument("--state", required=True, help="state to inspect")
    args = parser.parse_args(argv)
    root = build.REPO_ROOT
    failures, pending, checked, paths = [], [], [], {}
    try:
        config = build.load_config(root / args.config)
        if args.state not in config["states"]:
            raise build.BuildError(f"unknown state {args.state!r} in {build.config_spec_path(config)}")
        layer_set = build.load_layer_set(root / config["layer_set"])
        build.assert_layer_set_binding(layer_set, config)
        geometry = layer_set.get("geometry")
        if not geometry:
            raise build.BuildError(
                f"{config['layer_set']} declares no 'geometry' contract to check")
        layer_root = (root / layer_set["asset_root"]).resolve()
        for layer in build.applicable_layers(layer_set, args.state):
            path = build.layer_image_path(layer, args.state, layer_root)
            if path.is_file():
                paths[layer["id"]] = path
            elif layer.get("required", True):
                pending.append(layer["id"])
        order = [layer["id"] for layer in build.applicable_layers(layer_set, args.state)]
        for name, rule in geometry.items():
            if name in CHECKS:
                failures.extend(CHECKS[name](paths, rule))
            elif name in ORDERED_CHECKS:
                failures.extend(ORDERED_CHECKS[name](paths, rule, order))
            else:
                continue
            checked.append(name)
    except (build.BuildError, OSError, KeyError, TypeError, ValueError) as error:
        failures.append(str(error))
    except ImportError:
        failures.append("geometry checks require Pillow; use the Sprite Harness venv's Python")

    print("GEOMETRY FAILED" if failures else ("PENDING ART" if pending else "GEOMETRY OK"))
    print(f"{args.config} :: {args.state}: {len(paths)} layer(s) present, "
          f"checks run: {', '.join(checked) or 'none'}")
    for failure in failures:
        print("- " + str(failure).replace(str(root) + "/", ""))
    if pending:
        print("Required layers not authored yet (geometry not asserted for them):")
        for layer_id in pending:
            print("- " + layer_id)
    print("Geometry checks only; identity, palette and readability still require visual review.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
