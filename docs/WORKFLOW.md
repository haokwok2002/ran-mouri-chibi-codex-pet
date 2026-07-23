# Codex Pet 制作与归档工作流

本仓库把“给用户安装的发布物”和“可复现的制作档案”分开存放，但两者都保留在版本控制中。

## 角色目录约定

每个角色都位于 `pets/<pet-slug>/`：

```text
pets/<pet-slug>/
├── README.md                         # 角色说明、展示与安装方法
├── ready-to-use/                     # 对外发布层：唯一需要给普通用户看的目录
│   ├── pet.json
│   ├── spritesheet.webp
│   ├── install.sh
│   ├── install.ps1
│   ├── preview.gif
│   ├── preview-sheet.png
│   └── transition-preview.gif
└── production-pipeline/              # 制作档案层：仅重新制作或审计时进入
    ├── DESIGN.md                      # 角色、动作、版本与兼容性决策
    ├── prompts/                       # 可复现的图片提示词
    ├── references/                    # 可公开的身份锚点和来源说明
    ├── source/                        # 已批准的绿幕锚点和原始分镜
    ├── scripts/                       # 构建、验证、质检脚本
    └── qa/                            # 预览、构建清单与验证报告
```

`ready-to-use/` 是发布合同：普通用户只需它就能安装。`production-pipeline/` 是审计和再生产档案：它不参与安装，但保留“成品从哪里来”的证据。

## 哪些内容进入 GitHub

| 类别 | 位置 | 处理原则 |
| --- | --- | --- |
| 可安装成品 | `ready-to-use/` | 提交；每次发布都必须有清晰的预览和安装脚本。 |
| 角色设计、提示词、公开参考图、原始分镜、QA | `production-pipeline/` | 提交；这是可复现记录，不在根目录堆放。 |
| 透明抠像中间图、缓存、虚拟环境、日志 | `.gitignore` 指定的位置 | 不提交；可由现有源分镜重新生成。 |
| API Key、私密 `.env`、不可公开的原始输入图 | 工作区根目录或角色目录中被忽略的文件 | 永不读取、提交或上传。 |

## 新增角色

1. 从一个现有角色复制目录结构到 `pets/<new-slug>/`，但先更换 Pet ID、说明和设计文档。
2. 新角色默认使用 **V2**：先在 `DESIGN.md` 写明九个标准状态的固定帧计划；8 列是每行容量，不是每个动作都要画满 8 帧。完整映射和理由见[维护经验](MAINTAINER-NOTES.md#动作帧数是运行时合同)。
3. 先完成 `production-pipeline/references/` 与 `DESIGN.md`，再生成动作分镜。
4. 构建并通过该角色的结构与质量检查后，更新 `ready-to-use/`；最终图集必须在深色和浅色底上检查轮廓，确认没有绿边、孤立噪点或素材自身绘制的投影。
5. 在角色 README 添加安装命令、预览和版本类型（V1 或 V2）。
6. 按 [发布检查表](RELEASE-CHECKLIST.md) 检查后再提交。

不要为了“目录好看”删除已有参考图、源分镜或 QA。它们应留在角色自己的制作档案层，而不是散落在仓库根目录。
