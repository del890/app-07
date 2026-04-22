"""Align a signal time series to the chronological draw timeline.

Two policies in v1:

- **forward_fill**: for each draw date, use the most recent signal value at or
  before that date. Appropriate for continuous signals (markets, indices)
  sampled at a slower or equal cadence than draws.
- **event_keyed**: align only on exact date matches. Appropriate for calendar
  signals (holidays, named events) where forward-filling past the event is
  meaningless.

Lag semantics: ``lag_draws`` shifts the *pairing*, not the signal. The signal
value aligned to draw T is paired with the metric at draw T + lag_draws. This
matches the spec ("signal value at draw T is joined against draw T+N").
"""

from __future__ import annotations

from bisect import bisect_right
from datetime import date

from service.correlation.models import AlignmentPolicyName, AlignmentReport, SignalSeries
from service.ingestion import DrawHistory


def _forward_fill_value(
    dates_sorted: list[date],
    values: list[float],
    target: date,
) -> float | None:
    """Return the most recent value at or before *target*, or None if none exists."""
    idx = bisect_right(dates_sorted, target) - 1
    if idx < 0:
        return None
    return values[idx]


def _event_keyed_value(
    dates_sorted: list[date],
    values: list[float],
    target: date,
) -> float | None:
    """Return the value at exactly *target*, or None if no observation on that day."""
    idx = bisect_right(dates_sorted, target) - 1
    if idx < 0 or dates_sorted[idx] != target:
        return None
    return values[idx]


def build_pairs(
    history: DrawHistory,
    signal: SignalSeries,
    metric_values: tuple[float, ...],
    *,
    policy: AlignmentPolicyName,
    lag_draws: int,
) -> tuple[tuple[float, ...], tuple[float, ...], AlignmentReport]:
    """Return `(signal_values, metric_values, alignment_report)` after alignment.

    The returned tuples are the paired samples that survived alignment and lag.
    """
    if len(metric_values) != len(history):
        raise ValueError(
            f"metric_values has {len(metric_values)} entries; history has {len(history)} draws"
        )
    lookup = {
        "forward_fill": _forward_fill_value,
        "event_keyed": _event_keyed_value,
    }
    try:
        resolver = lookup[policy]
    except KeyError as exc:
        raise ValueError(f"unknown alignment policy '{policy}'") from exc

    dates_sorted = [p.date for p in signal.points]
    values_sorted = [p.value for p in signal.points]

    paired_signal: list[float] = []
    paired_metric: list[float] = []
    total = len(history)

    for i, record in enumerate(history.records):
        j = i + lag_draws
        if j < 0 or j >= total:
            continue
        aligned = resolver(dates_sorted, values_sorted, record.iso_date)
        if aligned is None:
            continue
        paired_signal.append(aligned)
        paired_metric.append(metric_values[j])

    report = AlignmentReport(policy=policy, lag_draws=lag_draws)
    return tuple(paired_signal), tuple(paired_metric), report
