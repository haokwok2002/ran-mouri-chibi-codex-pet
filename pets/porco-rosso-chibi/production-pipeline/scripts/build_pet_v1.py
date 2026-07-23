#!/usr/bin/env python3
"""Build a Codex Pet V1 8x9 atlas from green-screen animation boards."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


PIPELINE = Path(__file__).resolve().parents[1]
PET_ROOT = PIPELINE.parent
SOURCE = PIPELINE / "source" / "sequences" / "matted"
RELEASE = PET_ROOT / "ready-to-use"
QA = PIPELINE / "qa"
CELL_W, CELL_H, COLS, ROWS = 192, 208, 8, 9
MAX_W, MAX_H, GROUND_Y = 168, 178, 193
SPECS = (
    ("idle", 4, 2, 7),
    ("running-right", 4, 2, 8),
    ("running-left", 4, 2, 8),
    ("waving", 2, 2, 4),
    ("jumping", 3, 2, 5),
    ("failed", 4, 2, 8),
    ("waiting", 3, 2, 6),
    ("running", 3, 2, 6),
    ("review", 3, 2, 6),
)
JUMP_BOTTOM_OFFSETS = (0, -6, -15, -7, 0)
# The apex still needs a small clear margin above the hat.  The earlier build
# let the tall airborne pose extend past y=0, silently cutting off its crown.
JUMP_TOP_MARGIN = 4


def clear_hidden_rgb(image: Image.Image) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA")).copy()
    rgba[rgba[:, :, 3] == 0, :3] = 0
    return Image.fromarray(rgba)


def clean_components(image: Image.Image) -> Image.Image:
    """Remove isolated matte speckles without requiring OpenCV.

    Each source board has already been chroma-matted.  A 5×5 neighbourhood
    support test removes tiny detached remnants while preserving the large
    hat, sunglasses, hands and complete character silhouette.
    """
    rgba = np.asarray(image.convert("RGBA")).copy()
    alpha = rgba[:, :, 3] > 8
    padded = np.pad(alpha.astype(np.uint8), 2)
    support = sum(
        padded[dy : dy + alpha.shape[0], dx : dx + alpha.shape[1]]
        for dy in range(5)
        for dx in range(5)
    )
    keep = alpha & (support >= 8)
    rgba[~keep] = 0
    return clear_hidden_rgb(Image.fromarray(rgba))


def board_frames(name: str, columns: int, rows: int, count: int, mirror: bool = False) -> list[Image.Image]:
    board = Image.open(SOURCE / f"{name}-green.png").convert("RGBA")
    if board.width % columns or board.height % rows:
        raise ValueError(f"{name} 分镜尺寸与网格不匹配：{board.size}")
    width, height = board.width // columns, board.height // rows
    frames = []
    for index in range(count):
        x, y = (index % columns) * width, (index // columns) * height
        frame = clean_components(board.crop((x, y, x + width, y + height)))
        if mirror:
            frame = frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if not frame.getchannel("A").getbbox():
            raise ValueError(f"{name}[{index}] 没有可见角色")
        frames.append(frame)
    return frames


def torso_anchor_x(frame: Image.Image) -> float:
    """Use the central lower torso, not swinging hands or feet, as x anchor."""
    alpha = np.asarray(frame.getchannel("A")) > 16
    bbox = frame.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("动作帧为空")
    top, bottom = bbox[1], bbox[3]
    start = round(top + (bottom - top) * 0.42)
    end = round(top + (bottom - top) * 0.82)
    ys, xs = np.where(alpha[start:end, :])
    if len(xs) < 100:
        return (bbox[0] + bbox[2]) / 2
    return float(np.median(xs))


def crop_visible(frame: Image.Image, padding: int = 8) -> tuple[Image.Image, tuple[int, int, int, int]]:
    bbox = frame.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("动作帧为空")
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(frame.width, bbox[2] + padding)
    bottom = min(frame.height, bbox[3] + padding)
    return frame.crop((left, top, right, bottom)), bbox


def fit_action(name: str, frames: list[Image.Image]) -> tuple[list[Image.Image], dict]:
    """Normalize every generated panel to one body scale and torso anchor.

    Image generation moves the character within each board cell. We deliberately
    register every frame by the torso and shoe baseline, while retaining the
    authored jump arc as small fixed vertical offsets.
    """
    prepared = [crop_visible(frame) for frame in frames]
    visible_heights = [bbox[3] - bbox[1] for _, bbox in prepared]
    reference_height = float(median(visible_heights))
    # Stationary and run cycles should not pulse in scale. A jump keeps a
    # shared scale, preserving its crouch/airborne silhouette rather than
    # stretching each pose to the same height.
    normalize_pose_height = name != "jumping"
    target_height = min(MAX_H, round(reference_height * min(MAX_H / reference_height, 1.0)))
    output = []
    records = []
    common_scale = min(MAX_H / reference_height, MAX_W / max(crop.width for crop, _ in prepared))
    if name == "jumping":
        # All jump poses share one scale, but the tallest airborne silhouette
        # must fit between the apex baseline and the hat-safe top margin.
        max_visible_height = max(visible_bbox[3] - visible_bbox[1] for _, visible_bbox in prepared)
        jump_safe_height = GROUND_Y + min(JUMP_BOTTOM_OFFSETS) - JUMP_TOP_MARGIN
        common_scale = min(common_scale, jump_safe_height / max_visible_height)
        # Resampling soft alpha adds a few pixels beyond the source bounding
        # box.  Measure the actual resized alpha and tighten the shared scale
        # until every jump pose, especially the apex, fits intact.
        for _ in range(8):
            fit_ratios = []
            for index, (crop, _) in enumerate(prepared):
                probe = crop.resize(
                    (max(1, round(crop.width * common_scale)), max(1, round(crop.height * common_scale))),
                    Image.Resampling.LANCZOS,
                )
                probe_bbox = probe.getchannel("A").getbbox()
                if not probe_bbox:
                    raise ValueError(f"{name}[{index}] 缩放探测后为空")
                allowed_height = GROUND_Y + JUMP_BOTTOM_OFFSETS[index] - JUMP_TOP_MARGIN
                fit_ratios.append(allowed_height / (probe_bbox[3] - probe_bbox[1]))
            ratio = min(fit_ratios)
            if ratio >= 1:
                break
            common_scale *= ratio
        else:
            raise ValueError("跳跃动作无法在保留帽子的前提下放入单格")
    for index, (crop, visible_bbox) in enumerate(prepared):
        local_visible_height = visible_bbox[3] - visible_bbox[1]
        scale = (target_height / local_visible_height) if normalize_pose_height else common_scale
        size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
        resized = crop.resize(size, Image.Resampling.LANCZOS)
        bbox = resized.getchannel("A").getbbox()
        if not bbox:
            raise ValueError(f"{name}[{index}] 缩放后为空")
        # Keep the generated torso at the screen center; arms and raised legs
        # no longer pull the whole sprite left or right between frames.
        x_offset = round(CELL_W / 2 - torso_anchor_x(resized))
        jump_offset = JUMP_BOTTOM_OFFSETS[index] if name == "jumping" else 0
        y_offset = GROUND_Y + jump_offset - bbox[3]
        cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
        cell.alpha_composite(resized, (x_offset, y_offset))
        rgb = cell.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.1, percent=135, threshold=2))
        sharpened = Image.merge("RGBA", (*rgb.split(), cell.getchannel("A")))
        final = clear_hidden_rgb(sharpened)
        final_bbox = final.getchannel("A").getbbox()
        records.append({
            "frame": index + 1,
            "body_anchor_x": round(torso_anchor_x(final), 2),
            "top": final_bbox[1],
            "bottom": final_bbox[3],
            "width": final_bbox[2] - final_bbox[0],
            "height": final_bbox[3] - final_bbox[1],
        })
        output.append(final)
    return output, {"reference_height": round(reference_height, 2), "frames": records}


def make_sheet(atlas: Image.Image, output: Path) -> None:
    scale = 2
    sheet = Image.new("RGB", (atlas.width * scale, atlas.height * scale), "#d6d6d6")
    checker = Image.new("RGBA", atlas.size, (232, 232, 232, 255))
    tile = 16
    draw = ImageDraw.Draw(checker)
    for y in range(0, atlas.height, tile):
        for x in range(0, atlas.width, tile):
            if (x // tile + y // tile) % 2:
                draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill=(246, 246, 246, 255))
    checker.alpha_composite(atlas)
    sheet.paste(checker.convert("RGB").resize(sheet.size, Image.Resampling.NEAREST))
    sheet.save(output)


def make_gifs(rows: list[tuple[str, list[Image.Image]]]) -> None:
    """Render preview GIFs against an opaque matte.

    GIF has only binary transparency. Directly encoding the atlas's soft alpha
    edges turns antialiased outline pixels into isolated palette speckles in
    many viewers. The installable WebP remains transparent; previews use a
    stable dark matte to keep every edge clean and legible.
    """
    duration = {"idle": 600, "running-right": 120, "running-left": 120, "waving": 150, "jumping": 140, "failed": 140, "waiting": 150, "running": 120, "review": 150}
    preview = QA / "previews"
    preview.mkdir(parents=True, exist_ok=True)
    def preview_frame(frame: Image.Image) -> Image.Image:
        scaled = frame.resize((384, 416), Image.Resampling.NEAREST)
        matte = Image.new("RGB", scaled.size, "#26313a")
        matte.paste(scaled, mask=scaled.getchannel("A"))
        return matte
    for name, frames in rows:
        scaled = [preview_frame(frame) for frame in frames]
        scaled[0].save(preview / f"{name}.gif", save_all=True, append_images=scaled[1:], loop=0, duration=duration[name], disposal=2)
    all_frames = [preview_frame(frame) for _, frames in rows for frame in frames]
    all_frames[0].save(RELEASE / "preview.gif", save_all=True, append_images=all_frames[1:], loop=0, duration=120, disposal=2)
    transitions = [preview_frame(frames[0]) for _, frames in rows]
    transitions[0].save(RELEASE / "transition-preview.gif", save_all=True, append_images=transitions[1:], loop=0, duration=280, disposal=2)


def main() -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    built: list[tuple[str, list[Image.Image]]] = []
    alignment: dict[str, dict] = {}
    for name, cols, rows, count in SPECS:
        if name == "running-left":
            frames = board_frames("running-right", cols, rows, count, mirror=True)
        else:
            frames = board_frames(name, cols, rows, count)
        fitted, alignment[name] = fit_action(name, frames)
        built.append((name, fitted))
    atlas = Image.new("RGBA", (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))
    for row, (_, frames) in enumerate(built):
        for col, frame in enumerate(frames):
            atlas.alpha_composite(frame, (col * CELL_W, row * CELL_H))
    atlas = clear_hidden_rgb(atlas)
    atlas.save(RELEASE / "spritesheet.webp", "WEBP", lossless=True, method=6)
    make_sheet(atlas, RELEASE / "preview-sheet.png")
    make_gifs(built)
    (QA / "build-manifest.json").write_text(json.dumps({"spriteVersionNumber": 1, "atlas": "spritesheet.webp", "size": [1536, 1872], "states": [{"name": name, "frames": len(frames)} for name, frames in built], "alignment": alignment}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[完成] 已生成 Codex Pet V1 图集与预览")


if __name__ == "__main__":
    main()
