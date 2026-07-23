#!/usr/bin/env python3
"""Audit small-size clarity and frame uniqueness for the independent Q version."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = PIPELINE_ROOT.parent / "ready-to-use"
QA_DIR = PIPELINE_ROOT / "qa"
CELL_W, CELL_H = 192, 208
FRAME_COUNTS = (7, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8)
STATE_NAMES = (
    "idle",
    "running-right",
    "running-left",
    "waving",
    "jumping",
    "failed",
    "waiting",
    "running",
    "review",
    "look-000-to-157.5",
    "look-180-to-337.5",
)


def audit_atlas(path: Path) -> dict:
    atlas = Image.open(path).convert("RGBA")
    edge_scores: list[float] = []
    widths: list[int] = []
    heights: list[int] = []
    state_reports: list[dict] = []
    all_unique = True

    for row, (state, count) in enumerate(zip(STATE_NAMES, FRAME_COUNTS)):
        frames: list[np.ndarray] = []
        digests: set[bytes] = set()
        for column in range(count):
            image = atlas.crop(
                (
                    column * CELL_W,
                    row * CELL_H,
                    (column + 1) * CELL_W,
                    (row + 1) * CELL_H,
                )
            )
            array = np.asarray(image)
            frames.append(array.astype(np.int16))
            digests.add(image.tobytes())
            alpha = array[:, :, 3]
            x, y, width, height = cv2.boundingRect((alpha > 8).astype(np.uint8))
            widths.append(int(width))
            heights.append(int(height))
            gray = cv2.cvtColor(array[:, :, :3], cv2.COLOR_RGB2GRAY)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            visible = alpha > 32
            edge_scores.append(float(np.abs(laplacian[visible]).mean()))

        adjacent = [
            float(np.abs(frames[index] - frames[(index + 1) % count]).mean())
            for index in range(count)
        ]
        unique = len(digests)
        all_unique &= unique == count
        state_reports.append(
            {
                "state": state,
                "frames": count,
                "unique_frames": unique,
                "adjacent_mae_min": round(min(adjacent), 2),
                "adjacent_mae_max": round(max(adjacent), 2),
            }
        )

    report = {
        "atlas": path.name,
        "mean_edge_acuity": round(float(np.mean(edge_scores)), 2),
        "median_subject_width": round(float(np.median(widths)), 1),
        "median_subject_height": round(float(np.median(heights)), 1),
        "max_subject_width": max(widths),
        "max_subject_height": max(heights),
        "all_frames_unique_within_state": all_unique,
        "states": state_reports,
    }
    return report


def main() -> int:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    current = audit_atlas(RELEASE_DIR / "spritesheet.webp")
    comparison_path = PIPELINE_ROOT.parent.parent.parent / "codex" / "spritesheet.webp"
    comparison = audit_atlas(comparison_path) if comparison_path.is_file() else None
    errors: list[str] = []
    if current["mean_edge_acuity"] < 80:
        errors.append("缩小后的平均边缘清晰度低于 80")
    if current["max_subject_width"] > 168 or current["max_subject_height"] > 178:
        errors.append("角色超出第二版 168×178 安全尺寸")
    if not current["all_frames_unique_within_state"]:
        errors.append("存在重复帧")
    if comparison and current["mean_edge_acuity"] <= comparison["mean_edge_acuity"]:
        errors.append("第二版未比第一版更清晰")

    report = {
        "ok": not errors,
        "errors": errors,
        "current": current,
        "comparison_v1": comparison,
        "edge_acuity_gain": (
            round(current["mean_edge_acuity"] / comparison["mean_edge_acuity"], 2)
            if comparison
            else None
        ),
    }
    output = QA_DIR / "quality-report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
