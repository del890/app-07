"""Single-correlation and batch-correlation computations.

Single-correlation calls return a raw p-value only — no correction is invented
when the caller did not ask for one. Batch calls apply Benjamini-Hochberg FDR
across all results in the batch and populate ``q_value`` on every row, keeping
``p_value`` (raw) alongside so callers can see both.

Statistical tests:

- continuous metric → Spearman rank correlation (rho, p-value via two-sided t-approx)
- binary metric     → Mann-Whitney U (effect size as rank-biserial r, p-value from scipy)
"""

from __future__ import annotations

from datetime import UTC, datetime

from scipy import stats

from service.correlation.alignment import build_pairs
from service.correlation.metrics import resolve_metric
from service.correlation.models import (
    AlignmentPolicyName,
    BatchCorrelationResult,
    CorrelationInput,
    CorrelationResult,
    MetricSpec,
    SignalSeries,
    TestName,
)
from service.ingestion import DrawHistory

DEFAULT_MIN_SAMPLE_SIZE = 30

BH_DESCRIPTION = (
    "Benjamini-Hochberg (1995) step-up procedure controlling the false "
    "discovery rate at q = p * m / rank, with monotonicity enforcement."
)


def _spearman(signal: tuple[float, ...], metric: tuple[float, ...]) -> tuple[float, float]:
    if len(signal) < 2:
        return 0.0, 1.0
    result = stats.spearmanr(signal, metric)
    rho = float(result.statistic)
    pvalue = float(result.pvalue)
    # Guard against NaN when variance is zero on one side.
    if rho != rho:
        rho = 0.0
    if pvalue != pvalue:
        pvalue = 1.0
    return rho, pvalue


def _mann_whitney(
    signal: tuple[float, ...], metric_binary: tuple[float, ...]
) -> tuple[float, float]:
    """Return (rank-biserial effect size, two-sided p-value) for a binary split."""
    group_one = [s for s, m in zip(signal, metric_binary, strict=True) if m == 1.0]
    group_zero = [s for s, m in zip(signal, metric_binary, strict=True) if m == 0.0]
    if not group_one or not group_zero:
        # All mass on one side — no test, flat result.
        return 0.0, 1.0
    n1, n0 = len(group_one), len(group_zero)
    result = stats.mannwhitneyu(group_one, group_zero, alternative="two-sided")
    # scipy returns U1 for the first sample (group_one). When group_one tends
    # higher, U1 approaches n1*n0 (maximum). Rank-biserial correlation:
    #   r = 2*U1/(n1*n0) - 1  ∈ [-1, 1]; positive = group_one tends higher.
    u1 = float(result.statistic)
    pvalue = float(result.pvalue)
    effect = (2.0 * u1) / (n1 * n0) - 1.0
    if pvalue != pvalue:
        pvalue = 1.0
    return float(effect), pvalue


def correlate(
    history: DrawHistory,
    *,
    signal: SignalSeries,
    metric: MetricSpec,
    alignment: AlignmentPolicyName = "forward_fill",
    lag_draws: int = 0,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> CorrelationResult:
    """Compute a single correlation result (no multiple-comparisons correction).

    Returns with ``under_powered=True`` when the aligned sample size is below
    ``min_sample_size``; the result is *not* suppressed.
    """
    metric_values = resolve_metric(history, metric)
    signal_values, metric_paired, report = build_pairs(
        history, signal, metric_values, policy=alignment, lag_draws=lag_draws
    )

    test: TestName
    if metric.kind == "binary":
        test = "mann_whitney_u"
        effect, p_value = _mann_whitney(signal_values, metric_paired)
    else:
        test = "spearman"
        effect, p_value = _spearman(signal_values, metric_paired)

    sample_size = len(signal_values)
    return CorrelationResult(
        dataset_hash=history.provenance.content_hash,
        computed_at=datetime.now(UTC),
        input=CorrelationInput(
            signal_name=signal.name,
            signal_source=signal.source,
            signal_cadence=signal.cadence,
            signal_unit=signal.unit,
            metric_name=metric.name,
            metric_kind=metric.kind,
            metric_params=dict(metric.params),
        ),
        alignment=report,
        test=test,
        effect_size=effect,
        sample_size=sample_size,
        p_value=p_value,
        q_value=None,
        under_powered=sample_size < min_sample_size,
        min_sample_size=min_sample_size,
    )


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    """Return FDR-corrected q-values using the BH step-up procedure.

    Implementation is hand-rolled (no scipy dependency on this one) to make it
    easy to verify against a pen-and-paper calculation in tests.
    """
    m = len(p_values)
    if m == 0:
        return []
    # Sort ascending with original index tracked
    indexed = sorted(enumerate(p_values), key=lambda kv: kv[1])
    q_sorted: list[float] = [0.0] * m
    # BH raw: q_i = p_i * m / rank, where rank is 1-indexed
    for rank, (_, p) in enumerate(indexed, start=1):
        q_sorted[rank - 1] = min(1.0, p * m / rank)
    # Enforce monotonicity from the top down: q_sorted[i] = min(q_sorted[i], q_sorted[i+1])
    for i in range(m - 2, -1, -1):
        q_sorted[i] = min(q_sorted[i], q_sorted[i + 1])
    # Map back to original order
    q_values = [0.0] * m
    for rank, (orig_idx, _) in enumerate(indexed):
        q_values[orig_idx] = q_sorted[rank]
    return q_values


def correlate_batch(
    history: DrawHistory,
    *,
    signals: list[SignalSeries],
    metrics: list[MetricSpec],
    alignment: AlignmentPolicyName = "forward_fill",
    lag_draws: int = 0,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> BatchCorrelationResult:
    """Run correlations for every (signal, metric) pair and apply BH FDR correction."""
    raw_results: list[CorrelationResult] = []
    for signal in signals:
        for metric in metrics:
            raw_results.append(
                correlate(
                    history,
                    signal=signal,
                    metric=metric,
                    alignment=alignment,
                    lag_draws=lag_draws,
                    min_sample_size=min_sample_size,
                )
            )

    q_values = benjamini_hochberg([r.p_value for r in raw_results])
    corrected: tuple[CorrelationResult, ...] = tuple(
        r.model_copy(update={"q_value": q}) for r, q in zip(raw_results, q_values, strict=True)
    )
    return BatchCorrelationResult(
        dataset_hash=history.provenance.content_hash,
        computed_at=datetime.now(UTC),
        correction_method="benjamini_hochberg",
        correction_description=BH_DESCRIPTION,
        results=corrected,
    )
