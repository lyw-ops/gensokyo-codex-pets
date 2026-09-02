#!/usr/bin/env python3
"""Split the approved Eating Set v1 six-panel sheet into runtime sprites.

Reads docs/reference/reimu/eating_set_v1/eating-set-v1-sheet.png and writes
assets/reimu/eating/<state>/base.png. Deterministic, purely mechanical:
alpha-connectivity segmentation, nearest-panel assignment of floating
effects, and bottom-center placement on a fixed square canvas. No pixels
are repainted or rescaled.

Requires: pillow, numpy, scipy.
"""

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

REPO = Path(__file__).resolve().parent.parent
SHEET = REPO / "docs/reference/reimu/eating_set_v1/eating-set-v1-sheet.png"
OUT_DIR = REPO / "assets/reimu/eating"
STATE_IDS = ["idle", "task_1", "task_2", "task_3", "task_4", "task_5"]

ALPHA_THRESHOLD = 8      # alpha > threshold counts as content
BIG_COMPONENT_PX = 50000  # a full panel is far larger than any floating effect
CANVAS = 596
BOTTOM_MARGIN = 10


def split_merged(component: np.ndarray) -> list[np.ndarray]:
    """Split one connected blob holding two panels via erosion-seeded watershed."""
    for iterations in range(1, 60):
        eroded = ndimage.binary_erosion(component, iterations=iterations)
        labels, count = ndimage.label(eroded)
        sizes = ndimage.sum(eroded, labels, range(1, count + 1))
        seeds = sorted(
            ((i + 1, s) for i, s in enumerate(sizes) if s > 30000),
            key=lambda t: -t[1],
        )[:2]
        if len(seeds) == 2:
            break
    else:
        raise SystemExit("could not split merged panels; sheet layout changed?")
    seed_masks = [labels == cid for cid, _ in seeds]
    seed_masks.sort(key=lambda m: np.where(m)[1].mean())  # left panel first
    distances = [ndimage.distance_transform_edt(~m) for m in seed_masks]
    left = component & (distances[0] <= distances[1])
    return [left, component & ~left]


def main() -> None:
    image = np.array(Image.open(SHEET).convert("RGBA"))
    mask = image[..., 3] > ALPHA_THRESHOLD
    labels, count = ndimage.label(mask)
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    big_ids = [i + 1 for i, s in enumerate(sizes) if s > BIG_COMPONENT_PX]

    panels: list[np.ndarray] = []
    for cid in big_ids:
        component = labels == cid
        # A component roughly twice panel size holds two touching panels.
        if sizes[cid - 1] > 2.0 * np.median([sizes[i - 1] for i in big_ids if sizes[i - 1] < 250000]):
            panels.extend(split_merged(component))
        else:
            panels.append(component)
    if len(panels) != 6:
        raise SystemExit(f"expected 6 panels, found {len(panels)}")
    # Reading order: sort by row band, then x.
    panels.sort(key=lambda m: (np.where(m)[0].mean() // 400, np.where(m)[1].mean()))

    # Attach every small component (hearts, sweat, steam, sparkles) to the
    # panel whose content is nearest to its centroid.
    panel_distance = [ndimage.distance_transform_edt(~m) for m in panels]
    for cid in range(1, count + 1):
        if cid in big_ids:
            continue
        ys, xs = np.where(labels == cid)
        cy, cx = int(ys.mean()), int(xs.mean())
        nearest = int(np.argmin([d[cy, cx] for d in panel_distance]))
        panels[nearest] |= labels == cid

    for state_id, panel in zip(STATE_IDS, panels):
        sprite = image.copy()
        sprite[~panel] = 0
        ys, xs = np.where(panel)
        sprite = sprite[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
        h, w = sprite.shape[:2]
        if h > CANVAS - BOTTOM_MARGIN or w > CANVAS:
            raise SystemExit(f"{state_id}: content {w}x{h} exceeds canvas {CANVAS}")
        canvas = np.zeros((CANVAS, CANVAS, 4), dtype=np.uint8)
        x0 = (CANVAS - w) // 2
        y0 = CANVAS - BOTTOM_MARGIN - h
        canvas[y0 : y0 + h, x0 : x0 + w] = sprite
        out = OUT_DIR / state_id / "base.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(canvas).save(out)
        print(f"{state_id}: {w}x{h} -> {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
