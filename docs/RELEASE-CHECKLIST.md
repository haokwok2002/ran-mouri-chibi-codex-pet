# GitHub 发布检查表

在提交或发布任一角色前，逐项确认：

1. `ready-to-use/` 同时包含 `pet.json`、`spritesheet.webp`、`install.sh` 与 `install.ps1`。
2. 角色 README 中的安装命令、Pet ID、版本类型和预览路径与实际文件一致。
3. 运行该角色的验证与质量检查；人工查看 `preview.gif`、`transition-preview.gif` 和 `preview-sheet.png`。
4. 将最终透明精灵图在深色与浅色背景、真实单格尺寸下检查；不得出现绿边、孤立噪点或素材自身绘制的投影、地面阴影。
5. 确认 `.env`、`.env.*`（除 `.env.example`）、虚拟环境、缓存、日志、透明抠像中间图和不可公开输入图没有进入待提交列表。
6. 不在 README、脚本、报告或提示词中留下个人绝对路径、API Key 或内部服务地址。
7. 执行 `git diff --check`，并检查 `git status --short` 中没有意外文件。

普通用户只需要下载仓库、从根目录运行 `install.sh <角色 slug>` 或进入某个 `ready-to-use/` 目录运行其安装脚本；他们不需要 Python、图片模型或 `.env`。
