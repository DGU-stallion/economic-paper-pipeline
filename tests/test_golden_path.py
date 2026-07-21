#!/usr/bin/env python3
"""Golden path test — validates the canonical research workflow via CLI.

Tests that the workflow can be driven entirely through the CLI protocol
described in SKILL.md, without depending on any specific agent's chat history.

This verifies Milestone 5 acceptance:
- Three agent types use the same core state and artifact schema
- Agents without proprietary skill mechanisms can operate via CLI
- Agent switch does not require original chat history
- Golden path runs in a reproducible local environment
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


class GoldenPathCliTests(unittest.TestCase):
    """Drive the golden path through the CLI protocol (no agent-specific APIs)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.project_dir = Path(self.tmp) / "test-golden"
        self.project_dir.mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_pp(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "pipeline.py"), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={
                **__import__("os").environ,
                "EPP_PAPERS_DIR": self.tmp,
                "EPP_CONFIG_DIR": str(Path(self.tmp) / ".config"),
            },
        )

    def test_inspect_empty_project_reports_blockers(self):
        """pp inspect on an empty dir outputs valid JSON with blockers."""
        result = self._run_pp("inspect", str(self.project_dir), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], "1")
        self.assertLess(report["overall_readiness"], 0.2)
        self.assertTrue(report["next_actions"])

    def test_doctor_runs_without_error(self):
        """pp doctor --check --json exits 0 with a valid report."""
        result = self._run_pp("doctor", "--check", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("status", report)

    def test_workflow_plan_rejects_missing_context(self):
        """pp workflow plan analyze fails without upstream context."""
        # Create a project first
        self._run_pp("new", "test-golden")
        self._run_pp("use", "test-golden")

        result = self._run_pp("workflow", "plan", "analyze", "基准回归")
        self.assertNotEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertFalse(output["ok"])
        self.assertIn("y_var", output["missing"])

    def test_full_golden_path_with_fixtures(self):
        """Simulate the golden path: conceptualize → data → analyze → verify.

        Uses pre-built fixtures to avoid needing real web search or TeX.
        """
        from scripts.shared.state import save as save_state, load as load_state
        from scripts.workflow import (
            plan, commit_result, verify, supply_user_input,
        )
        from scripts.shared.registry import reset_registry, get_registry
        from scripts.shared.contract import ModuleContract, FieldSpec

        # Register modules
        reset_registry()
        reg = get_registry()
        for mod_name in [
            "conceptualize", "research", "literature", "data",
            "analyze", "verify", "write", "format",
        ]:
            mod = __import__(f"scripts.modules.{mod_name}", fromlist=["MODULE_CONTRACT"])
            reg.register(mod.MODULE_CONTRACT)

        project_name = "test-golden"
        papers_dir = Path(self.tmp)
        project_dir = papers_dir / project_name
        project_dir.mkdir(exist_ok=True)

        # Initialize state
        state = {
            "current_micro_state": "concept-init",
            "context_store": {},
            "micro_state_history": [],
            "stage_completed": [],
        }
        save_state(project_name, state, papers_dir)

        # Step 1: Conceptualize (user supplies research question)
        supply_user_input(
            project_name, "research_question",
            "数字化转型是否提升制造业企业就业？",
            source_description="用户确认研究问题",
            papers_dir=papers_dir,
        )
        supply_user_input(project_name, "y_var", "employment", papers_dir=papers_dir)
        supply_user_input(project_name, "d_var", "digital_index", papers_dir=papers_dir)
        supply_user_input(project_name, "identification", "FE", papers_dir=papers_dir)
        supply_user_input(
            project_name, "control_vars", ["size", "age", "leverage"],
            papers_dir=papers_dir,
        )

        # Step 2: Data (supply clean data path)
        data_dir = project_dir / "data" / "clean"
        data_dir.mkdir(parents=True)
        fixture_data = FIXTURES / "fe_minimal_data.csv"
        import shutil
        shutil.copy(fixture_data, data_dir / "panel_clean.csv")

        supply_user_input(
            project_name, "clean_data_path",
            str(data_dir / "panel_clean.csv"),
            papers_dir=papers_dir,
        )

        # Step 3: Analyze — plan should now succeed
        plan_result = plan(project_name, "analyze", "基准回归", papers_dir=papers_dir)
        self.assertTrue(plan_result["ok"], plan_result)

        # Simulate execution result
        commit_res = commit_result(
            project_name, "analyze",
            result={"baseline": {"coef": 1.0, "se": 0.05, "n": 15}},
            papers_dir=papers_dir,
        )
        self.assertTrue(commit_res["ok"], commit_res)
        self.assertIn("baseline", commit_res["outputs_written"])

        # Step 4: Verify
        verify_res = verify(
            project_name, "analyze", checks_passed=True,
            notes="系数 1.0 符合预期方向",
            papers_dir=papers_dir,
        )
        self.assertTrue(verify_res["ok"], verify_res)

        # Final check: load state and confirm evidence chain
        final_state = load_state(project_name, papers_dir)
        ctx = final_state["context_store"]

        # User-supplied inputs
        self.assertEqual(ctx["research_question"]["evidence_status"], "user_supplied")
        self.assertEqual(ctx["y_var"]["evidence_status"], "user_supplied")

        # Executed and verified outputs
        self.assertEqual(ctx["baseline"]["evidence_status"], "verified")
        self.assertEqual(ctx["baseline"]["value"]["coef"], 1.0)

        # Module-level evidence
        self.assertEqual(ctx["analyze"]["evidence_status"], "verified")


class AgentCapabilityTests(unittest.TestCase):
    """Test that capability declaration works for all three agent types."""

    def test_declare_and_read_capabilities(self):
        from scripts.agent_caps import declare_capabilities, get_capabilities

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "cap-test"
            (base / project_name).mkdir()

            # Initialize state
            from scripts.shared.state import save as save_state
            save_state(project_name, {"current_micro_state": "init", "context_store": {}}, base)

            caps = declare_capabilities(
                "kiro", web_search=True, mcp_servers=["tavily"],
                project_name=project_name, papers_dir=base,
            )
            self.assertEqual(caps["agent_type"], "kiro")
            self.assertTrue(caps["web_search"])
            self.assertIn("tavily", caps["mcp_servers"])

            # Read back
            read_caps = get_capabilities(project_name, base)
            self.assertEqual(read_caps["agent_type"], "kiro")

    def test_capability_matrix(self):
        from scripts.agent_caps import declare_capabilities, capability_matrix

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "matrix-test"
            (base / project_name).mkdir()

            from scripts.shared.state import save as save_state
            save_state(project_name, {"current_micro_state": "init", "context_store": {}}, base)

            declare_capabilities(
                "codex", web_search=False,
                project_name=project_name, papers_dir=base,
            )

            matrix = capability_matrix(project_name, base)
            # Codex has no web search → research is degraded
            self.assertTrue(matrix["research"]["degraded"])
            # Conceptualize always works
            self.assertTrue(matrix["conceptualize"]["available"])
            self.assertFalse(matrix["conceptualize"]["degraded"])

    def test_all_three_agents_share_same_state_schema(self):
        """Claude Code, Codex, and Kiro all use the same state format."""
        from scripts.agent_caps import declare_capabilities, get_capabilities
        from scripts.shared.state import save as save_state, load as load_state

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "shared-schema"
            (base / project_name).mkdir()
            save_state(project_name, {"current_micro_state": "init", "context_store": {}}, base)

            for agent_type in ("claude-code", "codex", "kiro"):
                declare_capabilities(
                    agent_type, web_search=(agent_type != "codex"),
                    project_name=project_name, papers_dir=base,
                )
                state = load_state(project_name, base)
                # All agents write to the same key
                self.assertIn("agent_capabilities", state)
                self.assertEqual(state["agent_capabilities"]["agent_type"], agent_type)

    def test_agent_switch_preserves_context(self):
        """Switching agents does not lose research progress."""
        from scripts.agent_caps import declare_capabilities
        from scripts.workflow import supply_user_input
        from scripts.shared.state import save as save_state, load as load_state

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "switch-test"
            (base / project_name).mkdir()
            save_state(project_name, {"current_micro_state": "init", "context_store": {}}, base)

            # Agent 1 (Claude Code) does conceptualize
            declare_capabilities("claude-code", web_search=True,
                                 project_name=project_name, papers_dir=base)
            supply_user_input(project_name, "research_question", "AI与就业",
                              papers_dir=base)

            # Agent 2 (Kiro) takes over — context is preserved
            declare_capabilities("kiro", web_search=True,
                                 project_name=project_name, papers_dir=base)
            state = load_state(project_name, base)
            self.assertEqual(
                state["context_store"]["research_question"]["value"],
                "AI与就业",
            )
            self.assertEqual(state["agent_capabilities"]["agent_type"], "kiro")


if __name__ == "__main__":
    unittest.main()
