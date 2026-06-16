#!/usr/bin/env python3
"""Backend capability detection and registry."""

from __future__ import annotations

HAS_LINEARMODELS = False
HAS_STATSMODELS = False
HAS_PANDAS = False

try:
    import linearmodels  # noqa: F401
    HAS_LINEARMODELS = True
except ImportError:
    pass

try:
    import statsmodels  # noqa: F401
    HAS_STATSMODELS = True
except ImportError:
    pass

try:
    import pandas  # noqa: F401
    HAS_PANDAS = True
except ImportError:
    pass


def detect() -> dict:
    """Return capability dict for AI agent decision-making."""
    return {
        "python_analysis": HAS_LINEARMODELS and HAS_STATSMODELS and HAS_PANDAS,
        "linearmodels": HAS_LINEARMODELS,
        "statsmodels": HAS_STATSMODELS,
        "pandas": HAS_PANDAS,
    }


def best_analysis_backend() -> str:
    """Return name of best available analysis backend."""
    if HAS_LINEARMODELS and HAS_STATSMODELS:
        return "python"
    return "llm_only"
