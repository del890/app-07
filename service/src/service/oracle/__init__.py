"""Dream-oracle capability.

Translates a free-text dream or scenario description into 15 Lotofácil number
suggestions via a structured symbolic-extraction pipeline.

Public surface:
  ``interpret_dream`` — main entry point (JSON or SSE streaming)
  ``DreamOracleResult`` — response model
  ``ORACLE_DISCLAIMER`` — the entertainment disclaimer string
"""

from __future__ import annotations

from service.oracle.agent import interpret_dream
from service.oracle.guard import DreamGuardError, check_dream_description
from service.oracle.models import DreamOracleResult, ExtractedSymbol
from service.oracle.prompt import ORACLE_DISCLAIMER

__all__ = [
    "DreamGuardError",
    "DreamOracleResult",
    "ExtractedSymbol",
    "ORACLE_DISCLAIMER",
    "check_dream_description",
    "interpret_dream",
]
