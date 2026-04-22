"""Statistical-analysis capability — frequency, gaps, co-occurrence, structural,
order, and PI-alignment.

Each result embeds `StatMeta` with dataset hash, window descriptor, window size,
and computation timestamp. A result without provenance is a bug.
"""

from __future__ import annotations

from service.statistics.base import (
    StatMeta,
    WindowSelection,
    make_meta,
    resolve_window,
)
from service.statistics.cooccurrence import (
    ARITY_MAX,
    ARITY_MIN,
    TOP_K_MAX,
    Combination,
    CooccurrenceResult,
    clear_cooccurrence_cache,
    compute_cooccurrence,
)
from service.statistics.frequency import (
    FrequencyResult,
    NumberFrequency,
    compute_frequency,
)
from service.statistics.gaps import (
    GapResult,
    HotColdThreshold,
    NumberGap,
    compute_gaps,
)
from service.statistics.order import OrderResult, PositionStat, compute_order
from service.statistics.pi_alignment import (
    PI_DIGITS,
    RULES,
    PiAlignmentResult,
    PiRule,
    compute_pi_alignment,
)
from service.statistics.structural import (
    HistogramBin,
    StructuralResult,
    compute_structural,
)

__all__ = [
    "ARITY_MAX",
    "ARITY_MIN",
    "PI_DIGITS",
    "RULES",
    "TOP_K_MAX",
    "Combination",
    "CooccurrenceResult",
    "FrequencyResult",
    "GapResult",
    "HistogramBin",
    "HotColdThreshold",
    "NumberFrequency",
    "NumberGap",
    "OrderResult",
    "PiAlignmentResult",
    "PiRule",
    "PositionStat",
    "StatMeta",
    "StructuralResult",
    "WindowSelection",
    "clear_cooccurrence_cache",
    "compute_cooccurrence",
    "compute_frequency",
    "compute_gaps",
    "compute_order",
    "compute_pi_alignment",
    "compute_structural",
    "make_meta",
    "resolve_window",
]
