# 生产流水线

此目录包含重新生成动作分镜、构建最终图集和执行质量验证所需的全部代码与素材。最终可安装输出会写入当前角色目录的 `ready-to-use/`。

## 环境准备

从当前角色目录（例如 `ran-mouri-chibi/`）运行：

```bash
python3 -m venv production-pipeline/.venv
source production-pipeline/.venv/bin/activate
pip install -r production-pipeline/requirements.txt
```

图片服务配置由工作区根目录的共享 `.env` 提供。首次创建工作区时，在 `codex-pet/` 根目录运行：

```bash
cp .env.example .env
```

然后编辑根目录的 `.env`。该文件只保留在本机，不会被 Git 跟踪；所有直接位于 `codex-pet/` 下的角色流水线都会自动读取它。若角色项目不位于此工作区，可设置 `CODEX_PET_ENV_FILE` 为共享 `.env` 的绝对路径。

## 从现有分镜重新构建

```bash
source production-pipeline/.venv/bin/activate
bash production-pipeline/scripts/build.sh
```

构建会更新：

- `ready-to-use/spritesheet.webp`
- `ready-to-use/preview.gif`
- `ready-to-use/preview-sheet.png`
- `ready-to-use/transition-preview.gif`
- `production-pipeline/qa/` 下的验证报告和逐状态预览

## 重新生成动作分镜

```bash
source production-pipeline/.venv/bin/activate
bash production-pipeline/scripts/generate_sequences.sh
bash production-pipeline/scripts/build.sh
```

生成脚本使用 `references/xiaolan-reference.png` 与 `source/anchor-green.png` 锁定角色身份，调用工作区根目录的 `tools/image-api/generate_image.py`，并将绿幕分镜输出到 `source/sequences/source/`。

## 目录结构

```text
production-pipeline/
├── requirements.txt
├── DESIGN.md
├── prompts/              # 动作提示词
├── references/           # 身份参考图
├── source/               # 绿幕锚点与原始分镜（已提交）
│   └── sequences/
│       ├── source/       # 生成的绿幕状态分镜（已提交）
│       └── matted/       # 构建时生成的透明中间图（本地忽略）
├── scripts/              # 生成、构建与验证脚本
└── qa/                   # 构建清单、验证报告和逐状态预览
```

共享配置位于仓库根目录：`../../../.env.example`（模板）和 `../../../.env`（仅本机）；通用图片生成器位于 `../../../tools/image-api/generate_image.py`。

更详细的构图、动作和锚点规范见 [`DESIGN.md`](DESIGN.md)。
