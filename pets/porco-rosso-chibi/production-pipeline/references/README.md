# 角色参考图

将后续获准使用的角色参考图存放在此处，并在文件旁记录来源与使用范围。制作时至少准备一张清晰的正面/三分之二全身参考图，用于锁定脸部、护目镜、飞行帽、夹克、领带和配色。

首个生产身份锚点固定命名为 `porco-rosso-reference-green.png`。它必须是全身、正面、纯 `#00FF00` 绿幕、无文字和无水印的单角色图；后续动作分镜应把它作为第一参考图。

当前锚点已由图片服务依据角色初始图重新绘制，再经 `../scripts/normalize_chroma_background.py` 标准化为精确绿幕；检查报告为 `../qa/reference-green-report.json`。`../scripts/prepare_reference.py` 保留作无网络时的本地备选流程。该锚点是生产用身份参考，不是最终安装资源。

不要将无法公开分发的参考素材混入最终 `ready-to-use/` 包。
