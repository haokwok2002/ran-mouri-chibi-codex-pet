#!/usr/bin/env python3
"""Build clean public previews directly from a validated Codex pet atlas."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CELL_WIDTH = 192
CELL_HEIGHT = 208
LABEL_HEIGHT = 24
BACKGROUND = (246, 246, 243, 255)
CELL_BACKGROUND = (252, 252, 250, 255)
TEXT = (47, 48, 44, 255)
SEPARATOR = (220, 220, 214, 255)

STATES = (
    ("idle", "Idle", 0, 6),
    ("running-right", "Run right", 1, 8),
    ("running-left", "Run left", 2, 8),
    ("waving", "Wave", 3, 4),
    ("jumping", "Jump", 4, 5),
    ("failed", "Failed", 5, 8),
    ("waiting", "Waiting", 6, 6),
    ("running", "Working", 7, 6),
    ("review", "Review", 8, 6),
)


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def atlas_cell(atlas: Image.Image, row: int, column: int) -> Image.Image:
    left = column * CELL_WIDTH
    top = row * CELL_HEIGHT
    return atlas.crop((left, top, left + CELL_WIDTH, top + CELL_HEIGHT))


def stabilize_cell(cell: Image.Image, preserve_vertical_motion: bool = False) -> Image.Image:
    alpha = cell.getchannel("A").point(lambda value: 255 if value > 16 else 0)
    box = alpha.getbbox()
    if box is None:
        return cell

    center_x = (box[0] + box[2]) / 2
    # Integer pixels cannot place every odd/even-width silhouette on the same
    # half-pixel center. Keep all frames in the narrow 95.5-96.0 anchor band.
    shift_x = math.floor(CELL_WIDTH / 2 - center_x)
    shift_y = 0 if preserve_vertical_motion else 202 - box[3]
    stabilized = Image.new("RGBA", cell.size, (0, 0, 0, 0))
    stabilized.alpha_composite(cell, (shift_x, shift_y))
    return stabilized


def composite_cell(cell: Image.Image, preserve_vertical_motion: bool = False) -> Image.Image:
    canvas = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), CELL_BACKGROUND)
    canvas.alpha_composite(stabilize_cell(cell, preserve_vertical_motion))
    return canvas


def centered_label(draw: ImageDraw.ImageDraw, label: str, y: int, font: ImageFont.ImageFont) -> None:
    box = draw.textbbox((0, 0), label, font=font)
    width = box[2] - box[0]
    draw.text(((CELL_WIDTH - width) // 2, y), label, fill=TEXT, font=font)


def build_gif(atlas: Image.Image, output: Path) -> None:
    font = load_font(13)
    frames: list[Image.Image] = []
    durations: list[int] = []

    for _, label, row, frame_count in STATES:
        for column in range(frame_count):
            frame = Image.new("RGB", (CELL_WIDTH, CELL_HEIGHT + LABEL_HEIGHT), BACKGROUND[:3])
            cell = composite_cell(
                atlas_cell(atlas, row, column), preserve_vertical_motion=(row == 4)
            ).convert("RGB")
            frame.paste(cell, (0, 0))
            draw = ImageDraw.Draw(frame)
            centered_label(draw, label, CELL_HEIGHT + 4, font)
            frames.append(frame)
            durations.append(420 if column == 0 else 130)

    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=False,
    )


def build_action_gifs(atlas: Image.Image, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for slug, _, row, frame_count in STATES:
        frames = [
            composite_cell(
                atlas_cell(atlas, row, column), preserve_vertical_motion=(row == 4)
            ).convert("RGB")
            for column in range(frame_count)
        ]
        frames[0].save(
            output_dir / f"{slug}.gif",
            save_all=True,
            append_images=frames[1:],
            duration=150,
            loop=0,
            disposal=2,
            optimize=False,
        )


def build_sheet(atlas: Image.Image, output: Path) -> None:
    font = load_font(13)
    row_height = CELL_HEIGHT + LABEL_HEIGHT
    sheet = Image.new("RGB", (CELL_WIDTH * 8, row_height * len(STATES)), BACKGROUND[:3])
    draw = ImageDraw.Draw(sheet)

    for state_index, (_, label, row, frame_count) in enumerate(STATES):
        y = state_index * row_height
        draw.rectangle((0, y, sheet.width, y + LABEL_HEIGHT - 1), fill=BACKGROUND[:3])
        draw.text((8, y + 4), f"{label} · {frame_count} frames", fill=TEXT[:3], font=font)
        for column in range(8):
            x = column * CELL_WIDTH
            draw.rectangle(
                (x, y + LABEL_HEIGHT, x + CELL_WIDTH - 1, y + row_height - 1),
                fill=CELL_BACKGROUND[:3],
                outline=SEPARATOR[:3],
            )
            if column < frame_count:
                cell = composite_cell(
                    atlas_cell(atlas, row, column), preserve_vertical_motion=(row == 4)
                ).convert("RGB")
                sheet.paste(cell, (x, y + LABEL_HEIGHT))

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("atlas", type=Path)
    parser.add_argument("--gif", required=True, type=Path)
    parser.add_argument("--sheet", required=True, type=Path)
    parser.add_argument("--actions-dir", type=Path)
    args = parser.parse_args()

    atlas = Image.open(args.atlas).convert("RGBA")
    if atlas.size != (1536, 2288):
        raise SystemExit(f"expected a 1536x2288 v2 atlas, got {atlas.size[0]}x{atlas.size[1]}")
    build_gif(atlas, args.gif)
    build_sheet(atlas, args.sheet)
    if args.actions_dir:
        build_action_gifs(atlas, args.actions_dir)


if __name__ == "__main__":
    main()
