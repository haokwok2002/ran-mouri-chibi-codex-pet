#!/usr/bin/env python3
"""Normalize a generated chroma-key background to exact #00FF00.

Only green pixels connected to the canvas border are replaced. This keeps the
character and its antialiased outline intact while making the production
background deterministic for later key removal.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    image = cv2.imread(str(args.input), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Cannot read input image: {args.input}")
    blue, green, red = cv2.split(image)
    likely_key = ((green >= 150) & (red <= 95) & (blue <= 95)).astype(np.uint8)
    count, labels, _, _ = cv2.connectedComponentsWithStats(likely_key, connectivity=8)
    border_labels = set(labels[0, :]) | set(labels[-1, :]) | set(labels[:, 0]) | set(labels[:, -1])
    border_labels.discard(0)
    background = np.isin(labels, list(border_labels)) if border_labels else np.zeros_like(likely_key, dtype=bool)
    image[background] = (0, 255, 0)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.output), image):
        raise OSError(f"Cannot write output image: {args.output}")

    edge = np.concatenate((image[0], image[-1], image[:, 0], image[:, -1]))
    args.report.write_text(
        json.dumps(
            {
                "ok": bool(np.all(edge == np.array((0, 255, 0)))),
                "input": str(args.input),
                "output": str(args.output),
                "canvas": {"width": int(image.shape[1]), "height": int(image.shape[0])},
                "background_rgb": [0, 255, 0],
                "normalized_background_pixels": int(np.count_nonzero(background)),
                "method": "api-reference-image-plus-border-connected-chroma-normalization",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"[完成] 标准化绿幕：{args.output}")


if __name__ == "__main__":
    main()
