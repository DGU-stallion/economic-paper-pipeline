#!/usr/bin/env python3
"""调研助手 — 独立运行入口

提供三种使用方式：

1. 引导模式（默认）: 打印入口话术，让 LLM 引导用户对话
   $ python -m scripts.modules.research

2. 快速模式: 直接传入研究问题，输出模板化的搜索结果框架
   $ python -m scripts.modules.research --question "最低工资对就业的影响"

3. 提交模式: 向已有项目中写入搜索结果
   $ python -m scripts.modules.research --project my-paper --papers papers.json --sources sources.json

搜索后端优先级（自动检测）:
   Tavily → paper-search-mcp → WebSearch/WebFetch → 手动引导
"""

from __future__ import annotations
import argparse
import json
import sys
from scripts.shared.paths import PAPERS_DIR
from scripts.modules.research.core import run, commit_results
from scripts.modules.research.search_backends import detect_all, get_primary, get_summary
from scripts.modules.research.tavily_access import detect as detect_tavily


def main():
    parser = argparse.ArgumentParser(
        description="调研助手 — 经济学论文数据与文献调研",
    )
    parser.add_argument(
        "--question", "-q",
        help="研究问题（快速模式）",
    )
    parser.add_argument(
        "--project", "-p",
        help="项目名（写入 papers/<项目名>/ 目录）",
    )
    parser.add_argument(
        "--papers",
        help="候选论文 JSON 文件路径（提交模式）",
    )
    parser.add_argument(
        "--sources",
        help="数据源 JSON 文件路径（提交模式）",
    )
    parser.add_argument(
        "--verdict",
        choices=["feasible", "needs_adjustment", "infeasible"],
        help="可行性结论（提交模式）",
    )
    parser.add_argument(
        "--check-backends",
        action="store_true",
        help="仅检测可用搜索后端",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="输出入口话术供 LLM 使用（LLM 调用模式）",
    )

    args = parser.parse_args()

    # ── 检测搜索后端 ──
    all_backends = detect_all()
    primary = get_primary(all_backends)
    backend_summary = get_summary(all_backends)

    # ── 仅检测后端 ──
    if args.check_backends:
        print(json.dumps(all_backends, ensure_ascii=False, indent=2))
        print(f"\n主后端: {primary['name']}")
        return

    # ── 入口话术模式（LLM 调用） ──
    if args.standalone:
        tavily_status = detect_tavily()
        print(f"""\
你好，我是调研助手。我的工作是帮你从网络上搜集两样东西：

1. **相关文献** — 与你的研究问题相关的学术论文
2. **可用数据源** — 你能用来做实证研究的数据集

搜索后端状态:
{backend_summary}

当前主后端: {primary['name']} {'✅' if primary.get('available') else '⚠️'}

数据收集增强工具:
- tavily_search — 实时 web 搜索
- tavily_extract — 从 URL 提取干净正文（获取数据源页面结构化内容）
- tavily_crawl — 爬取数据门户所有链接（自动发现数据集）
- tavily_map — 发现站点 URL 结构（先探测再精准抓取）
- paper-search-mcp — 学术论文搜索（arXiv / Google Scholar / PubMed）

请告诉我：
- 你想研究什么？一句话说明研究问题
- 如果不确定，可以先告诉我研究方向，我帮你梳理关键词
""")
        return

    # ── 引导模式（无参数） ──
    if not args.question:
        print("调研助手 (Research Assistant)")
        print("=" * 50)
        print(f"\n搜索后端: {backend_summary}")
        print(f"主后端: {primary['name']}\n")
        print("用法:")
        print("  ｜ 引导模式:  python -m scripts.modules.research")
        print("  ｜ 快速模式:  python -m scripts.modules.research --question \"研究问题\"")
        print("  ｜ 提交模式:  python -m scripts.modules.research --project NAME --papers papers.json")
        print("  ｜ 后端检测:  python -m scripts.modules.research --check-backends")
        print()
        print("在 Claude 中直接说自然语言即可，不需要手动传参数。")
        return

    # ── 快速模式 / 提交模式 ──
    project_dir = None
    if args.project:
        project_dir = PAPERS_DIR / args.project
        if not project_dir.exists():
            print(f"项目 '{args.project}' 不存在")
            sys.exit(1)

    result = run(
        research_question=args.question,
        project_dir=project_dir,
    )

    # 记录使用的后端
    result["search_backend_used"] = primary["name"]

    # ── 提交模式：加载外部 JSON 结果 ──
    if args.papers:
        with open(args.papers, "r", encoding="utf-8") as f:
            result["candidate_papers"] = json.load(f)

    if args.sources:
        with open(args.sources, "r", encoding="utf-8") as f:
            result["data_sources"] = json.load(f)

    if args.verdict:
        result["feasibility_verdict"] = args.verdict

    # ── 写入项目 ──
    if project_dir and ((args.papers or args.sources) or args.verdict):
        if args.question:
            commit_results(result, project_dir, args.question)
        print(f"✅ 调研结果已写入 {project_dir / 'literature' / '00_candidate_papers.md'}")
        print(f"✅ 调研结果已写入 {project_dir / 'data' / '00_feasibility_report.md'}")
        print(f"   候选论文: {len(result.get('candidate_papers', []))} 篇")
        print(f"   数据源: {len(result.get('data_sources', []))} 个")
        print(f"   可行性: {result.get('feasibility_verdict', '?')}")
        print(f"   搜索后端: {result.get('search_backend_used', '?')}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
