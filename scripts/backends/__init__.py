#!/usr/bin/env python3
"""Backend capability detection and registry."""

from __future__ import annotations

HAS_LINEARMODELS = False
HAS_STATSMODELS = False
HAS_PANDAS = False
HAS_PYFIXEST = False
HAS_THRREG = False  # R package thrreg via rpy2
HAS_STATA = False

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

try:
    import pyfixest  # noqa: F401
    HAS_PYFIXEST = True
except ImportError:
    pass

try:
    import rpy2.robjects as ro
    from rpy2.robjects.packages import importr
    importr("thrreg")
    HAS_THRREG = True
except (ImportError, Exception):
    pass

try:
    import subprocess
    r = subprocess.run(["stata", "-q"], capture_output=True, text=True, timeout=5)
    HAS_STATA = r.returncode in (0, 1)
except (FileNotFoundError, Exception):
    pass


def detect() -> dict:
    """Return capability dict for AI agent decision-making."""
    return {
        "python_analysis": HAS_LINEARMODELS and HAS_STATSMODELS and HAS_PANDAS,
        "linearmodels": HAS_LINEARMODELS,
        "statsmodels": HAS_STATSMODELS,
        "pandas": HAS_PANDAS,
        "pyfixest": HAS_PYFIXEST,
        "thrreg": HAS_THRREG,
        "stata": HAS_STATA,
    }


def best_analysis_backend() -> str:
    """Return name of best available analysis backend."""
    if HAS_LINEARMODELS and HAS_STATSMODELS:
        return "python"
    if HAS_STATA:
        return "stata"
    return "llm_only"
