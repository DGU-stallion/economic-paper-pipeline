#!/usr/bin/env python3
"""概念助手 — 独立运行入口

用法:
  # 引导模式: 输出入口话术，让 LLM 引导用户对话
  python -m scripts.modules.conceptualize

  # 快速模式: 直接传入研究问题，启动 5W1H 流程
  python -m scripts.modules.conceptualize --idea "最低工资对就业的影响"

  # 提交模式: 将概念化结果写入项目
  python -m scripts.modules.conceptualize --project my-paper \
      --question "..." --y employment --d min_wage --identification DID
"""

from __future__ import annotations
import argparse
import json
import sys
from scripts.shared.paths import PAPERS_DIR
from scripts.modules.conceptualize.core import run, commit_proposal, ENTRY_PROMPT


def main():
    parser = argparse.ArgumentParser(
        description="概念助手 — 经济学论文选题与概念化",
    )
    parser.add_argument(
        "--idea", "-i",
        help="一句话研究想法（快速模式）",
    )
    parser.add_argument(
        "--project", "-p",
        help="项目名（写入 papers/<项目名>/ 目录）",
    )
    parser.add_argument("--question", help="研究问题（提交模式）")
    parser.add_argument("--y", help="被解释变量 Y")
    parser.add_argument("--d", help="核心解释变量 D")
    parser.add_argument("--identification", help="识别策略")
    parser.add_argument("--hypotheses", nargs="*", help="研究假设列表")
    parser.add_argument("--controls", nargs="*", help="控制变量列表")
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="输出入口话术供 LLM 使用",
    )

    args = parser.parse_args()

    if args.standalone:
        print(ENTRY_PROMPT)
        return

    if not args.idea and not all([args.question, args.y, args.d]):
        print("概念助手 (Conceptualize)")
        print("=" * 50)
        print()
        print("用法:")
        print("  ｜ 引导模式: python -m scripts.modules.conceptualize")
        print("  ｜ 快速模式: python -m scripts.modules.conceptualize --idea \"研究想法\"")
        print("  ｜ 提交模式: python -m scripts.modules.conceptualize --project NAME \\")
        print("  ｜             --question \"...\" --y Y --d D --identification DID")
        print()
        print("在 Claude 中直接说自然语言即可，不需要手动传参数。")
        return

    project_dir = None
    if args.project:
        project_dir = PAPERS_DIR / args.project
        if not project_dir.exists():
            print(f"项目 '{args.project}' 不存在")
            sys.exit(1)

    if args.idea:
        result = run(initial_idea=args.idea, project_dir=project_dir)
    else:
        result = {
            "research_question": args.question or "",
            "y_var": args.y or "",
            "d_var": args.d or "",
            "identification": args.identification or "",
            "hypotheses": args.hypotheses or [],
            "control_vars": args.controls or [],
            "keywords": [],
        }

    if project_dir:
        commit_proposal(result, project_dir)
        print(f"✅ 研究方案已写入 {project_dir / 'topics' / '00_research_proposal.md'}")
        print(f"   研究问题: {result['research_question']}")
        print(f"   Y: {result['y_var']}, D: {result['d_var']}")
        print(f"   识别策略: {result['identification']}")
        print(f"   假设: {len(result.get('hypotheses', []))} 条")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
