#!/usr/bin/env python3
"""Validate the local pet package and every V2 atlas cell."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = PIPELINE_ROOT.parent / "ready-to-use"
QA_DIR = PIPELINE_ROOT / "qa"
CELL_W, CELL_H = 192, 208
COLS, ROWS = 8, 11
EXPECTED_USED = (7, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8)
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
TARGET_BODY_CENTER_X = 96
TARGET_GROUND_Y = 193
GROUNDED_ROWS = {0, 3, 5, 6, 7, 8, 9, 10}


def skirt_anchor_x(cell: Image.Image) -> float:
    pixels = np.asarray(cell.convert("RGBA"))
    red, green, blue, alpha = [pixels[:, :, index] for index in range(4)]
    yy, _ = np.indices(alpha.shape)
    mask = (
        (alpha > 180)
        & (red < 175)
        & (green < 185)
        & (blue < 220)
        & (blue > red * 0.92)
        & (yy > 75)
        & (yy < 175)
    ).astype(np.uint8)
    count, _, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
    candidates = [
        (int(stats[label, cv2.CC_STAT_AREA]), float(centroids[label][0]))
        for label in range(1, count)
        if int(stats[label, cv2.CC_STAT_AREA]) > 80
    ]
    if not candidates:
        bbox = cell.getchannel("A").getbbox()
        if not bbox:
            raise ValueError("空白动作格")
        return (bbox[0] + bbox[2]) / 2
    return max(candidates)[1]


def main() -> int:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = RELEASE_DIR / "pet.json"
    atlas_path = RELEASE_DIR / "spritesheet.webp"

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"pet.json 无法读取：{exc}", file=sys.stderr)
        return 1

    for key in ("id", "displayName", "description", "spriteVersionNumber", "spritesheetPath"):
        if key not in manifest:
            errors.append(f"pet.json 缺少 {key}")
    if manifest.get("spriteVersionNumber") != 2:
        errors.append("spriteVersionNumber 必须为 2")
    if manifest.get("spritesheetPath") != "spritesheet.webp":
        errors.append("spritesheetPath 必须为 spritesheet.webp")

    try:
        atlas = Image.open(atlas_path)
        atlas.load()
        image_format = atlas.format
        atlas = atlas.convert("RGBA")
    except Exception as exc:
        errors.append(f"spritesheet.webp 无法读取：{exc}")
        atlas = Image.new("RGBA", (1, 1))
        image_format = None

    if image_format != "WEBP":
        errors.append(f"图集格式必须为 WEBP，实际为 {image_format}")
    if atlas.size != (COLS * CELL_W, ROWS * CELL_H):
        errors.append(f"图集尺寸必须为 1536×2288，实际为 {atlas.width}×{atlas.height}")

    transparent_rgb_residue = 0
    chroma_residue = 0
    if atlas.size == (COLS * CELL_W, ROWS * CELL_H):
        for r, g, b, a in atlas.getdata():
            if a == 0 and (r or g or b):
                transparent_rgb_residue += 1
            if a >= 32 and g > 145 and g > r * 1.8 and g > b * 1.8:
                chroma_residue += 1
        if transparent_rgb_residue:
            errors.append(f"透明像素中残留 RGB：{transparent_rgb_residue}")
        if chroma_residue:
            warnings.append(f"疑似绿幕残边像素：{chroma_residue}")

    cells = []
    alignment = []
    if atlas.size == (COLS * CELL_W, ROWS * CELL_H):
        for row in range(ROWS):
            for column in range(COLS):
                cell = atlas.crop(
                    (
                        column * CELL_W,
                        row * CELL_H,
                        (column + 1) * CELL_W,
                        (row + 1) * CELL_H,
                    )
                )
                visible = sum(value > 8 for value in cell.getchannel("A").getdata())
                used = column < EXPECTED_USED[row]
                if used and visible < 350:
                    errors.append(f"{STATE_NAMES[row]}[{column}] 可见像素过少：{visible}")
                if not used and visible:
                    errors.append(f"{STATE_NAMES[row]}[{column}] 应为空，实际有 {visible} 个可见像素")
                cells.append(
                    {
                        "row": row,
                        "column": column,
                        "state": STATE_NAMES[row],
                        "used": used,
                        "nontransparent_pixels": visible,
                    }
                )

        for row, state in enumerate(STATE_NAMES):
            cell = atlas.crop((0, row * CELL_H, CELL_W, (row + 1) * CELL_H))
            bbox = cell.getchannel("A").getbbox()
            if not bbox:
                continue
            body_center_x = skirt_anchor_x(cell)
            ground_y = bbox[3]
            if abs(body_center_x - TARGET_BODY_CENTER_X) > 1.5:
                errors.append(
                    f"{state} 首帧身体中心未对齐：{body_center_x:.2f}"
                )
            if ground_y != TARGET_GROUND_Y:
                errors.append(f"{state} 首帧脚底未对齐：{ground_y}")
            alignment.append(
                {
                    "state": state,
                    "first_frame_body_center_x": round(body_center_x, 2),
                    "first_frame_ground_y": ground_y,
                }
            )

        for row in GROUNDED_ROWS:
            bottoms = []
            for column in range(EXPECTED_USED[row]):
                cell = atlas.crop(
                    (
                        column * CELL_W,
                        row * CELL_H,
                        (column + 1) * CELL_W,
                        (row + 1) * CELL_H,
                    )
                )
                bbox = cell.getchannel("A").getbbox()
                if bbox:
                    bottoms.append(bbox[3])
            if bottoms and any(bottom != TARGET_GROUND_Y for bottom in bottoms):
                errors.append(
                    f"{STATE_NAMES[row]} 站定帧脚底漂移：{bottoms}"
                )

        jump_last = atlas.crop(
            (4 * CELL_W, 4 * CELL_H, 5 * CELL_W, 5 * CELL_H)
        ).getchannel("A").getbbox()
        if jump_last and jump_last[3] != TARGET_GROUND_Y:
            errors.append(f"jumping 落地帧未回到基线：{jump_last[3]}")

    report = {
        "ok": not errors,
        "file": atlas_path.name,
        "format": image_format,
        "mode": "RGBA",
        "columns": COLS,
        "rows": ROWS,
        "sprite_version_number": manifest.get("spriteVersionNumber"),
        "width": atlas.width,
        "height": atlas.height,
        "transparent_rgb_residue_pixels": transparent_rgb_residue,
        "chroma_fringe_pixels": chroma_residue,
        "errors": errors,
        "warnings": warnings,
        "runtime_anchor": {
            "target_body_center_x": TARGET_BODY_CENTER_X,
            "target_ground_y": TARGET_GROUND_Y,
            "states": alignment,
        },
        "cells": cells,
    }
    output = QA_DIR / "pet-validation.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("ok", "format", "width", "height", "errors", "warnings")}, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
