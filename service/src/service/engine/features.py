"""Feature engineering for the learned model.

Per-draw, per-number feature vector. For draw T (the *target*), features
describe the state of the history through draw T-1:

    f0: freq in last 10 draws
    f1: freq in last 50 draws
    f2: freq in last 200 draws
    f3: current gap (draws since last appearance)
    f4: normalised current gap (current_gap / mean_gap, 0 when mean_gap == 0)
    f5: appeared in the previous draw (binary)
    f6: appeared in any of the last 3 draws (binary)

The feature spec is versioned (``FEATURE_VERSION``) and carried through to the
model artifact so that mismatched (features, model) pairs are detected loudly.

Minimum prior history required to produce a row with non-degenerate features
is ``MIN_PRIOR_DRAWS``; earlier rows are skipped during training.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from service.ingestion import DrawHistory, DrawRecord

FEATURE_NAMES = (
    "freq_last_10",
    "freq_last_50",
    "freq_last_200",
    "current_gap",
    "norm_current_gap",
    "appeared_prev_draw",
    "appeared_last_3",
)
FEATURE_COUNT = len(FEATURE_NAMES)
FEATURE_VERSION = "v1"
MIN_PRIOR_DRAWS = 200  # need enough history for freq_last_200


@dataclass(frozen=True)
class NumberState:
    """Rolling state for one number during a single forward pass through history."""

    last_seen_index: int | None = None
    gaps_observed: tuple[int, ...] = ()
    last_10_hits: int = 0
    last_50_hits: int = 0
    last_200_hits: int = 0

    def mean_gap(self) -> float:
        if not self.gaps_observed:
            return 0.0
        return sum(self.gaps_observed) / len(self.gaps_observed)


def build_feature_vector(
    state: NumberState, *, t_prev_draw_index: int, last_3_hit: bool, appeared_prev: bool
) -> tuple[float, ...]:
    mean_gap = state.mean_gap()
    current_gap = (
        (t_prev_draw_index - state.last_seen_index)
        if state.last_seen_index is not None
        else t_prev_draw_index + 1
    )
    norm_gap = (current_gap / mean_gap) if mean_gap > 0 else 0.0
    return (
        float(state.last_10_hits),
        float(state.last_50_hits),
        float(state.last_200_hits),
        float(current_gap),
        float(norm_gap),
        float(appeared_prev),
        float(last_3_hit),
    )


def extract_training_matrix(
    history: DrawHistory,
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Build `(X, Y, target_indices)` for the learned model.

    - ``X`` has shape `(N_rows, 25, FEATURE_COUNT)` where ``N_rows`` is the number
      of draws that had at least ``MIN_PRIOR_DRAWS`` of history before them.
    - ``Y`` has shape `(N_rows, 25)`; `Y[i, n-1] == 1` iff number n appeared in
      the i-th target draw.
    - ``target_indices`` lists the chronological draw indices the rows correspond
      to (useful for train/cal/eval splits).

    Computed in a single forward pass over the history — O(T * 15) work.
    """
    records = history.records
    total = len(records)

    if total < MIN_PRIOR_DRAWS + 1:
        raise ValueError(
            f"history has {total} draws; need at least {MIN_PRIOR_DRAWS + 1} to produce "
            "a learned-model training matrix"
        )

    # Per-number rolling state
    last_seen: dict[int, int] = {}
    gaps_by_n: dict[int, list[int]] = {n: [] for n in range(1, 26)}
    # rolling hit counts — recomputed via deques to avoid O(N*window) rescans
    # We rebuild per target, but with moving sums it's still cheap.
    # To stay simple and fast enough at 3,656 draws, use ring buffers.

    rows_x: list[list[list[float]]] = []
    rows_y: list[list[int]] = []
    target_indices: list[int] = []

    for t in range(total):
        # If we have enough prior history, emit a feature row for this target draw.
        if t >= MIN_PRIOR_DRAWS:
            prev_index = t - 1
            prev_numbers = set(records[prev_index].numbers_sorted)
            last_3_numbers: set[int] = set()
            for j in range(max(0, t - 3), t):
                last_3_numbers.update(records[j].numbers_sorted)

            feat_for_n: list[list[float]] = []
            label_for_n: list[int] = []
            for n in range(1, 26):
                state = NumberState(
                    last_seen_index=last_seen.get(n),
                    gaps_observed=tuple(gaps_by_n[n]),
                    last_10_hits=_count_in_window(records, n, t - 10, t),
                    last_50_hits=_count_in_window(records, n, t - 50, t),
                    last_200_hits=_count_in_window(records, n, t - 200, t),
                )
                vec = build_feature_vector(
                    state,
                    t_prev_draw_index=prev_index,
                    last_3_hit=n in last_3_numbers,
                    appeared_prev=n in prev_numbers,
                )
                feat_for_n.append(list(vec))
                label_for_n.append(1 if n in records[t].numbers_sorted else 0)
            rows_x.append(feat_for_n)
            rows_y.append(label_for_n)
            target_indices.append(t)

        # Now advance state to include draw t (so draw t+1 sees it)
        for n in records[t].numbers_sorted:
            if n in last_seen:
                gaps_by_n[n].append(t - last_seen[n])
            last_seen[n] = t

    x_arr = np.asarray(rows_x, dtype=np.float64)
    y_arr = np.asarray(rows_y, dtype=np.int64)
    return x_arr, y_arr, target_indices


def extract_features_at(history: DrawHistory, *, predict_for_index: int) -> np.ndarray:
    """Return the 25×FEATURE_COUNT feature matrix describing state before draw
    ``predict_for_index``. Used at inference time; ``predict_for_index`` is the
    chronological index of the target draw.
    """
    records = history.records
    if predict_for_index < 1:
        raise ValueError("predict_for_index must be >= 1")
    if predict_for_index > len(records):
        raise ValueError(
            f"predict_for_index {predict_for_index} exceeds history length {len(records)}"
        )

    # Recompute last_seen and gaps for every number up through predict_for_index - 1.
    last_seen: dict[int, int] = {}
    gaps_by_n: dict[int, list[int]] = {n: [] for n in range(1, 26)}
    for t in range(predict_for_index):
        for n in records[t].numbers_sorted:
            if n in last_seen:
                gaps_by_n[n].append(t - last_seen[n])
            last_seen[n] = t

    prev_index = predict_for_index - 1
    prev_numbers = set(records[prev_index].numbers_sorted)
    last_3_numbers: set[int] = set()
    for j in range(max(0, predict_for_index - 3), predict_for_index):
        last_3_numbers.update(records[j].numbers_sorted)

    features = np.zeros((25, FEATURE_COUNT), dtype=np.float64)
    for n in range(1, 26):
        state = NumberState(
            last_seen_index=last_seen.get(n),
            gaps_observed=tuple(gaps_by_n[n]),
            last_10_hits=_count_in_window(records, n, predict_for_index - 10, predict_for_index),
            last_50_hits=_count_in_window(records, n, predict_for_index - 50, predict_for_index),
            last_200_hits=_count_in_window(records, n, predict_for_index - 200, predict_for_index),
        )
        vec = build_feature_vector(
            state,
            t_prev_draw_index=prev_index,
            last_3_hit=n in last_3_numbers,
            appeared_prev=n in prev_numbers,
        )
        features[n - 1] = vec
    return features


def _count_in_window(records: Sequence[DrawRecord], n: int, start: int, end: int) -> int:
    start = max(0, start)
    end = max(start, min(end, len(records)))
    count = 0
    for idx in range(start, end):
        if n in records[idx].numbers_sorted:
            count += 1
    return count
