#!/usr/bin/env python3
"""Tests for empirical analysis decoupling — skill works in guidance mode without deps."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.skill_guide import get_agent_guide, _is_skill_ready


class EmpiricalDecoupleTests(unittest.TestCase):
    def test_skill_guide_reports_readiness_status(self):
        """empirical-analysis reports ready=True if linearmodels installed, else provides hint."""
        guide = get_agent_guide(
            completed_skill="data-collector",
            artifacts=["data/clean/panel.csv"],
        )
        empirical_steps = [s for s in guide["next_steps"] if s["skill"] == "empirical-analysis"]
        if empirical_steps:
            step = empirical_steps[0]
            if step["ready"]:
                # linearmodels is installed in this env
                self.assertTrue(_is_skill_ready("empirical-analysis"))
            else:
                # Not installed — should have install hint
                self.assertIn("install_hint", step)
                self.assertIn("pip", step["install_hint"])

    def test_skill_md_exists_and_marks_optional(self):
        """empirical-analysis/SKILL.md exists and declares optional: true."""
        skill_path = Path(__file__).resolve().parent.parent / "skills" / "empirical-analysis" / "SKILL.md"
        self.assertTrue(skill_path.is_file())
        content = skill_path.read_text(encoding="utf-8")
        self.assertIn("optional: true", content)

    def test_install_guide_exists(self):
        """INSTALL_GUIDE.md provides tiered installation instructions."""
        guide_path = Path(__file__).resolve().parent.parent / "skills" / "empirical-analysis" / "INSTALL_GUIDE.md"
        self.assertTrue(guide_path.is_file())
        content = guide_path.read_text(encoding="utf-8")
        self.assertIn("builtin", content)
        self.assertIn("diff-diff", content)
        self.assertIn("statspai", content)


if __name__ == "__main__":
    unittest.main()
