"""Draw-derived metrics exposed to the correlation layer.

A metric is a function of the history that returns one value per draw, in
chronological order. v1 catalog:

- ``sum`` (continuous) — `sum(numbers_sorted)`.
- ``even_count`` (continuous) — count of even numbers per draw.
- ``number_present`` (binary) — 1 if `params["number"]` appears, else 0.

New metrics must be deterministic, side-effect free, and declare their kind.
"""

from __future__ import annotations

from collections.abc import Callable

from service.correlation.models import MetricKind, MetricSpec
from service.ingestion import DrawHistory

MetricParams = dict[str, int | float | str]
MetricFn = Callable[[DrawHistory, MetricParams], tuple[float, ...]]


def _metric_sum(history: DrawHistory, _params: MetricParams) -> tuple[float, ...]:
    return tuple(float(sum(r.numbers_sorted)) for r in history.records)


def _metric_even_count(history: DrawHistory, _params: MetricParams) -> tuple[float, ...]:
    return tuple(float(sum(1 for n in r.numbers_sorted if n % 2 == 0)) for r in history.records)


def _metric_number_present(history: DrawHistory, params: MetricParams) -> tuple[float, ...]:
    number = params.get("number")
    if not isinstance(number, int) or number < 1 or number > 25:
        raise ValueError(
            f"metric 'number_present' requires params['number'] in [1,25], got {number!r}"
        )
    return tuple(float(number in r.numbers_sorted) for r in history.records)


METRIC_CATALOG: dict[str, tuple[MetricKind, MetricFn]] = {
    "sum": ("continuous", _metric_sum),
    "even_count": ("continuous", _metric_even_count),
    "number_present": ("binary", _metric_number_present),
}


def resolve_metric(history: DrawHistory, spec: MetricSpec) -> tuple[float, ...]:
    """Compute the metric values over *history* in chronological order.

    Raises ``ValueError`` for unknown metrics or metrics whose declared kind
    disagrees with the catalog entry — the catalog is authoritative, but
    requiring agreement makes programming mistakes loud.
    """
    if spec.name not in METRIC_CATALOG:
        raise ValueError(f"unknown metric '{spec.name}'. Available: {sorted(METRIC_CATALOG)}")
    kind, fn = METRIC_CATALOG[spec.name]
    if spec.kind != kind:
        raise ValueError(f"metric '{spec.name}' kind is {kind}; caller declared {spec.kind}")
    return fn(history, dict(spec.params))
