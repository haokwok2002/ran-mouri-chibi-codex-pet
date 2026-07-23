#!/usr/bin/env python3
"""Prepare a source illustration as a clean green-screen pet identity reference.

This deterministic helper keeps the supplied character art, isolates its central
foreground, and places it on a flat #00FF00 canvas. It does not call an image
service or read any environment configuration.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


CHROMA_GREEN_BGR = (0, 255, 0)


def largest_center_component(mask: np.ndarray) -> np.ndarray:
    """Keep the foreground component containing the image center when possible."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if count <= 1:
        raise ValueError("Unable to find a foreground component.")

    height, width = mask.shape
    center_label = labels[height // 2, width // 2]
    if center_label != 0:
        selected = center_label
    else:
        selected = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return np.where(labels == selected, 255, 0).astype(np.uint8)


def extract_subject(image: np.ndarray) -> np.ndarray:
    """Use GrabCut plus a center-component filter to remove source background."""
    height, width = image.shape[:2]
    mask = np.zeros((height, width), np.uint8)
    inset_x = max(2, round(width * 0.18))
    inset_y = max(2, round(height * 0.02))
    rect = (inset_x, inset_y, width - inset_x * 2, height - inset_y - 2)
    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(image, mask, rect, bg_model, fg_model, 8, cv2.GC_INIT_WITH_RECT)
    foreground = np.where(
        (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0
    ).astype(np.uint8)
    foreground = largest_center_component(foreground)
    foreground = cv2.morphologyEx(
        foreground, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1
    )
    # Source illustrations sometimes contain a floor shadow touching the shoes.
    # A pet source must not carry that detached ground effect into its chroma
    # frame. Preserve the two expected shoe silhouettes and clear everything
    # else below the natural foot line.
    height = image.shape[0]
    width = image.shape[1]
    dark_lower_band = np.zeros_like(foreground)
    lower_start = round(height * 0.90)
    dark_lower_band[lower_start:, :] = 255
    shoe_keep = np.zeros_like(foreground)
    cv2.ellipse(
        shoe_keep,
        (round(width * 0.415), round(height * 0.935)),
        (round(width * 0.077), round(height * 0.036)),
        0,
        0,
        360,
        255,
        -1,
    )
    cv2.ellipse(
        shoe_keep,
        (round(width * 0.548), round(height * 0.940)),
        (round(width * 0.066), round(height * 0.037)),
        0,
        0,
        360,
        255,
        -1,
    )
    foreground[(dark_lower_band > 0) & (shoe_keep == 0)] = 0
    return foreground


def compose_green_reference(
    source: np.ndarray, mask: np.ndarray, canvas_width: int, canvas_height: int
) -> tuple[np.ndarray, dict[str, int]]:
    """Crop the isolated subject, preserve margins, and center it on chroma green."""
    points = cv2.findNonZero(mask)
    if points is None:
        raise ValueError("Foreground mask is empty.")
    x, y, width, height = cv2.boundingRect(points)
    source_crop = source[y : y + height, x : x + width]
    mask_crop = mask[y : y + height, x : x + width]

    max_width = round(canvas_width * 0.68)
    max_height = round(canvas_height * 0.74)
    scale = min(max_width / width, max_height / height)
    target_width = max(1, round(width * scale))
    target_height = max(1, round(height * scale))
    subject = cv2.resize(source_crop, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
    alpha = cv2.resize(mask_crop, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

    result = np.full((canvas_height, canvas_width, 3), CHROMA_GREEN_BGR, dtype=np.uint8)
    left = (canvas_width - target_width) // 2
    top = (canvas_height - target_height) // 2
    roi = result[top : top + target_height, left : left + target_width]
    alpha_f = (alpha.astype(np.float32) / 255.0)[..., None]
    roi[:] = np.round(subject * alpha_f + roi * (1.0 - alpha_f)).astype(np.uint8)
    return result, {
        "subject_left": left,
        "subject_top": top,
        "subject_width": target_width,
        "subject_height": target_height,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1536)
    args = parser.parse_args()

    image = cv2.imread(str(args.input), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Cannot read input image: {args.input}")
    mask = extract_subject(image)
    output, placement = compose_green_reference(image, mask, args.width, args.height)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.output), output):
        raise OSError(f"Cannot write output image: {args.output}")

    border = np.concatenate((output[0], output[-1], output[:, 0], output[:, -1]))
    report = {
        "ok": bool(np.all(border == np.array(CHROMA_GREEN_BGR))),
        "input": str(args.input),
        "output": str(args.output),
        "canvas": {"width": args.width, "height": args.height},
        "background_bgr": list(CHROMA_GREEN_BGR),
        "foreground_pixels": int(np.count_nonzero(mask)),
        "placement": placement,
        "method": "grabcut-central-foreground-plus-flat-chroma-composite",
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[完成] 写入绿幕参考图：{args.output}")
    print(f"[完成] 写入检查报告：{args.report}")


if __name__ == "__main__":
    main()
