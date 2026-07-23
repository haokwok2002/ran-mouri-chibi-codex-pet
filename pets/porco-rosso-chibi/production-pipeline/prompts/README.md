# 动作提示词目录

所有标准动作都先读取 `sequence-common.txt`，并把 `../references/porco-rosso-reference-green.png` 作为第一身份参考。提示词已锁定飞行帽、黑色墨镜、奶油白双排扣夹克、红领带、白裤和棕鞋；不得出现文字、Logo、场景、阴影、浮动特效或可见网格。

| 文件 | 用途 | 分镜 |
| --- | --- | --- |
| `idle.txt` | 安静待命 | 7 帧 + 第 8 格回环参考 |
| `running-right.txt` | 向右快跑 | 8 帧 |
| `waving.txt` | 飞行员式招呼 | 4 帧 |
| `jumping.txt` | 任务完成小跳 | 5 帧 + 第 6 格回环参考 |
| `failed.txt` | 克制认栽 | 8 帧 |
| `waiting.txt` | 整领带等待 | 6 帧 |
| `working.txt` | 无道具的飞行推演手势 | 6 帧，对应客户端 `running` 状态 |
| `review.txt` | 触胡子/下巴检查 | 6 帧 |
`running-left` 不单独生成：只在确认右向步态、服装和角色身份水平镜像后，逐格镜像 `running-right`，并保持原有帧序。
