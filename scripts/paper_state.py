#!/usr/bin/env python3
"""Evidence-based paper project state inspection.

The scanner is intentionally read-only and dependency-free. It reports what
can be proven from project artifacts and structured context; it does not infer
completion from a directory name alone.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1"
INITIATIVE_MODES = {"conservative", "collaborative", "autopilot"}
PLACEHOLDER_MARKERS = ("todo", "tbd", "placeholder", "待补充", "待定", "示例结果")


def _relative(project_dir: Path, paths: Iterable[Path]) -> list[str]:
    return sorted({str(path.relative_to(project_dir)).replace("\\", "/") for path in paths if path.is_file()})


def _files(project_dir: Path, *patterns: str) -> list[Path]:
    found: list[Path] = []
    for pattern in patterns:
        found.extend(project_dir.glob(pattern))
    return sorted({path for path in found if path.is_file()})


def _read_text(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def _has_placeholder(paths: Iterable[Path]) -> bool:
    for path in paths:
        text = _read_text(path).lower()
        if any(marker in text for marker in PLACEHOLDER_MARKERS):
            return True
    return False


def _load_state(project_dir: Path) -> dict[str, Any]:
    state_path = project_dir / "pipeline_state.json"
    if not state_path.is_file():
        return {}
    try:
        value = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"_state_error": "pipeline_state.json 无法解析"}
    return value if isinstance(value, dict) else {"_state_error": "pipeline_state.json 必须是对象"}


def _find_context_value(value: Any, key: str) -> Any:
    if not isinstance(value, dict):
        return None
    direct = value.get(key)
    if direct not in (None, "", [], {}):
        return direct
    for nested in value.values():
        found = _find_context_value(nested, key)
        if found not in (None, "", [], {}):
            return found
    return None


def _dimension(
    readiness: float,
    evidence: list[str],
    blockers: list[str],
    unknowns: list[str] | None = None,
) -> dict[str, Any]:
    score = round(max(0.0, min(1.0, readiness)), 2)
    if score >= 0.75 and not blockers:
        status = "ready"
    elif score > 0:
        status = "in_progress"
    else:
        status = "blocked"
    return {
        "readiness": score,
        "status": status,
        "evidence": sorted(set(evidence)),
        "blockers": blockers,
        "unknowns": unknowns or [],
    }


def scan_project(project_dir: Path | str, initiative_mode: str = "collaborative") -> dict[str, Any]:
    """Inspect a paper project without modifying it."""
    if initiative_mode not in INITIATIVE_MODES:
        raise ValueError(f"未知主动模式: {initiative_mode}")

    root = Path(project_dir).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"论文项目目录不存在: {root}")

    state = _load_state(root)
    context = state.get("context_store", {}) if isinstance(state, dict) else {}

    proposal = _files(root, "topics/00_research_proposal.md", "topics/*proposal*.md")
    research_evidence = _relative(root, proposal)
    research_signals = {
        "research_question": bool(_find_context_value(context, "research_question")) or bool(proposal),
        "y_var": bool(_find_context_value(context, "y_var")),
        "d_var": bool(_find_context_value(context, "d_var")),
        "proposal": bool(proposal),
    }
    research_blockers = []
    if not research_signals["research_question"]:
        research_blockers.append("缺少明确的研究问题")
    if not research_signals["y_var"] or not research_signals["d_var"]:
        research_blockers.append("尚未确认核心 Y/D 变量")
    research = _dimension(sum(research_signals.values()) / 4, research_evidence, research_blockers)

    candidates = _files(root, "literature/00_candidate_papers.md", "literature/*candidate*.md")
    reviews = _files(root, "literature/*review*.md")
    bibliographies = _files(root, "paper/*.bib", "literature/*.bib")
    literature_evidence = _relative(root, candidates + reviews + bibliographies)
    literature_score = 0.25 * bool(candidates) + 0.4 * bool(reviews) + 0.25 * bool(bibliographies)
    literature_blockers = []
    if not candidates:
        literature_blockers.append("尚无候选文献清单")
    if not reviews:
        literature_blockers.append("尚无基于候选文献的综述")
    literature = _dimension(
        literature_score,
        literature_evidence,
        literature_blockers,
        ["引用真实性尚未形成机器可读验证记录"] if bibliographies else [],
    )

    raw_data = _files(root, "data/raw/**/*.*")
    clean_data = _files(root, "data/clean/**/*.*")
    quality_reports = _files(root, "data/*validation*.md", "data/*quality*.md")
    context_clean = _find_context_value(context, "clean_data_path")
    data_evidence = _relative(root, raw_data + clean_data + quality_reports)
    data_score = 0.25 * bool(raw_data) + 0.4 * bool(clean_data or context_clean) + 0.25 * bool(quality_reports)
    data_blockers = []
    if not raw_data and not clean_data and not context_clean:
        data_blockers.append("尚未发现可分析的数据")
    if (clean_data or context_clean) and not quality_reports:
        data_blockers.append("清洗后数据缺少质量验证报告")
    data = _dimension(data_score, data_evidence, data_blockers, ["实体、时间和聚类列尚未机器验证"])

    model_specs = _files(root, "analysis/**/*model_spec*.md", "analysis/**/*spec*.json")
    identification_value = _find_context_value(context, "identification")
    identification_score = 0.5 * bool(identification_value) + 0.5 * bool(model_specs)
    identification_blockers = []
    if not identification_value:
        identification_blockers.append("尚未确认识别策略")
    if not model_specs:
        identification_blockers.append("缺少可追溯的模型规格")
    identification = _dimension(
        identification_score,
        _relative(root, model_specs),
        identification_blockers,
        ["核心识别假设仍需研究者确认"] if identification_value else [],
    )

    baselines = _files(root, "analysis/**/*baseline*.tex", "analysis/**/*baseline*.json")
    robustness = _files(root, "analysis/**/*robust*.tex", "analysis/**/*robust*.json")
    baseline_context = _find_context_value(context, "baseline")
    executed = isinstance(baseline_context, dict) and baseline_context.get("evidence_status") in {"executed", "verified"}
    analysis_score = 0.55 * bool(baselines) + 0.25 * bool(robustness) + 0.2 * executed
    analysis_blockers = []
    if not baselines:
        analysis_blockers.append("尚无真实基准回归产物")
    if baselines and not executed:
        analysis_blockers.append("基准结果缺少 executed/verified 证据状态")
    analysis = _dimension(analysis_score, _relative(root, baselines + robustness), analysis_blockers)

    main_tex = _files(root, "paper/main.tex")
    sections = _files(root, "paper/sections/*.tex")
    writing_files = main_tex + sections
    writing_placeholder = _has_placeholder(writing_files)
    writing_score = 0.55 * bool(main_tex) + 0.25 * bool(sections) + 0.15 * bool(bibliographies)
    if writing_files and not writing_placeholder:
        writing_score += 0.05
    writing_blockers = []
    if not main_tex:
        writing_blockers.append("尚无论文主文件")
    if writing_placeholder:
        writing_blockers.append("论文仍包含占位内容")
    writing = _dimension(writing_score, _relative(root, writing_files + bibliographies), writing_blockers)

    scripts = _files(root, "data/scripts/*.py", "analysis/**/*.py", "analysis/**/*.do")
    manifests = _files(root, "runs/**/manifest.json", "artifact_manifest.json")
    reproducibility_score = 0.3 * bool((root / "pipeline_state.json").is_file()) + 0.35 * bool(scripts)
    reproducibility_score += 0.2 * bool(clean_data) + 0.15 * bool(manifests)
    reproducibility_blockers = []
    if state.get("_state_error"):
        reproducibility_blockers.append(state["_state_error"])
    if not scripts:
        reproducibility_blockers.append("缺少可重放的数据或分析脚本")
    if not manifests:
        reproducibility_blockers.append("缺少运行 provenance manifest")
    reproducibility_evidence = _relative(root, scripts + manifests)
    if (root / "pipeline_state.json").is_file():
        reproducibility_evidence.append("pipeline_state.json")
    reproducibility = _dimension(reproducibility_score, reproducibility_evidence, reproducibility_blockers)

    dimensions = {
        "research_question": research,
        "literature": literature,
        "data": data,
        "identification": identification,
        "analysis": analysis,
        "writing": writing,
        "reproducibility": reproducibility,
    }
    overall = round(sum(item["readiness"] for item in dimensions.values()) / len(dimensions), 2)

    return {
        "schema_version": SCHEMA_VERSION,
        "project": {"name": root.name, "path": str(root)},
        "initiative_mode": initiative_mode,
        "overall_readiness": overall,
        "dimensions": dimensions,
        "next_actions": _next_actions(dimensions, initiative_mode),
    }


def _next_actions(dimensions: dict[str, dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    definitions = [
        ("clarify-research", "明确研究问题和 Y/D 变量", "research_question", "local"),
        ("validate-data", "验证数据来源与面板结构", "data", "local_write"),
        ("search-literature", "搜索并验证核心与最新文献", "literature", "external"),
        ("confirm-identification", "确认识别策略与核心假设", "identification", "decision"),
        ("run-baseline", "执行并登记基准实证结果", "analysis", "analysis"),
        ("draft-paper", "基于已验证证据推进论文写作", "writing", "local_write"),
        ("record-provenance", "补齐可重放脚本和运行记录", "reproducibility", "local_write"),
    ]
    actions = []
    for action_id, title, dimension_name, risk in definitions:
        dimension = dimensions[dimension_name]
        if dimension["status"] == "ready":
            continue
        if mode == "conservative":
            requires_confirmation = True
        elif risk == "external":
            requires_confirmation = True
        elif mode == "autopilot":
            requires_confirmation = risk == "decision"
        else:
            requires_confirmation = risk in {"local_write", "decision", "analysis"}
        actions.append({
            "id": action_id,
            "title": title,
            "reason": dimension["blockers"][0] if dimension["blockers"] else "当前证据不足",
            "dimension": dimension_name,
            "requires_confirmation": requires_confirmation,
        })
    return actions[:3]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检查论文项目状态、阻塞项和下一行动")
    parser.add_argument("project", nargs="?", default=".", help="论文项目目录")
    parser.add_argument("--mode", choices=sorted(INITIATIVE_MODES), default="collaborative")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = scan_project(args.project, args.mode)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"论文状态：{report['overall_readiness']:.0%} ({report['initiative_mode']})")
        for name, dimension in report["dimensions"].items():
            print(f"- {name}: {dimension['readiness']:.0%} {dimension['status']}")
        print("下一步：")
        for index, action in enumerate(report["next_actions"], 1):
            print(f"{index}. {action['title']} — {action['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
