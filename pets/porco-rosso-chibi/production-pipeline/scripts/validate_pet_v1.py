#!/usr/bin/env python3
"""Validate the local Codex Pet V1 package."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image


PIPELINE = Path(__file__).resolve().parents[1]
RELEASE = PIPELINE.parent / "ready-to-use"
QA = PIPELINE / "qa"
COUNTS = (7, 8, 8, 4, 5, 8, 6, 6, 6)
NAMES = ("idle", "running-right", "running-left", "waving", "jumping", "failed", "waiting", "running", "review")
CELL_W, CELL_H = 192, 208
TARGET_TORSO_X = 96
JUMP_BOTTOMS = (193, 187, 178, 186, 193)
JUMP_TOP_MARGIN = 4


def torso_anchor_x(cell: Image.Image) -> float:
    """Find the central lower-torso anchor without being biased by limbs."""
    alpha = np.asarray(cell.getchannel("A")) > 16
    bbox = cell.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("空白动作格")
    start = round(bbox[1] + (bbox[3] - bbox[1]) * 0.42)
    end = round(bbox[1] + (bbox[3] - bbox[1]) * 0.82)
    _, xs = np.where(alpha[start:end, :])
    return float(np.median(xs)) if len(xs) else (bbox[0] + bbox[2]) / 2


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    manifest = json.loads((RELEASE / "pet.json").read_text(encoding="utf-8"))
    required = {"id", "displayName", "description", "spritesheetPath"}
    missing = sorted(required - set(manifest))
    if missing:
        errors.append(f"pet.json 缺少：{', '.join(missing)}")
    if "spriteVersionNumber" in manifest:
        errors.append("V1 pet.json 不应包含 spriteVersionNumber")
    atlas_file = RELEASE / manifest.get("spritesheetPath", "spritesheet.webp")
    source = Image.open(atlas_file)
    image_format = source.format
    atlas = source.convert("RGBA")
    if image_format != "WEBP":
        errors.append(f"图集格式应为 WEBP，实际为 {image_format}")
    if atlas.size != (1536, 1872):
        errors.append(f"图集尺寸应为 1536×1872，实际为 {atlas.size}")
    cells = []
    alignment: dict[str, list[dict]] = {}
    if not errors:
        for row, (name, count) in enumerate(zip(NAMES, COUNTS)):
            alignment[name] = []
            for col in range(8):
                cell = atlas.crop((col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H))
                alpha = cell.getchannel("A")
                visible = sum(value > 8 for value in alpha.getdata())
                used = col < count
                if used and visible < 350:
                    errors.append(f"{name}[{col}] 像素不足：{visible}")
                if not used and visible:
                    errors.append(f"{name}[{col}] 应为空，实际可见像素：{visible}")
                if used:
                    bbox = alpha.getbbox()
                    anchor = torso_anchor_x(cell)
                    expected_bottom = JUMP_BOTTOMS[col] if name == "jumping" else 193
                    if abs(anchor - TARGET_TORSO_X) > 1:
                        errors.append(f"{name}[{col}] 躯干横向锚点漂移：{anchor:.2f}")
                    if bbox and bbox[3] != expected_bottom:
                        errors.append(f"{name}[{col}] 脚底/跳跃轨迹错误：{bbox[3]}，应为 {expected_bottom}")
                    if name == "jumping" and bbox and bbox[1] < JUMP_TOP_MARGIN:
                        errors.append(f"{name}[{col}] 帽子顶部空间不足：{bbox[1]}，至少应为 {JUMP_TOP_MARGIN}")
                    alignment[name].append({"frame": col + 1, "torso_anchor_x": round(anchor, 2), "bottom": bbox[3] if bbox else None})
                cells.append({"row": row, "column": col, "state": name, "used": used, "nontransparent_pixels": visible})
        chroma = sum(1 for r, g, b, a in atlas.getdata() if a > 32 and g > 150 and g > r * 1.8 and g > b * 1.8)
        if chroma:
            warnings.append(f"疑似绿幕残边像素：{chroma}")
    report = {"ok": not errors, "file": atlas_file.name, "format": image_format, "mode": atlas.mode, "columns": 8, "rows": 9, "sprite_version_number": 1, "width": atlas.width, "height": atlas.height, "errors": errors, "warnings": warnings, "alignment": alignment, "cells": cells}
    QA.mkdir(parents=True, exist_ok=True)
    (QA / "pet-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
