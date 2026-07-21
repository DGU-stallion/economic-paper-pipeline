#!/usr/bin/env python3
"""Real runtime smoke tests for module CLIs and analysis backends."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
MODULES = (
    "conceptualize", "research", "literature", "data",
    "analyze", "verify", "write", "format",
)


class ModuleCliTests(unittest.TestCase):
    def test_all_module_help_commands_succeed(self):
        failures = []
        for module in MODULES:
            result = subprocess.run(
                [sys.executable, "-m", f"scripts.modules.{module}", "--help"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                failures.append(f"{module}: {result.stderr.strip()}")
        self.assertEqual(failures, [], "\n\n".join(failures))


@unittest.skipUnless(
    importlib.util.find_spec("linearmodels") and importlib.util.find_spec("pandas"),
    "Standard analysis dependencies are not installed",
)
class AnalysisBackendTests(unittest.TestCase):
    def test_fe_fixture_executes_and_writes_latex(self):
        from scripts.backends.python_analysis import run_panel_ols

        with tempfile.TemporaryDirectory() as tmp:
            result = run_panel_ols(
                FIXTURES / "fe_minimal_data.csv", "y", "x", ["size", "lev"],
                fe_entity="firm", fe_time="year", cluster_entity="firm",
                project_dir=Path(tmp), backend="linearmodels",
            )
            self.assertEqual(result["backend_used"], "linearmodels")
            self.assertEqual(result["n"], 15)
            self.assertAlmostEqual(result["models"]["m1"]["params"]["x"], 1.0, places=6)
            self.assertTrue(Path(result["tex_path"]).is_file())

    def test_did_fixture_executes_and_writes_latex(self):
        from scripts.backends.python_analysis import run_did

        with tempfile.TemporaryDirectory() as tmp:
            result = run_did(
                FIXTURES / "did_minimal_data.csv", "y", "treat", "post", ["size"],
                fe_entity="firm", fe_time="year", cluster_entity="firm",
                project_dir=Path(tmp),
            )
            self.assertEqual(result["n"], 20)
            self.assertAlmostEqual(float(result["did_coef"]), 0.544, places=3)
            self.assertTrue((Path(tmp) / "analysis" / "output" / "02_did.tex").is_file())


if __name__ == "__main__":
    unittest.main()
