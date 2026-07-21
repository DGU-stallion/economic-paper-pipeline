#!/usr/bin/env python3
"""Validate that CLI examples shown in README actually work.

Release gate: "README 示例均经过自动验证"

Tests the key commands that appear in the README quick-start section.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class ReadmeCliExamplesTests(unittest.TestCase):
    """Verify all CLI commands shown in README execute successfully."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = {
            **os.environ,
            "EPP_PAPERS_DIR": self.tmp,
            "EPP_CONFIG_DIR": str(Path(self.tmp) / ".config"),
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "pipeline.py"), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=self.env,
        )

    def test_list_command(self):
        """README: python3 scripts/pipeline.py list"""
        result = self._run("list")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_new_project(self):
        """README: python3 scripts/pipeline.py new my-paper"""
        result = self._run("new", "my-paper")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("创建成功", result.stdout)

    def test_status_after_new(self):
        """README: python3 scripts/pipeline.py status"""
        self._run("new", "status-test")
        self._run("use", "status-test")
        result = self._run("status")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_cleanup_command(self):
        """README: python3 scripts/pipeline.py cleanup"""
        self._run("new", "cleanup-test")
        self._run("use", "cleanup-test")
        result = self._run("cleanup")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_help_command(self):
        """README: epp help — lists available commands"""
        result = self._run("help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("可用命令", result.stdout)

    def test_doctor_check_json(self):
        """README: python3 install/bootstrap.py --check --profile standard --json"""
        result = subprocess.run(
            [sys.executable, str(ROOT / "install" / "bootstrap.py"),
             "--check", "--profile", "standard", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("status", report)
        self.assertIn("capabilities", report)

    def test_inspect_json(self):
        """README equivalent: epp inspect <dir> --json"""
        result = self._run("inspect", self.tmp, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], "1")

    def test_workflow_subcommand_exists(self):
        """epp workflow shows usage (not an error)"""
        result = self._run("workflow")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("plan", result.stdout)


class VersionSingleSourceTests(unittest.TestCase):
    """Release gate: version has a single source of truth."""

    def test_version_source_is_scripts_init(self):
        """pyproject.toml reads version from scripts.__version__"""
        from scripts import __version__
        self.assertTrue(__version__.startswith("5."))

    def test_pyproject_references_dynamic_version(self):
        """pyproject.toml uses dynamic = ["version"] sourced from scripts.__init__"""
        import tomllib
        with open(ROOT / "pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        self.assertIn("version", config["project"].get("dynamic", []))
        self.assertEqual(
            config["tool"]["setuptools"]["dynamic"]["version"]["attr"],
            "scripts.__version__",
        )


if __name__ == "__main__":
    unittest.main()
