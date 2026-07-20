#!/usr/bin/env python3
"""Agent bootstrap and doctor contract tests."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP = ROOT / "install" / "bootstrap.py"


class BootstrapContractTests(unittest.TestCase):
    def run_bootstrap(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-I", str(BOOTSTRAP), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_standard_check_returns_stable_json_report(self):
        result = self.run_bootstrap("--check", "--profile", "standard", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)

        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], "1")
        self.assertEqual(report["profile"], "standard")
        self.assertIn(report["status"], {"ready", "degraded"})
        self.assertIn("python", report["capabilities"])
        self.assertIn("analysis", report["capabilities"])
        self.assertIn("latex", report["capabilities"])
        self.assertIsInstance(report["recommendations"], list)

    def test_lite_profile_does_not_require_analysis_backend(self):
        result = self.run_bootstrap("--check", "--profile", "lite", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["profile"], "lite")
        self.assertTrue(report["capabilities"]["python"]["available"])

    def test_pipeline_exposes_doctor_json(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "pipeline.py"), "doctor", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["schema_version"], "1")

    def test_agent_install_contract_exists(self):
        contract = ROOT / "AGENT_INSTALL.md"
        self.assertTrue(contract.is_file())
        content = contract.read_text(encoding="utf-8")
        self.assertIn("bootstrap.py", content)
        self.assertIn("不要上传", content)


if __name__ == "__main__":
    unittest.main()
