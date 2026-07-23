"""
generate_image.py — Codex Pet 共享图片生成脚本
通过兼容 OpenAI Images API 的服务生成图片。

两种模式：
  1. 纯文生图:  python gen_image.py --prompt "描述" --output out.png
  2. 参考图编辑: python gen_image.py --prompt "描述" --ref ref1.png [--ref ref2.png] --output out.png

环境变量（自动从工作区根目录的 .env 读取）：
  IMAGE_API_KEY    API Key
  IMAGE_API_BASE   API Base URL
  IMAGE_MODEL      图片模型 ID

可选：设置 CODEX_PET_ENV_FILE 为其他共享 .env 的绝对路径。
"""

import argparse
import base64
import os
import sys
import time
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = WORKSPACE_ROOT / ".env"


def shared_env_file() -> Path:
    """Return the workspace credential file, allowing an explicit override."""
    configured = os.environ.get("CODEX_PET_ENV_FILE", "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_ENV_FILE


def load_local_env(path: Path) -> None:
    """Load simple KEY=VALUE entries without adding a dotenv dependency."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


ENV_FILE = shared_env_file()
load_local_env(ENV_FILE)
API_KEY = os.environ.get("IMAGE_API_KEY", "").strip()
API_BASE = os.environ.get("IMAGE_API_BASE", "").strip().rstrip("/")
MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-2-0421-global").strip()
DEFAULT_SIZE = "1024x1536"  # 竖版全身图尺寸（宽x高）
DEFAULT_QUALITY = "high"  # high / medium / low
TIMEOUT_SECONDS = 300  # 高质量参考图编辑有时超过 2 分钟


def image_api_client():
    """Load the optional network dependency only when an image is requested."""
    try:
        import httpx
    except ModuleNotFoundError as exc:
        raise SystemExit("缺少 httpx；请先安装角色生产流水线的 requirements.txt。") from exc
    return httpx


def encode_image_to_base64(image_path: str) -> str:
    """将本地图片编码为 base64 字符串。"""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def get_image_mime(image_path: str) -> str:
    """根据扩展名判断 MIME 类型。"""
    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    return mime_map.get(ext, "image/png")


def generate_image_text_only(prompt: str, size: str, quality: str, output_path: str):
    """模式1：纯文生图。"""
    httpx = image_api_client()
    print(f"[模式] 纯文生图")
    print(f"[Prompt] {prompt}")
    print(f"[尺寸] {size}  [质量] {quality}")
    print(f"[输出] {output_path}")
    print("─" * 50)

    url = f"{API_BASE}/images/generations"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality,
    }

    t0 = time.time()
    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        resp = client.post(url, json=payload, headers=headers)

    elapsed = time.time() - t0
    print(f"[耗时] {elapsed:.1f}s  [状态码] {resp.status_code}")

    if resp.status_code != 200:
        print(f"[错误] {resp.text}")
        sys.exit(1)

    data = resp.json()
    # 响应可能包含 url 或 b64_json
    image_data = data["data"][0]
    if "b64_json" in image_data:
        img_bytes = base64.standard_b64decode(image_data["b64_json"])
        Path(output_path).write_bytes(img_bytes)
    elif "url" in image_data:
        # 下载 URL
        img_resp = httpx.get(image_data["url"], timeout=60)
        Path(output_path).write_bytes(img_resp.content)
    else:
        print(f"[错误] 未知响应格式: {list(image_data.keys())}")
        sys.exit(1)

    file_size = Path(output_path).stat().st_size / 1024
    print(f"[完成] 已保存 {output_path} ({file_size:.0f} KB)")


def generate_image_with_reference(prompt: str, ref_paths: list, size: str, quality: str, output_path: str):
    """模式2：上传参考图 + prompt 生成新图（使用 images/edits 接口）。"""
    httpx = image_api_client()
    print(f"[模式] 参考图编辑")
    print(f"[Prompt] {prompt}")
    print(f"[参考图] {ref_paths}")
    print(f"[尺寸] {size}  [质量] {quality}")
    print(f"[输出] {output_path}")
    print("─" * 50)

    url = f"{API_BASE}/images/edits"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    # 构建 multipart/form-data
    # gpt-image-2 的 edits 接口支持上传多张 image 文件
    files = []
    for ref_path in ref_paths:
        mime = get_image_mime(ref_path)
        filename = Path(ref_path).name
        files.append(("image", (filename, open(ref_path, "rb"), mime)))

    form_data = {
        "model": MODEL,
        "prompt": prompt,
        "n": "1",
        "size": size,
        "quality": quality,
    }

    t0 = time.time()
    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        resp = client.post(url, data=form_data, files=files, headers=headers)

    # 关闭文件句柄
    for _, (_, fh, _) in files:
        fh.close()

    elapsed = time.time() - t0
    print(f"[耗时] {elapsed:.1f}s  [状态码] {resp.status_code}")

    if resp.status_code != 200:
        print(f"[错误] {resp.text}")
        sys.exit(1)

    data = resp.json()
    image_data = data["data"][0]
    if "b64_json" in image_data:
        img_bytes = base64.standard_b64decode(image_data["b64_json"])
        Path(output_path).write_bytes(img_bytes)
    elif "url" in image_data:
        img_resp = httpx.get(image_data["url"], timeout=60)
        Path(output_path).write_bytes(img_resp.content)
    else:
        print(f"[错误] 未知响应格式: {list(image_data.keys())}")
        sys.exit(1)

    file_size = Path(output_path).stat().st_size / 1024
    print(f"[完成] 已保存 {output_path} ({file_size:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(
        description="Codex Pet 共享图片生成工具 (gpt-image-2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 纯文生图
  python gen_image.py --prompt "水彩风格动漫女孩挥手" --output wave.png

  # 带参考图生成（推荐用法）
  python gen_image.py \\
    --ref ran-fullbody-reference.png \\
    --prompt "保持完全相同的角色、画风和服装。改为挥手姿态：右手举起挥手，面带微笑。纯白背景。" \\
    --output wave.png

  # 多张参考图
  python gen_image.py \\
    --ref ran-fullbody-reference.png \\
    --ref ran-face-reference.jpg \\
    --prompt "同角色，跑步姿态" \\
    --output running.png
""",
    )
    parser.add_argument("--prompt", "-p", required=True, help="图片描述 prompt")
    parser.add_argument("--ref", "-r", action="append", default=[], help="参考图路径（可多次指定）")
    parser.add_argument("--output", "-o", required=True, help="输出图片路径")
    parser.add_argument("--size", "-s", default=DEFAULT_SIZE, help=f"图片尺寸 (默认 {DEFAULT_SIZE})")
    parser.add_argument("--quality", "-q", default=DEFAULT_QUALITY, choices=["high", "medium", "low"], help="质量等级")

    args = parser.parse_args()

    missing = [
        name
        for name, value in (("IMAGE_API_KEY", API_KEY), ("IMAGE_API_BASE", API_BASE))
        if not value
    ]
    if missing:
        print(
            f"[错误] 缺少配置：{', '.join(missing)}。请在工作区根目录的 .env 中填写，"
            "或通过 CODEX_PET_ENV_FILE 指定共享配置文件。",
            file=sys.stderr,
        )
        sys.exit(2)

    # 确保输出目录存在
    output_dir = Path(args.output).parent
    if output_dir != Path("."):
        output_dir.mkdir(parents=True, exist_ok=True)

    if args.ref:
        # 校验参考图文件存在
        for ref_path in args.ref:
            if not Path(ref_path).exists():
                print(f"[错误] 参考图不存在: {ref_path}")
                sys.exit(1)
        generate_image_with_reference(args.prompt, args.ref, args.size, args.quality, args.output)
    else:
        generate_image_text_only(args.prompt, args.size, args.quality, args.output)


if __name__ == "__main__":
    main()
