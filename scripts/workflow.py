#!/usr/bin/env python3
"""Workflow execution engine — plan → run → commit lifecycle.

This module implements the Milestone 4 execution contract:
- Input validation gate before any module execution
- Evidence status tracking: planned → user_supplied → executed → verified
- Atomic state persistence with revision snapshots
- Artifact registration with provenance
- Interrupt recovery from the last stable revision
- Path containment (rejects paths outside project workspace)
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from scripts.shared.contract import ModuleContract
from scripts.shared.paths import PAPERS_DIR
from scripts.shared.registry import get_registry
from scripts.shared.state import (
    get_current_project,
    get_state_file,
    load as load_state,
    save as save_state,
)

# ── Evidence status constants ──

EVIDENCE_PLANNED = "planned"
EVIDENCE_USER_SUPPLIED = "user_supplied"
EVIDENCE_EXECUTED = "executed"
EVIDENCE_VERIFIED = "verified"

VALID_EVIDENCE_STATUSES = {
    EVIDENCE_PLANNED,
    EVIDENCE_USER_SUPPLIED,
    EVIDENCE_EXECUTED,
    EVIDENCE_VERIFIED,
}

# Legal evidence transitions (from → allowed targets)
_EVIDENCE_TRANSITIONS = {
    EVIDENCE_PLANNED: {EVIDENCE_USER_SUPPLIED, EVIDENCE_EXECUTED},
    EVIDENCE_USER_SUPPLIED: {EVIDENCE_EXECUTED, EVIDENCE_VERIFIED},
    EVIDENCE_EXECUTED: {EVIDENCE_VERIFIED},
    EVIDENCE_VERIFIED: set(),  # terminal
}

REVISIONS_DIR_NAME = ".revisions"
MAX_REVISIONS = 20


class WorkflowError(Exception):
    """Raised when a workflow operation is invalid."""

    def __init__(self, message: str, fix_hint: str = ""):
        super().__init__(message)
        self.fix_hint = fix_hint


# ── Path safety ──


def assert_within_project(path: Path | str, project_dir: Path) -> Path:
    """Ensure path resolves inside the project directory. Raises WorkflowError if not."""
    resolved = Path(path).expanduser().resolve()
    project_resolved = project_dir.resolve()
    try:
        resolved.relative_to(project_resolved)
    except ValueError:
        raise WorkflowError(
            f"路径 {resolved} 不在项目工作区 {project_resolved} 内",
            fix_hint="请使用相对于项目目录的路径",
        )
    return resolved


# ── Atomic state persistence ──


def _revisions_dir(project_dir: Path) -> Path:
    return project_dir / REVISIONS_DIR_NAME


def save_revision(project_dir: Path, state: dict, label: str = "") -> str:
    """Save a revision snapshot. Returns the revision ID."""
    rev_dir = _revisions_dir(project_dir)
    rev_dir.mkdir(parents=True, exist_ok=True)

    rev_id = f"{int(time.time())}_{os.getpid()}"
    rev_path = rev_dir / f"{rev_id}.json"

    snapshot = {
        "revision_id": rev_id,
        "label": label,
        "timestamp": datetime.now().isoformat(),
        "state": state,
    }
    # Atomic write: write to temp then rename
    fd, tmp_path = tempfile.mkstemp(dir=str(rev_dir), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(rev_path))
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    # Prune old revisions
    _prune_revisions(rev_dir)
    return rev_id


def _prune_revisions(rev_dir: Path) -> None:
    revisions = sorted(rev_dir.glob("*.json"), key=lambda p: p.stem)
    while len(revisions) > MAX_REVISIONS:
        revisions.pop(0).unlink()


def list_revisions(project_dir: Path) -> list[dict[str, str]]:
    """List available revisions, newest first."""
    rev_dir = _revisions_dir(project_dir)
    if not rev_dir.is_dir():
        return []
    results = []
    for path in sorted(rev_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            results.append({
                "revision_id": data.get("revision_id", path.stem),
                "label": data.get("label", ""),
                "timestamp": data.get("timestamp", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return results


def restore_revision(project_name: str, revision_id: str, papers_dir: Path | None = None) -> dict:
    """Restore project state from a specific revision."""
    base = papers_dir or PAPERS_DIR
    project_dir = base / project_name
    rev_dir = _revisions_dir(project_dir)
    rev_path = rev_dir / f"{revision_id}.json"

    if not rev_path.is_file():
        raise WorkflowError(
            f"修订版本 {revision_id} 不存在",
            fix_hint="使用 list_revisions 查看可用版本",
        )

    snapshot = json.loads(rev_path.read_text(encoding="utf-8"))
    state = snapshot["state"]
    save_state(project_name, state, base)
    return state


# ── Atomic save wrapper ──


def atomic_save(project_name: str, state: dict, papers_dir: Path | None = None) -> None:
    """Save state atomically: temp file → rename. Never corrupts on crash."""
    base = papers_dir or PAPERS_DIR
    state_file = get_state_file(project_name, base)
    state_file.parent.mkdir(parents=True, exist_ok=True)

    state["updated_at"] = datetime.now().isoformat()

    fd, tmp_path = tempfile.mkstemp(
        dir=str(state_file.parent), suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(state_file))
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ── Evidence status management ──


def get_evidence_status(state: dict, dimension: str) -> str | None:
    """Get the evidence status of a context dimension."""
    ctx = state.get("context_store", {})
    entry = ctx.get(dimension)
    if isinstance(entry, dict):
        return entry.get("evidence_status")
    return None


def set_evidence_status(
    state: dict, dimension: str, status: str, reason: str = ""
) -> dict:
    """Set evidence status for a dimension, enforcing legal transitions."""
    if status not in VALID_EVIDENCE_STATUSES:
        raise WorkflowError(
            f"无效证据状态: {status}",
            fix_hint=f"合法状态: {', '.join(sorted(VALID_EVIDENCE_STATUSES))}",
        )

    ctx = state.setdefault("context_store", {})
    entry = ctx.get(dimension, {})
    if not isinstance(entry, dict):
        entry = {"value": entry}

    current = entry.get("evidence_status")
    if current and current != status:
        allowed = _EVIDENCE_TRANSITIONS.get(current, set())
        if status not in allowed:
            raise WorkflowError(
                f"证据状态不能从 {current} 转到 {status}",
                fix_hint=f"允许的转换: {current} → {sorted(allowed) if allowed else '(终态)'}",
            )

    entry["evidence_status"] = status
    entry["status_updated_at"] = datetime.now().isoformat()
    if reason:
        entry["status_reason"] = reason
    ctx[dimension] = entry
    return state


# ── Artifact registration ──


def register_artifact(
    state: dict,
    artifact_path: str,
    artifact_type: str,
    producer: str,
    project_dir: Path,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """Register a produced artifact with provenance tracking."""
    # Validate path is within project
    abs_path = (project_dir / artifact_path).resolve()
    assert_within_project(abs_path, project_dir)

    if not abs_path.is_file():
        raise WorkflowError(
            f"产物文件不存在: {artifact_path}",
            fix_hint="请先确认文件已成功生成",
        )

    artifacts = state.setdefault("artifacts", [])
    record = {
        "path": artifact_path,
        "type": artifact_type,
        "producer": producer,
        "registered_at": datetime.now().isoformat(),
        "size_bytes": abs_path.stat().st_size,
    }
    if metadata:
        record["metadata"] = metadata

    # Replace existing record for the same path
    artifacts = [a for a in artifacts if a.get("path") != artifact_path]
    artifacts.append(record)
    state["artifacts"] = artifacts
    return state


# ── Input validation gate ──


def validate_before_run(
    module_name: str, state: dict
) -> dict[str, Any]:
    """Validate that all required inputs are present before running a module.

    Returns {"ok": True} or {"ok": False, "missing": [...], "fix_hints": [...]}.
    """
    registry = get_registry()
    contract = registry.get(module_name)
    if not contract:
        return {"ok": False, "missing": [], "fix_hints": [f"模块 '{module_name}' 未注册"]}

    ctx = state.get("context_store", {})
    missing = []
    fix_hints = []

    for key, spec in contract.consumes.items():
        if not spec.required:
            continue
        value = ctx.get(key)
        # A dict with only evidence_status but no real value doesn't count
        if value is None:
            missing.append(key)
            source = spec.source or "上游模块"
            fix_hints.append(f"'{key}' ({spec.desc}) 需由 {source} 提供")
        elif isinstance(value, dict) and "value" in value:
            if not value["value"]:
                missing.append(key)
                fix_hints.append(f"'{key}' 已注册但值为空")
        elif isinstance(value, str) and not value.strip():
            missing.append(key)
            fix_hints.append(f"'{key}' 为空字符串")

    return {
        "ok": len(missing) == 0,
        "missing": missing,
        "fix_hints": fix_hints,
    }


# ── Workflow lifecycle: plan → run → commit ──


def plan(
    project_name: str,
    module_name: str,
    description: str = "",
    papers_dir: Path | None = None,
) -> dict[str, Any]:
    """Plan phase: validate inputs and save a pre-execution snapshot.

    Returns a plan dict with validation result and revision ID.
    Does NOT modify the module state if validation fails.
    """
    base = papers_dir or PAPERS_DIR
    project_dir = base / project_name
    state = load_state(project_name, base)

    validation = validate_before_run(module_name, state)
    if not validation["ok"]:
        return {
            "ok": False,
            "phase": "plan",
            "error": "输入验证失败，无法推进",
            "missing": validation["missing"],
            "fix_hints": validation["fix_hints"],
        }

    # Save a pre-execution revision (recovery point)
    rev_id = save_revision(
        project_dir, state, label=f"pre:{module_name}:{description or 'plan'}"
    )

    # Mark the module as planned in state
    state = set_evidence_status(state, module_name, EVIDENCE_PLANNED, description)
    atomic_save(project_name, state, base)

    return {
        "ok": True,
        "phase": "plan",
        "module": module_name,
        "revision_id": rev_id,
        "description": description,
    }


def commit_result(
    project_name: str,
    module_name: str,
    result: dict[str, Any],
    artifacts: list[dict[str, str]] | None = None,
    papers_dir: Path | None = None,
) -> dict[str, Any]:
    """Commit phase: write module outputs to context and register artifacts.

    Only succeeds if the module was previously in 'planned' state.
    Transitions evidence status to 'executed'.
    """
    base = papers_dir or PAPERS_DIR
    project_dir = base / project_name
    state = load_state(project_name, base)

    # Verify the module was planned
    current_evidence = get_evidence_status(state, module_name)
    if current_evidence not in (EVIDENCE_PLANNED, None):
        # Allow re-execution from planned state only
        if current_evidence in (EVIDENCE_EXECUTED, EVIDENCE_VERIFIED):
            return {
                "ok": False,
                "phase": "commit",
                "error": f"模块 '{module_name}' 已经处于 {current_evidence} 状态",
                "fix_hint": "如需重新执行，请先回滚至 planned 状态",
            }

    # Write outputs to context_store
    registry = get_registry()
    contract = registry.get(module_name)
    ctx = state.setdefault("context_store", {})

    if contract:
        for key in contract.provides:
            if key in result:
                value = result[key]
                # Wrap in evidence-tracked dict
                ctx[key] = {
                    "value": value,
                    "evidence_status": EVIDENCE_EXECUTED,
                    "producer": module_name,
                    "committed_at": datetime.now().isoformat(),
                }

    # Register artifacts
    if artifacts:
        for art in artifacts:
            path = art.get("path", "")
            art_type = art.get("type", "unknown")
            if path:
                try:
                    register_artifact(
                        state, path, art_type, module_name, project_dir,
                        metadata=art.get("metadata"),
                    )
                except WorkflowError:
                    pass  # Non-fatal: artifact may not exist yet

    # Mark module as executed
    state = set_evidence_status(state, module_name, EVIDENCE_EXECUTED, "commit_result")

    # Save with revision
    save_revision(project_dir, state, label=f"post:{module_name}:executed")
    atomic_save(project_name, state, base)

    return {
        "ok": True,
        "phase": "commit",
        "module": module_name,
        "evidence_status": EVIDENCE_EXECUTED,
        "outputs_written": [k for k in (contract.provides if contract else {}) if k in result],
    }


def verify(
    project_name: str,
    module_name: str,
    checks_passed: bool,
    notes: str = "",
    papers_dir: Path | None = None,
) -> dict[str, Any]:
    """Verify phase: mark a module's outputs as verified (or not).

    Only succeeds if the module is currently 'executed'.
    """
    base = papers_dir or PAPERS_DIR
    project_dir = base / project_name
    state = load_state(project_name, base)

    current_evidence = get_evidence_status(state, module_name)
    if current_evidence != EVIDENCE_EXECUTED:
        return {
            "ok": False,
            "phase": "verify",
            "error": f"模块 '{module_name}' 当前状态为 {current_evidence or 'None'}，只能验证已执行的模块",
            "fix_hint": "先完成 plan → run → commit 生命周期",
        }

    if not checks_passed:
        return {
            "ok": False,
            "phase": "verify",
            "error": "验证未通过",
            "notes": notes,
            "fix_hint": "检查产物正确性后重新执行",
        }

    state = set_evidence_status(state, module_name, EVIDENCE_VERIFIED, notes)

    # Also update context entries that this module produced
    registry = get_registry()
    contract = registry.get(module_name)
    ctx = state.get("context_store", {})
    if contract:
        for key in contract.provides:
            entry = ctx.get(key)
            if isinstance(entry, dict) and entry.get("producer") == module_name:
                entry["evidence_status"] = EVIDENCE_VERIFIED
                entry["verified_at"] = datetime.now().isoformat()

    save_revision(project_dir, state, label=f"post:{module_name}:verified")
    atomic_save(project_name, state, base)

    return {
        "ok": True,
        "phase": "verify",
        "module": module_name,
        "evidence_status": EVIDENCE_VERIFIED,
        "notes": notes,
    }


# ── User-supplied evidence ──


def supply_user_input(
    project_name: str,
    key: str,
    value: Any,
    source_description: str = "",
    papers_dir: Path | None = None,
) -> dict[str, Any]:
    """Record a user-supplied value (not produced by code execution).

    Evidence status is set to 'user_supplied', distinct from 'executed'.
    This is for research decisions, manual observations, and externally
    obtained results that the user vouches for.
    """
    base = papers_dir or PAPERS_DIR
    state = load_state(project_name, base)
    ctx = state.setdefault("context_store", {})

    ctx[key] = {
        "value": value,
        "evidence_status": EVIDENCE_USER_SUPPLIED,
        "source": source_description or "user_supplied",
        "supplied_at": datetime.now().isoformat(),
    }

    project_dir = base / project_name
    save_revision(project_dir, state, label=f"user_supplied:{key}")
    atomic_save(project_name, state, base)

    return {
        "ok": True,
        "key": key,
        "evidence_status": EVIDENCE_USER_SUPPLIED,
    }


# ── Interrupt recovery ──


def recover(project_name: str, papers_dir: Path | None = None) -> dict[str, Any]:
    """Recover from the last stable revision after an interruption."""
    base = papers_dir or PAPERS_DIR
    project_dir = base / project_name
    revisions = list_revisions(project_dir)

    if not revisions:
        return {
            "ok": False,
            "error": "没有可恢复的修订版本",
            "fix_hint": "项目尚未进行任何 workflow 操作",
        }

    # Pick the most recent revision
    latest = revisions[0]
    state = restore_revision(project_name, latest["revision_id"], base)

    return {
        "ok": True,
        "restored_from": latest["revision_id"],
        "label": latest["label"],
        "timestamp": latest["timestamp"],
        "current_state": state.get("current_micro_state", "unknown"),
    }
