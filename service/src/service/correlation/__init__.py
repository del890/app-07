"""External-signal-correlation capability.

Research-only outputs — see `RESEARCH_DISCLAIMER`. Single correlations return a
raw p-value; batch correlations additionally attach a Benjamini-Hochberg q-value.
Under-powered correlations are flagged, never suppressed.
"""

from __future__ import annotations

from service.correlation.alignment import build_pairs
from service.correlation.compute import (
    BH_DESCRIPTION,
    DEFAULT_MIN_SAMPLE_SIZE,
    benjamini_hochberg,
    correlate,
    correlate_batch,
)
from service.correlation.loader import SignalLoadError, load_csv, load_json
from service.correlation.metrics import METRIC_CATALOG, resolve_metric
from service.correlation.models import (
    RESEARCH_DISCLAIMER,
    AlignmentPolicyName,
    AlignmentReport,
    BatchCorrelationResult,
    CorrectionMethod,
    CorrelationInput,
    CorrelationResult,
    MetricKind,
    MetricSpec,
    SignalCadence,
    SignalPoint,
    SignalSeries,
    TestName,
)

__all__ = [
    "BH_DESCRIPTION",
    "DEFAULT_MIN_SAMPLE_SIZE",
    "METRIC_CATALOG",
    "RESEARCH_DISCLAIMER",
    "AlignmentPolicyName",
    "AlignmentReport",
    "BatchCorrelationResult",
    "CorrectionMethod",
    "CorrelationInput",
    "CorrelationResult",
    "MetricKind",
    "MetricSpec",
    "SignalCadence",
    "SignalLoadError",
    "SignalPoint",
    "SignalSeries",
    "TestName",
    "benjamini_hochberg",
    "build_pairs",
    "correlate",
    "correlate_batch",
    "load_csv",
    "load_json",
    "resolve_metric",
]
