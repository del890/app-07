"""Pydantic models for the external-signal-correlation capability."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SignalCadence = Literal["daily", "weekly", "monthly", "event_keyed"]
AlignmentPolicyName = Literal["forward_fill", "event_keyed"]
TestName = Literal["spearman", "mann_whitney_u"]
MetricKind = Literal["continuous", "binary"]
CorrectionMethod = Literal["benjamini_hochberg"]


RESEARCH_DISCLAIMER = (
    "Research artifact only. Correlation does not imply causation; outputs "
    "from this capability must not be rendered in the play surface or used as "
    "predictions without going through the prediction engine."
)


class SignalPoint(BaseModel):
    """A single (date, value) observation in a signal series."""

    model_config = ConfigDict(frozen=True)

    date: date
    value: float


class SignalSeries(BaseModel):
    """A named external-signal time series registered with the correlation layer.

    Mandatory metadata (per the external-signal-correlation spec): ``name``,
    ``cadence``, ``unit``, ``source``. Values are date-indexed and
    chronologically sorted on construction.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    cadence: SignalCadence
    unit: str = Field(min_length=1)
    source: str = Field(min_length=1, description="Human-readable description of the data source.")
    description: str = ""
    points: tuple[SignalPoint, ...]

    @field_validator("points")
    @classmethod
    def _validate_points(cls, v: tuple[SignalPoint, ...]) -> tuple[SignalPoint, ...]:
        if not v:
            raise ValueError("signal series must contain at least one point")
        sorted_points = tuple(sorted(v, key=lambda p: p.date))
        # Duplicate dates are ambiguous under forward-fill and cause surprising
        # alignment behavior; reject them at ingest time.
        seen: set[date] = set()
        for p in sorted_points:
            if p.date in seen:
                raise ValueError(f"duplicate date in signal series: {p.date.isoformat()}")
            seen.add(p.date)
        return sorted_points


class MetricSpec(BaseModel):
    """Declarative description of a draw-derived metric.

    v1 metric catalog (see `service.correlation.metrics.resolve_metric`):

    - ``sum`` — continuous; `sum(draw.numbers_sorted)`.
    - ``even_count`` — continuous; number of even numbers in the draw.
    - ``number_present`` — binary; 1 if ``params['number']`` appears, else 0.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    kind: MetricKind
    params: dict[str, int | float | str] = Field(default_factory=dict)


class CorrelationInput(BaseModel):
    """Provenance of the inputs a correlation was computed over."""

    model_config = ConfigDict(frozen=True)

    signal_name: str
    signal_source: str
    signal_cadence: SignalCadence
    signal_unit: str
    metric_name: str
    metric_kind: MetricKind
    metric_params: dict[str, int | float | str]


class AlignmentReport(BaseModel):
    """How the signal was aligned against the draw timeline for this result."""

    model_config = ConfigDict(frozen=True)

    policy: AlignmentPolicyName
    lag_draws: int = Field(
        description=(
            "Signal value at draw T is joined with the metric at draw T + lag_draws. "
            "Positive lag → signal leads metric; negative lag → signal trails metric."
        )
    )


class CorrelationResult(BaseModel):
    """A single correlation result, fully labelled as a research artifact."""

    model_config = ConfigDict(frozen=True)

    artifact_type: Literal["research"] = "research"
    disclaimer: str = RESEARCH_DISCLAIMER

    dataset_hash: str
    computed_at: datetime

    input: CorrelationInput
    alignment: AlignmentReport

    test: TestName
    effect_size: float = Field(
        description=(
            "For Spearman: rank correlation rho in [-1, 1]. "
            "For Mann-Whitney: rank-biserial effect size in [-1, 1]."
        )
    )
    sample_size: int = Field(ge=0)
    p_value: float = Field(
        ge=0.0,
        le=1.0,
        description="Raw two-sided p-value from the statistical test.",
    )
    q_value: float | None = Field(
        default=None,
        description=(
            "Benjamini-Hochberg FDR-corrected q-value. Only populated when the "
            "result came from a batch call; single-correlation calls leave this None "
            "to avoid fabricating a correction that wasn't applied."
        ),
    )
    under_powered: bool = Field(
        description=(
            "True when the aligned sample size fell below the documented minimum. "
            "Such results are returned (not suppressed) but must be surfaced with this flag."
        ),
    )
    min_sample_size: int = Field(ge=1)


class BatchCorrelationResult(BaseModel):
    """Result of a batch correlation run with multiple-comparisons correction."""

    model_config = ConfigDict(frozen=True)

    artifact_type: Literal["research"] = "research"
    disclaimer: str = RESEARCH_DISCLAIMER

    dataset_hash: str
    computed_at: datetime

    correction_method: CorrectionMethod
    correction_description: str
    results: tuple[CorrelationResult, ...]
