---
name: econ-compile
description: 编译 LaTeX 论文为 PDF
---

当用户说"编译"时：
1. 检测 TeX Live 是否可用（`xelatex --version`）
2. 可用 → 执行 xelatex × 3 + biber 管线
3. 不可用 → 提示 Overleaf 上传路径或本地安装指引
4. 编译错误 → 提取关键错误信息，尝试自动修复
