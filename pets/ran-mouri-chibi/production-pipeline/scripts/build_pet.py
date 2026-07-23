#!/usr/bin/env python3
"""Build the 8×11 Codex Pet V2 atlas from curated Xiaolan key poses."""

from __future__ import annotations

import json
from statistics import median
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PIPELINE_ROOT.parent
RELEASE_DIR = REPO_ROOT / "ready-to-use"
QA_DIR = PIPELINE_ROOT / "qa"
SEQUENCES = PIPELINE_ROOT / "source" / "sequences" / "matted"
ATLAS_PATH = RELEASE_DIR / "spritesheet.webp"
CELL_W, CELL_H = 192, 208
COLS, ROWS = 8, 11
ATLAS_W, ATLAS_H = CELL_W * COLS, CELL_H * ROWS
PET_MAX_WIDTH, PET_MAX_HEIGHT = 168, 178
RUNTIME_BODY_CENTER_X = 96
RUNTIME_GROUND_Y = 193

ROW_SPECS = (
    ("idle", 7),
    ("running-right", 8),
    ("running-left", 8),
    ("waving", 4),
    ("jumping", 5),
    ("failed", 8),
    ("waiting", 6),
    ("running", 6),
    ("review", 6),
    ("look-000-to-157.5", 8),
    ("look-180-to-337.5", 8),
)

# These timings are defined by the Codex desktop client for sprite V2. They
# cannot be overridden by pet.json. Keeping the generated previews on the same
# clock prevents a preview-only speed from being mistaken for runtime behavior.
STATE_RUNTIME_TIMING_MS = {
    # The current client reads the first six idle cells; the seventh atlas cell
    # remains populated for V2 atlas compatibility but is not played. Codex
    # applies a 6x idle multiplier to these source timings.
    "idle": [1680, 660, 660, 840, 840, 1920],
    "running-right": [120, 120, 120, 120, 120, 120, 120, 220],
    "running-left": [120, 120, 120, 120, 120, 120, 120, 220],
    "waving": [140, 140, 140, 280],
    "jumping": [140, 140, 140, 140, 280],
    "failed": [140, 140, 140, 140, 140, 140, 140, 240],
    "waiting": [150, 150, 150, 150, 150, 260],
    "running": [120, 120, 120, 120, 120, 220],
    "review": [150, 150, 150, 150, 150, 280],
}
LOOK_PREVIEW_CADENCE_MS = 130


def require(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"缺少素材：{path}")
    return path


def open_rgba(path: Path) -> Image.Image:
    return Image.open(require(path)).convert("RGBA")


def clear_transparent_rgb(image: Image.Image) -> Image.Image:
    """Guarantee transparent pixels are (0, 0, 0, 0), as Codex expects."""
    pixels = np.array(image.convert("RGBA"), dtype=np.uint8, copy=True)
    pixels[pixels[:, :, 3] == 0, :3] = 0
    return Image.fromarray(pixels)


def keep_character_components(frame: Image.Image) -> Image.Image:
    """Remove tiny cross-panel fragments while preserving the drawn character."""
    pixels = np.array(frame.convert("RGBA"), dtype=np.uint8, copy=True)
    alpha_mask = (pixels[:, :, 3] > 8).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(alpha_mask, 8)
    if count <= 1:
        return frame
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest = int(areas.max())
    minimum = max(500, round(largest * 0.025))
    keep = np.zeros_like(alpha_mask, dtype=bool)
    for label in range(1, count):
        if int(stats[label, cv2.CC_STAT_AREA]) >= minimum:
            keep |= labels == label
    pixels[~keep] = 0
    return Image.fromarray(pixels)


def union_bbox(frames: list[Image.Image], padding: int = 10) -> tuple[int, int, int, int]:
    """One shared crop for a whole action; never recenter individual frames."""
    boxes = [frame.getchannel("A").getbbox() for frame in frames]
    boxes = [box for box in boxes if box]
    if not boxes:
        raise ValueError("分镜板没有可见角色像素")
    left = max(0, min(box[0] for box in boxes) - padding)
    top = max(0, min(box[1] for box in boxes) - padding)
    right = min(frames[0].width, max(box[2] for box in boxes) + padding)
    bottom = min(frames[0].height, max(box[3] for box in boxes) + padding)
    return left, top, right, bottom


def face_anchor_x(frame: Image.Image) -> float:
    """Locate the warm skin-colored face component for horizontal registration."""
    pixels = np.asarray(frame.convert("RGBA"))
    red, green, blue, alpha = [pixels[:, :, index] for index in range(4)]
    yy, _ = np.indices(alpha.shape)
    mask = (
        (alpha > 180)
        & (red > 205)
        & (green > 175)
        & (blue > 150)
        & (red >= green)
        & (green >= blue * 0.92)
        & (yy < 300)
    ).astype(np.uint8)
    count, _, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
    candidates: list[tuple[int, float]] = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        width = int(stats[label, cv2.CC_STAT_WIDTH])
        height = int(stats[label, cv2.CC_STAT_HEIGHT])
        center_x, center_y = centroids[label]
        if area > 200 and width > 20 and height > 20 and center_y < 220:
            candidates.append((area, float(center_x)))
    if not candidates:
        bbox = frame.getchannel("A").getbbox()
        if not bbox:
            raise ValueError("无法定位角色面部")
        return (bbox[0] + bbox[2]) / 2
    return max(candidates)[1]


def skirt_anchor_x(frame: Image.Image) -> float:
    """Locate the lower navy garment, used when the face turns through profiles."""
    pixels = np.asarray(frame.convert("RGBA"))
    red, green, blue, alpha = [pixels[:, :, index] for index in range(4)]
    yy, xx = np.indices(alpha.shape)
    mask = (
        (alpha > 180)
        & (red < 175)
        & (green < 185)
        & (blue < 220)
        & (blue > red * 0.92)
        & (yy > 210)
        & (xx > 70)
        & (xx < 442)
    ).astype(np.uint8)
    count, _, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
    candidates = [
        (int(stats[label, cv2.CC_STAT_AREA]), float(centroids[label][0]))
        for label in range(1, count)
        if int(stats[label, cv2.CC_STAT_AREA]) > 100
    ]
    if not candidates:
        return face_anchor_x(frame)
    return max(candidates)[1]


def stabilize_horizontal(frames: list[Image.Image], *, use_skirt: bool) -> list[Image.Image]:
    """Register independently drawn frames to one body anchor; no motion is invented."""
    anchor = skirt_anchor_x if use_skirt else face_anchor_x
    centers = [anchor(frame) for frame in frames]
    target = median(centers)
    stabilized: list[Image.Image] = []
    for frame, center in zip(frames, centers):
        correction = round(target - center)
        canvas = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        canvas.alpha_composite(frame, (correction, 0))
        stabilized.append(clear_transparent_rgb(canvas))
    return stabilized


def stabilize_grounded_vertical(frames: list[Image.Image]) -> list[Image.Image]:
    """Remove board-placement drift from poses that are meant to stay grounded."""
    bottoms = []
    for frame in frames:
        bbox = frame.getchannel("A").getbbox()
        if not bbox:
            raise ValueError("无法定位角色脚底")
        bottoms.append(bbox[3])
    target = median(bottoms)
    stabilized: list[Image.Image] = []
    for frame, bottom in zip(frames, bottoms):
        correction = round(target - bottom)
        canvas = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        canvas.alpha_composite(frame, (0, correction))
        stabilized.append(clear_transparent_rgb(canvas))
    return stabilized


def output_skirt_anchor_x(frame: Image.Image) -> float:
    """Find the navy skirt in a finished 192x208 cell as a pelvis anchor."""
    pixels = np.asarray(frame.convert("RGBA"))
    red, green, blue, alpha = [pixels[:, :, index] for index in range(4)]
    yy, _ = np.indices(alpha.shape)
    mask = (
        (alpha > 180)
        & (red < 175)
        & (green < 185)
        & (blue < 220)
        & (blue > red * 0.92)
        & (yy > round(frame.height * 0.36))
        & (yy < round(frame.height * 0.84))
    ).astype(np.uint8)
    count, _, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
    candidates = [
        (int(stats[label, cv2.CC_STAT_AREA]), float(centroids[label][0]))
        for label in range(1, count)
        if int(stats[label, cv2.CC_STAT_AREA]) > 80
    ]
    if not candidates:
        bbox = frame.getchannel("A").getbbox()
        if not bbox:
            raise ValueError("无法定位成品角色中心")
        return (bbox[0] + bbox[2]) / 2
    return max(candidates)[1]


def register_sequence_to_runtime_anchor(frames: list[Image.Image]) -> list[Image.Image]:
    """Apply one shared correction so every state's first frame switches in place."""
    first_bbox = frames[0].getchannel("A").getbbox()
    if not first_bbox:
        raise ValueError("动作首帧为空")
    correction_x = round(RUNTIME_BODY_CENTER_X - output_skirt_anchor_x(frames[0]))
    correction_y = RUNTIME_GROUND_Y - first_bbox[3]
    registered: list[Image.Image] = []
    for frame in frames:
        canvas = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        canvas.alpha_composite(frame, (correction_x, correction_y))
        registered.append(clear_transparent_rgb(canvas))
    return registered


def snap_landing_to_ground(frame: Image.Image) -> Image.Image:
    """Correct the generated landing panel so its long hold ends on the floor."""
    bbox = frame.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("跳跃落地帧为空")
    canvas = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    canvas.alpha_composite(frame, (0, RUNTIME_GROUND_Y - bbox[3]))
    return clear_transparent_rgb(canvas)


def restore_open_eyes(frame: Image.Image, open_reference: Image.Image) -> Image.Image:
    """Restore only the two eye apertures from an approved open-eye drawing."""
    mask = Image.new("L", frame.size, 0)
    draw = ImageDraw.Draw(mask)
    # Separate small masks avoid replacing the nose, mouth, face contour, or
    # hairstyle. A one-pixel feather hides antialiasing boundaries.
    draw.rounded_rectangle((76, 65, 94, 91), radius=4, fill=255)
    draw.rounded_rectangle((98, 65, 117, 91), radius=4, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=1.0))
    return clear_transparent_rgb(Image.composite(open_reference, frame, mask))


def retime_idle_blink(frames: list[Image.Image]) -> list[Image.Image]:
    """Compress the visible blink into Codex's shortest 660 ms idle slot."""
    if len(frames) != 7:
        raise ValueError(f"idle 需要 7 个图集帧，实际为 {len(frames)}")
    # Original frame 3 is the cleanest fully closed drawing. Move it into
    # runtime slot 1, whose fixed duration is 660 ms. Runtime slots 2-4 keep
    # their independently drawn hair/clothing micro-motion but use the approved
    # open eyes, so no second slow eyelid sweep follows the blink.
    retimed = [frames[0], frames[3], frames[2], frames[1], frames[4], frames[5], frames[6]]
    open_reference = retimed[0]
    for index in (2, 3, 4):
        retimed[index] = restore_open_eyes(retimed[index], open_reference)
    return retimed


def load_sequence(
    name: str,
    columns: int,
    rows: int,
    count: int,
    *,
    mirror: bool = False,
    grounded: bool = True,
) -> list[Image.Image]:
    """Split a hand-drawn board and apply one identical transform to all frames."""
    board = open_rgba(SEQUENCES / f"{name}.png")
    expected = (columns * 512, rows * 512)
    if board.size != expected:
        raise ValueError(f"{name} 分镜板应为 {expected}，实际为 {board.size}")

    raw: list[Image.Image] = []
    for index in range(count):
        column = index % columns
        row = index // columns
        raw.append(
            keep_character_components(board.crop(
                (column * 512, row * 512, (column + 1) * 512, (row + 1) * 512)
            ))
        )

    # The image model may place panels a few pixels apart even when instructed
    # to lock the canvas. Correct that placement once using a stable anatomical
    # anchor. The drawings themselves are never rotated, scaled independently,
    # or reused to synthesize motion.
    # The pelvis/skirt is a more reliable body anchor than exposed skin: raised
    # hands in the jumping board can otherwise be mistaken for the face.
    raw = stabilize_horizontal(raw, use_skirt=True)
    if grounded:
        raw = stabilize_grounded_vertical(raw)

    shared_crop = union_bbox(raw)
    crop_width = shared_crop[2] - shared_crop[0]
    crop_height = shared_crop[3] - shared_crop[1]
    fit = min(PET_MAX_WIDTH / crop_width, PET_MAX_HEIGHT / crop_height)
    output_width = max(1, round(crop_width * fit))
    output_height = max(1, round(crop_height * fit))
    x = round((CELL_W - output_width) / 2)
    y = round((CELL_H - output_height) / 2)

    result: list[Image.Image] = []
    for frame in raw:
        frame = frame.crop(shared_crop).resize(
            (output_width, output_height), Image.Resampling.LANCZOS
        )
        # The source artwork is intentionally clean and high-contrast. Restore
        # a small amount of edge acuity after 512px-to-pet-size reduction so
        # eyes, the lifted forelock, and jacket silhouette stay legible.
        red, green, blue, alpha = frame.split()
        rgb = Image.merge("RGB", (red, green, blue)).filter(
            ImageFilter.UnsharpMask(radius=0.65, percent=95, threshold=2)
        )
        red, green, blue = rgb.split()
        frame = Image.merge("RGBA", (red, green, blue, alpha))
        cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
        cell.alpha_composite(frame, (x, y))
        if mirror:
            cell = cell.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        result.append(clear_transparent_rgb(cell))
    result = register_sequence_to_runtime_anchor(result)
    if name == "jumping":
        # Codex holds frame 5 for 280 ms. It must visibly finish on the shared
        # baseline instead of hovering before the next crouch begins.
        result[-1] = snap_landing_to_ground(result[-1])
    return result


def frame_sequence() -> list[list[Image.Image]]:
    idle = retime_idle_blink(load_sequence("idle", 4, 2, 7))
    running_right = load_sequence("run-right", 4, 2, 8, grounded=False)
    running_left = load_sequence("run-right", 4, 2, 8, mirror=True, grounded=False)
    waving = load_sequence("waving", 2, 2, 4)
    jumping = load_sequence("jumping", 3, 2, 5, grounded=False)
    failed_frames = load_sequence("failed", 4, 2, 8)
    waiting = load_sequence("waiting", 3, 2, 6)
    working_frames = load_sequence("working", 3, 2, 6)
    review_frames = load_sequence("review", 3, 2, 6)
    look_frames = load_sequence("look", 4, 4, 16)

    return [
        idle,
        running_right,
        running_left,
        waving,
        jumping,
        failed_frames,
        waiting,
        working_frames,
        review_frames,
        look_frames[:8],
        look_frames[8:],
    ]


def build_atlas(rows: list[list[Image.Image]]) -> Image.Image:
    if len(rows) != ROWS:
        raise ValueError(f"需要 {ROWS} 行，实际为 {len(rows)}")
    atlas = Image.new("RGBA", (ATLAS_W, ATLAS_H), (0, 0, 0, 0))
    for row_index, ((state, used), frames) in enumerate(zip(ROW_SPECS, rows)):
        if len(frames) != used:
            raise ValueError(f"{state} 需要 {used} 帧，实际为 {len(frames)}")
        for column, frame in enumerate(frames):
            atlas.alpha_composite(frame, (column * CELL_W, row_index * CELL_H))
    return clear_transparent_rgb(atlas)


def checker_cell() -> Image.Image:
    tile = 16
    image = Image.new("RGBA", (CELL_W, CELL_H), (239, 241, 245, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, CELL_H, tile):
        for x in range(0, CELL_W, tile):
            if (x // tile + y // tile) % 2:
                draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill=(225, 228, 234, 255))
    return image


def build_contact_sheet(atlas: Image.Image) -> None:
    label_width = 170
    preview = Image.new("RGBA", (label_width + ATLAS_W, ATLAS_H), (247, 248, 250, 255))
    draw = ImageDraw.Draw(preview)
    font = ImageFont.load_default()
    checker = checker_cell()
    for row, (state, used) in enumerate(ROW_SPECS):
        y = row * CELL_H
        draw.text((12, y + 94), f"{row:02d}  {state}  ({used})", fill=(35, 42, 55, 255), font=font)
        for column in range(COLS):
            preview.alpha_composite(checker, (label_width + column * CELL_W, y))
        strip = atlas.crop((0, y, ATLAS_W, y + CELL_H))
        preview.alpha_composite(strip, (label_width, y))
    preview.convert("RGB").save(RELEASE_DIR / "preview-sheet.png", optimize=True)


def build_animation_preview(rows: list[list[Image.Image]]) -> None:
    background = checker_cell().convert("RGBA")
    preview_dir = QA_DIR / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    combined: list[Image.Image] = []
    combined_durations: list[int] = []
    for (state, _), row_frames in zip(ROW_SPECS, rows):
        frames: list[Image.Image] = []
        for cell in row_frames:
            frame = Image.new("RGBA", (CELL_W, CELL_H + 24), (247, 248, 250, 255))
            frame.alpha_composite(background, (0, 24))
            frame.alpha_composite(cell, (0, 24))
            draw = ImageDraw.Draw(frame)
            draw.text((7, 7), state, fill=(28, 34, 45, 255), font=ImageFont.load_default())
            frames.append(frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=255))
        durations = STATE_RUNTIME_TIMING_MS.get(
            state, [LOOK_PREVIEW_CADENCE_MS] * len(frames)
        )
        # Directional look rows are QA sweeps, not autonomous runtime states.
        # Idle likewise previews only the six cells read by the current client.
        frames = frames[:len(durations)]
        frames[0].save(
            preview_dir / f"{state}.gif",
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            disposal=2,
            optimize=False,
        )
        combined.extend(frames)
        combined_durations.extend(durations[:-1] + [700])
    combined[0].save(
        RELEASE_DIR / "preview.gif",
        save_all=True,
        append_images=combined[1:],
        duration=combined_durations,
        loop=0,
        disposal=2,
        optimize=False,
    )


def build_transition_preview(rows: list[list[Image.Image]]) -> None:
    """Cycle through every state start frame to make switch alignment obvious."""
    background = checker_cell().convert("RGBA")
    frames: list[Image.Image] = []
    for (state, _), row_frames in zip(ROW_SPECS, rows):
        frame = Image.new("RGBA", (CELL_W, CELL_H + 24), (247, 248, 250, 255))
        frame.alpha_composite(background, (0, 24))
        frame.alpha_composite(row_frames[0], (0, 24))
        draw = ImageDraw.Draw(frame)
        draw.text((7, 7), f"switch -> {state}", fill=(28, 34, 45, 255), font=ImageFont.load_default())
        frames.append(frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=255))
    frames[0].save(
        RELEASE_DIR / "transition-preview.gif",
        save_all=True,
        append_images=frames[1:],
        duration=700,
        loop=0,
        disposal=2,
        optimize=False,
    )


def write_build_manifest(rows: list[list[Image.Image]]) -> None:
    data = {
        "format": "Codex Pet V2",
        "cell": [CELL_W, CELL_H],
        "columns": COLS,
        "rows": ROWS,
        "atlas": [ATLAS_W, ATLAS_H],
        "states": [
            {"row": index, "state": state, "frames": used}
            for index, (state, used) in enumerate(ROW_SPECS)
        ],
        "animation_policy": "Every used cell comes from a separately drawn chibi frame. One shared crop and scale is applied per action. A small horizontal anatomical-anchor registration corrects model placement drift; no rotation, zoom, vertical bob, or transform-generated animation is used.",
        "render_policy": "Compact 3.5-head-tall chibi, maximum 168x178 pixels inside each 192x208 cell, with subtle post-downscale edge sharpening for small-size clarity.",
        "runtime_anchor": {
            "body_center_x": RUNTIME_BODY_CENTER_X,
            "ground_y": RUNTIME_GROUND_Y,
            "policy": "Every state start frame shares one pelvis center and shoe baseline. Grounded loops also remove source-board vertical placement drift with one registration pass.",
        },
        "runtime_timing_ms": STATE_RUNTIME_TIMING_MS,
        "look_preview_cadence_ms": LOOK_PREVIEW_CADENCE_MS,
        "runtime_timing_policy": "State timings and frame counts are fixed by Codex desktop for sprite V2 and cannot be overridden by pet.json. State preview GIFs reproduce those fixed timings; look rows use a QA-only sweep cadence because runtime selects them directionally rather than animating them as a state.",
        "idle_blink_policy": {
            "runtime_closed_eye_slots": [1],
            "closed_eye_duration_ms": 660,
            "previous_visible_blink_envelope_ms": 3000,
            "speedup": 4.55,
            "policy": "The fully closed drawing occupies only Codex's shortest idle slot. Every following runtime frame restores approved open eyes while retaining independently drawn hair and clothing micro-motion.",
        },
    }
    (QA_DIR / "build-manifest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    rows = frame_sequence()
    atlas = build_atlas(rows)
    atlas.save(ATLAS_PATH, "WEBP", lossless=True, quality=100, method=6, exact=True)
    build_contact_sheet(atlas)
    build_animation_preview(rows)
    build_transition_preview(rows)
    write_build_manifest(rows)
    print(f"已生成：{ATLAS_PATH} ({ATLAS_W}×{ATLAS_H}, RGBA WebP)")


if __name__ == "__main__":
    main()
