#!/usr/bin/env python3
"""Evidence-based paper state intelligence tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PaperStateTests(unittest.TestCase):
    def test_empty_project_reports_blockers_and_next_actions(self):
        from scripts.paper_state import scan_project

        with tempfile.TemporaryDirectory() as tmp:
            report = scan_project(Path(tmp), initiative_mode="collaborative")

        self.assertEqual(report["schema_version"], "1")
        self.assertEqual(report["dimensions"]["research_question"]["status"], "blocked")
        self.assertLess(report["overall_readiness"], 0.2)
        self.assertGreaterEqual(len(report["next_actions"]), 2)
        self.assertLessEqual(len(report["next_actions"]), 3)

    def test_scan_uses_real_artifacts_and_is_deterministic(self):
        from scripts.paper_state import scan_project

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._build_evidence_project(root)
            first = scan_project(root, initiative_mode="collaborative")
            second = scan_project(root, initiative_mode="collaborative")

        self.assertEqual(first, second)
        self.assertGreater(first["overall_readiness"], 0.65)
        self.assertEqual(first["dimensions"]["analysis"]["status"], "ready")
        self.assertIn("analysis/output/02_baseline_regression.tex", first["dimensions"]["analysis"]["evidence"])

    def test_placeholder_does_not_count_as_completed_writing(self):
        from scripts.paper_state import scan_project

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "paper").mkdir()
            (root / "paper" / "main.tex").write_text("TODO: 待补充实证结果", encoding="utf-8")
            report = scan_project(root)

        writing = report["dimensions"]["writing"]
        self.assertNotEqual(writing["status"], "ready")
        self.assertTrue(any("占位" in item for item in writing["blockers"]))

    def test_conservative_mode_requires_confirmation(self):
        from scripts.paper_state import scan_project

        with tempfile.TemporaryDirectory() as tmp:
            report = scan_project(Path(tmp), initiative_mode="conservative")

        self.assertTrue(report["next_actions"])
        self.assertTrue(all(action["requires_confirmation"] for action in report["next_actions"]))

    def test_pipeline_inspect_returns_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, "scripts/pipeline.py", "inspect", tmp, "--json"],
                cwd=Path(__file__).resolve().parent.parent,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["schema_version"], "1")

    @staticmethod
    def _build_evidence_project(root: Path) -> None:
        files = {
            "topics/00_research_proposal.md": "研究问题：数字化是否提升就业？\nY: employment\nD: digital\n识别策略: FE",
            "literature/00_candidate_papers.md": "# 候选论文\n论文 A\n论文 B",
            "literature/04_review_final.md": "# 文献综述\n现有研究与研究缺口。",
            "paper/erjref.bib": "@article{a, title={A}, year={2024}}",
            "data/raw/source.csv": "id,year,y,d\n1,2020,1,2\n",
            "data/clean/panel_clean.csv": "id,year,y,d\n1,2020,1,2\n",
            "data/02_validation_report.md": "主键唯一，关键变量无缺失。",
            "analysis/output/00_model_spec.md": "双向固定效应，按实体聚类。",
            "analysis/output/02_baseline_regression.tex": "\\begin{tabular}{} result \\end{tabular}",
            "analysis/output/03_robustness.tex": "\\begin{tabular}{} robust \\end{tabular}",
            "paper/main.tex": "\\documentclass{article}\\begin{document}结果见表1。\\end{document}",
            "paper/sections/01_introduction.tex": "研究背景与贡献。",
            "data/scripts/01_clean.py": "print('reproducible')",
        }
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        state = {
            "context_store": {
                "research_question": "数字化是否提升就业？",
                "y_var": "employment",
                "d_var": "digital",
                "identification": "FE",
                "baseline": {"evidence_status": "executed"},
            }
        }
        (root / "pipeline_state.json").write_text(json.dumps(state), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
