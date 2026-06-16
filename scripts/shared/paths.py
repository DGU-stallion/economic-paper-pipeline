#!/usr/bin/env python3
"""
Central path configuration.

All path resolution goes through this module.
Derives PROJECT_ROOT from file location (not cwd).
PAPERS_DIR / CONFIG_DIR: env var override, then PROJECT_ROOT fallback.
"""
from __future__ import annotations
from pathlib import Path
import os

# ── Root: always scripts/shared/paths.py → PROJECT_ROOT ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ── Platform-agnostic root ──
PROJECT_ROOT = _PROJECT_ROOT

# ── Data / config dirs (env override, PROJECT_ROOT fallback) ──
PAPERS_DIR = Path(
    os.environ.get("EPP_PAPERS_DIR", str(_PROJECT_ROOT / "papers"))
)
CONFIG_DIR = Path(
    os.environ.get("EPP_CONFIG_DIR", str(_PROJECT_ROOT / ".config"))
)

# ── Templates ──
TEMPLATES_DIR = _PROJECT_ROOT / "templates"
