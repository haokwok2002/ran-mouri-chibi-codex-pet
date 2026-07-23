#!/usr/bin/env python3
"""Audit V1 frame uniqueness, clarity, and safe cell size."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image


PIPELINE = Path(__file__).resolve().parents[1]
ATLAS = PIPELINE.parent / "ready-to-use" / "spritesheet.webp"
OUT = PIPELINE / "qa" / "quality-report.json"
COUNTS = (7, 8, 8, 4, 5, 8, 6, 6, 6)
NAMES = ("idle", "running-right", "running-left", "waving", "jumping", "failed", "waiting", "running", "review")


def subject_size(alpha: np.ndarray) -> tuple[int, int]:
    ys, xs = np.where(alpha > 8)
    if not len(xs):
        return 0, 0
    return int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


def edge_acuity(rgb: np.ndarray, visible: np.ndarray) -> float:
    gray = rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.114
    padded = np.pad(gray, 1, mode="edge")
    laplacian = (
        padded[:-2, 1:-1]
        + padded[2:, 1:-1]
        + padded[1:-1, :-2]
        + padded[1:-1, 2:]
        - 4 * gray
    )
    return float(np.abs(laplacian[visible]).mean())


def main() -> None:
    atlas = Image.open(ATLAS).convert("RGBA")
    state_reports, errors, acuity, sizes = [], [], [], []
    for row, (name, count) in enumerate(zip(NAMES, COUNTS)):
        frames, digests = [], set()
        for col in range(count):
            frame = atlas.crop((col * 192, row * 208, (col + 1) * 192, (row + 1) * 208))
            array = np.asarray(frame)
            frames.append(array.astype(np.int16))
            digests.add(frame.tobytes())
            alpha = array[:, :, 3]
            w, h = subject_size(alpha)
            sizes.append((int(w), int(h)))
            visible = alpha > 32
            acuity.append(edge_acuity(array[:, :, :3].astype(np.float64), visible))
        adjacent = [float(np.abs(frames[i] - frames[(i + 1) % count]).mean()) for i in range(count)]
        unique = len(digests)
        if unique != count:
            errors.append(f"{name} 存在重复帧：{unique}/{count}")
        state_reports.append({"state": name, "frames": count, "unique_frames": unique, "adjacent_mae_min": round(min(adjacent), 2), "adjacent_mae_max": round(max(adjacent), 2)})
    report = {"ok": not errors, "atlas": ATLAS.name, "mean_edge_acuity": round(float(np.mean(acuity)), 2), "max_subject_width": max(w for w, _ in sizes), "max_subject_height": max(h for _, h in sizes), "errors": errors, "states": state_reports}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
