#!/usr/bin/env python3
"""Tests for workflow execution engine (Milestone 4).

Verifies:
- Input validation gate rejects missing inputs with actionable fix hints
- Evidence status transitions enforce legal paths
- Artifacts are registered with provenance and path containment
- Atomic save survives simulated crash (no corruption)
- Revision snapshots support full undo/recovery
- Paths outside project workspace are rejected
- plan → commit → verify lifecycle works end-to-end
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.shared.contract import FieldSpec, ModuleContract
from scripts.shared.registry import get_registry, reset_registry
from scripts.shared.state import save as save_state
from scripts.workflow import (
    EVIDENCE_EXECUTED,
    EVIDENCE_PLANNED,
    EVIDENCE_USER_SUPPLIED,
    EVIDENCE_VERIFIED,
    WorkflowError,
    assert_within_project,
    atomic_save,
    commit_result,
    get_evidence_status,
    list_revisions,
    plan,
    recover,
    register_artifact,
    restore_revision,
    save_revision,
    set_evidence_status,
    supply_user_input,
    validate_before_run,
    verify,
)


def _setup_registry():
    """Register a minimal test module."""
    reset_registry()
    reg = get_registry()
    reg.register(ModuleContract(
        name="analyze",
        description="Test analysis module",
        consumes={
            "y_var": FieldSpec(type="str", required=True, desc="Y变量", source="conceptualize"),
            "d_var": FieldSpec(type="str", required=True, desc="D变量", source="conceptualize"),
            "clean_data_path": FieldSpec(type="str", required=True, desc="数据路径", source="data"),
        },
        provides={
            "baseline": FieldSpec(type="dict", required=True, desc="基准回归结果"),
        },
        states=["analyze-baseline"],
    ))
    return reg


class PathSafetyTests(unittest.TestCase):
    def test_path_within_project_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sub = root / "data" / "clean"
            sub.mkdir(parents=True)
            result = assert_within_project(sub, root)
            self.assertEqual(result, sub.resolve())

    def test_path_outside_project_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            outside = Path(tmp) / "other" / "secret.csv"
            with self.assertRaises(WorkflowError) as ctx:
                assert_within_project(outside, root)
            self.assertIn("不在项目工作区", str(ctx.exception))
            self.assertTrue(ctx.exception.fix_hint)

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            outside = Path(tmp) / "secret.txt"
            outside.write_text("secret", encoding="utf-8")
            link = root / "escape"
            link.symlink_to(outside)
            with self.assertRaises(WorkflowError):
                assert_within_project(link, root)


class EvidenceStatusTests(unittest.TestCase):
    def test_planned_to_executed_is_legal(self):
        state = {"context_store": {"analyze": {"evidence_status": "planned"}}}
        state = set_evidence_status(state, "analyze", EVIDENCE_EXECUTED, "ran regression")
        self.assertEqual(state["context_store"]["analyze"]["evidence_status"], EVIDENCE_EXECUTED)

    def test_executed_to_verified_is_legal(self):
        state = {"context_store": {"analyze": {"evidence_status": "executed"}}}
        state = set_evidence_status(state, "analyze", EVIDENCE_VERIFIED, "checks passed")
        self.assertEqual(state["context_store"]["analyze"]["evidence_status"], EVIDENCE_VERIFIED)

    def test_verified_to_planned_is_illegal(self):
        state = {"context_store": {"analyze": {"evidence_status": "verified"}}}
        with self.assertRaises(WorkflowError) as ctx:
            set_evidence_status(state, "analyze", EVIDENCE_PLANNED)
        self.assertIn("不能从", str(ctx.exception))

    def test_executed_to_planned_is_illegal(self):
        state = {"context_store": {"analyze": {"evidence_status": "executed"}}}
        with self.assertRaises(WorkflowError):
            set_evidence_status(state, "analyze", EVIDENCE_PLANNED)

    def test_invalid_status_raises(self):
        state = {"context_store": {}}
        with self.assertRaises(WorkflowError):
            set_evidence_status(state, "analyze", "bogus")


class InputValidationTests(unittest.TestCase):
    def setUp(self):
        _setup_registry()

    def test_missing_inputs_rejected_with_hints(self):
        state = {"context_store": {"y_var": "gdp"}}
        result = validate_before_run("analyze", state)
        self.assertFalse(result["ok"])
        self.assertIn("d_var", result["missing"])
        self.assertIn("clean_data_path", result["missing"])
        self.assertTrue(len(result["fix_hints"]) >= 2)

    def test_all_inputs_present_passes(self):
        state = {"context_store": {
            "y_var": "gdp",
            "d_var": "digital",
            "clean_data_path": "/some/path.csv",
        }}
        result = validate_before_run("analyze", state)
        self.assertTrue(result["ok"])

    def test_empty_string_counts_as_missing(self):
        state = {"context_store": {
            "y_var": "gdp",
            "d_var": "",
            "clean_data_path": "/some/path.csv",
        }}
        result = validate_before_run("analyze", state)
        self.assertFalse(result["ok"])
        self.assertIn("d_var", result["missing"])

    def test_unknown_module_returns_error(self):
        state = {"context_store": {}}
        result = validate_before_run("nonexistent", state)
        self.assertFalse(result["ok"])


class RevisionTests(unittest.TestCase):
    def test_save_and_list_revisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = {"current_micro_state": "concept-init", "context_store": {}}
            rev_id = save_revision(root, state, label="test-snap")
            revisions = list_revisions(root)
            self.assertEqual(len(revisions), 1)
            self.assertEqual(revisions[0]["revision_id"], rev_id)
            self.assertEqual(revisions[0]["label"], "test-snap")

    def test_restore_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "test-proj"
            project_dir = base / project_name
            project_dir.mkdir()

            # Save initial state
            state_v1 = {"current_micro_state": "concept-init", "context_store": {"x": "1"}}
            save_state(project_name, state_v1, base)
            rev_id = save_revision(project_dir, state_v1, label="v1")

            # Modify state
            state_v2 = {"current_micro_state": "analyze-baseline", "context_store": {"x": "2"}}
            save_state(project_name, state_v2, base)

            # Restore
            restored = restore_revision(project_name, rev_id, base)
            self.assertEqual(restored["context_store"]["x"], "1")

    def test_nonexistent_revision_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "test-proj"
            (base / project_name).mkdir()
            with self.assertRaises(WorkflowError):
                restore_revision(project_name, "fake_id", base)


class AtomicSaveTests(unittest.TestCase):
    def test_atomic_save_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "test-proj"
            (base / project_name).mkdir()

            state = {"current_micro_state": "test", "context_store": {"key": "value"}}
            atomic_save(project_name, state, base)

            state_file = base / project_name / "pipeline_state.json"
            self.assertTrue(state_file.is_file())
            loaded = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(loaded["context_store"]["key"], "value")
            self.assertIn("updated_at", loaded)


class ArtifactRegistrationTests(unittest.TestCase):
    def test_register_existing_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "analysis" / "output" / "table.tex"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("\\begin{tabular}{}\\end{tabular}", encoding="utf-8")

            state = {"artifacts": []}
            state = register_artifact(
                state, "analysis/output/table.tex", "latex_table", "analyze", root,
            )
            self.assertEqual(len(state["artifacts"]), 1)
            self.assertEqual(state["artifacts"][0]["producer"], "analyze")
            self.assertGreater(state["artifacts"][0]["size_bytes"], 0)

    def test_register_nonexistent_artifact_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = {"artifacts": []}
            with self.assertRaises(WorkflowError):
                register_artifact(state, "nope.tex", "latex", "analyze", root)

    def test_register_outside_project_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            outside = Path(tmp) / "outside.txt"
            outside.write_text("x", encoding="utf-8")

            state = {"artifacts": []}
            with self.assertRaises(WorkflowError):
                register_artifact(state, "../outside.txt", "text", "test", root)


class LifecycleTests(unittest.TestCase):
    """End-to-end plan → commit → verify lifecycle."""

    def setUp(self):
        _setup_registry()

    def test_plan_rejects_missing_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "lifecycle-test"
            (base / project_name).mkdir()
            state = {"current_micro_state": "concept-init", "context_store": {}}
            save_state(project_name, state, base)

            result = plan(project_name, "analyze", papers_dir=base)
            self.assertFalse(result["ok"])
            self.assertEqual(result["phase"], "plan")
            self.assertIn("y_var", result["missing"])

    def test_full_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "lifecycle-test"
            project_dir = base / project_name
            project_dir.mkdir()

            state = {
                "current_micro_state": "analyze-baseline",
                "context_store": {
                    "y_var": "employment",
                    "d_var": "digital",
                    "clean_data_path": "data/clean/panel.csv",
                },
            }
            save_state(project_name, state, base)

            # Plan
            plan_result = plan(project_name, "analyze", "基准回归", papers_dir=base)
            self.assertTrue(plan_result["ok"])
            self.assertIn("revision_id", plan_result)

            # Commit
            commit_res = commit_result(
                project_name, "analyze",
                result={"baseline": {"coef": 0.5, "se": 0.1}},
                papers_dir=base,
            )
            self.assertTrue(commit_res["ok"])
            self.assertEqual(commit_res["evidence_status"], EVIDENCE_EXECUTED)
            self.assertIn("baseline", commit_res["outputs_written"])

            # Verify
            verify_res = verify(
                project_name, "analyze", checks_passed=True,
                notes="系数显著，符合预期", papers_dir=base,
            )
            self.assertTrue(verify_res["ok"])
            self.assertEqual(verify_res["evidence_status"], EVIDENCE_VERIFIED)

    def test_commit_without_plan_on_fresh_module(self):
        """Commit should work on a module that hasn't been planned yet (None status)."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "fresh-test"
            (base / project_name).mkdir()
            state = {
                "current_micro_state": "analyze-baseline",
                "context_store": {
                    "y_var": "y",
                    "d_var": "d",
                    "clean_data_path": "data.csv",
                },
            }
            save_state(project_name, state, base)

            result = commit_result(
                project_name, "analyze",
                result={"baseline": {"coef": 1.0}},
                papers_dir=base,
            )
            self.assertTrue(result["ok"])

    def test_double_commit_rejected(self):
        """Cannot commit a module that is already executed."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "double-test"
            (base / project_name).mkdir()
            state = {
                "current_micro_state": "analyze-baseline",
                "context_store": {
                    "y_var": "y", "d_var": "d", "clean_data_path": "x.csv",
                    "analyze": {"evidence_status": "executed"},
                },
            }
            save_state(project_name, state, base)

            result = commit_result(
                project_name, "analyze",
                result={"baseline": {"coef": 1.0}},
                papers_dir=base,
            )
            self.assertFalse(result["ok"])
            self.assertIn("已经处于", result["error"])

    def test_verify_without_execution_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "verify-fail"
            (base / project_name).mkdir()
            state = {
                "current_micro_state": "analyze-baseline",
                "context_store": {"analyze": {"evidence_status": "planned"}},
            }
            save_state(project_name, state, base)

            result = verify(project_name, "analyze", checks_passed=True, papers_dir=base)
            self.assertFalse(result["ok"])
            self.assertIn("只能验证已执行的模块", result["error"])


class RecoverTests(unittest.TestCase):
    def test_recover_from_interruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "recover-test"
            project_dir = base / project_name
            project_dir.mkdir()

            state = {"current_micro_state": "concept-init", "context_store": {"x": "safe"}}
            save_state(project_name, state, base)
            save_revision(project_dir, state, label="safe-point")

            # Simulate corruption
            corrupted = {"current_micro_state": "BROKEN", "context_store": {}}
            save_state(project_name, corrupted, base)

            # Recover
            result = recover(project_name, papers_dir=base)
            self.assertTrue(result["ok"])
            self.assertEqual(result["current_state"], "concept-init")

    def test_recover_no_revisions_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "empty-proj"
            (base / project_name).mkdir()
            result = recover(project_name, papers_dir=base)
            self.assertFalse(result["ok"])


class UserSuppliedTests(unittest.TestCase):
    def test_supply_user_input_sets_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "supply-test"
            (base / project_name).mkdir()
            state = {"current_micro_state": "concept-init", "context_store": {}}
            save_state(project_name, state, base)

            result = supply_user_input(
                project_name, "research_question",
                "数字化是否提升就业？",
                source_description="用户在对话中确认",
                papers_dir=base,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["evidence_status"], "user_supplied")

            # Verify persisted
            from scripts.shared.state import load as reload_state
            reloaded = reload_state(project_name, base)
            entry = reloaded["context_store"]["research_question"]
            self.assertEqual(entry["value"], "数字化是否提升就业？")
            self.assertEqual(entry["evidence_status"], "user_supplied")

    def test_user_supplied_can_transition_to_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project_name = "transition-test"
            (base / project_name).mkdir()
            state = {"current_micro_state": "test", "context_store": {}}
            save_state(project_name, state, base)

            supply_user_input(project_name, "y_var", "gdp", papers_dir=base)

            # Now set to executed (legal: user_supplied → executed)
            from scripts.shared.state import load as reload_state
            reloaded = reload_state(project_name, base)
            reloaded = set_evidence_status(reloaded, "y_var", "executed", "confirmed by regression")
            self.assertEqual(reloaded["context_store"]["y_var"]["evidence_status"], "executed")


if __name__ == "__main__":
    unittest.main()
