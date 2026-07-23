# 红猪 V1 制作流水线

此目录保存红猪 V1 的完整制作档案。普通安装只需要同级的 `../ready-to-use/`；只有重新生成、修复或审计时才进入这里。

```text
production-pipeline/
├── DESIGN.md                  # V1 兼容性、角色和动作设计
├── prompts/                   # 参考图与 8 组标准动作提示词
├── references/                # 已批准的公开生产身份锚点
├── source/
│   └── sequences/
│       ├── source/            # 已批准的绿幕分镜，提交到 Git
│       └── matted/            # 可再生透明中间图，Git 忽略
├── scripts/                   # 生成、抠像、构建、验证和质检
└── qa/                        # 构建清单、验证报告和动作预览
```

## 仅重建图集

在角色目录 `pets/porco-rosso-chibi/` 中执行：

```bash
PYTHON=/usr/bin/python3 bash production-pipeline/scripts/build.sh
```

构建会更新 `../ready-to-use/` 的精灵图、预览和安装包，同时更新本目录下的 QA 报告。构建脚本会检查 V1 的图集尺寸、空格、躯干锚点、跳跃轨迹和帽顶安全边距。

## 重新生成动作分镜

首次需要在仓库根目录创建 `.env`（绝不提交），然后在角色目录执行：

```bash
PYTHON=/usr/bin/python3 bash production-pipeline/scripts/generate_sequences.sh
PYTHON=/usr/bin/python3 bash production-pipeline/scripts/build.sh
```

共享生成器为 `../../../tools/image-api/generate_image.py`；默认读取仓库根目录 `.env`，也支持 `CODEX_PET_ENV_FILE` 覆盖。不要把任何私密或带水印的初始图放进 `references/` 或 `ready-to-use/`。
