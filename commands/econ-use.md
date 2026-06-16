---
name: econ-use
description: 切换到指定论文项目
---

用户说"切换到 XX 项目"时：
1. 检查 `papers/<name>/` 是否存在
2. 加载该项目的 pipeline_state.json
3. 更新 current_project.json（有 Python 后端时）
4. 无文件 → 对话记忆切换
5. 告知用户当前项目状态和可做之事
