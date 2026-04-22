"""PI-alignment analysis.

Every result cites the rule used, the PI digits consulted, and a plain-language
explanation of the computation. Rules are deterministic and reproducible — the
same (dataset_hash, rule, target) tuple always yields the same score.

v1 rule catalog
---------------

- ``digit_sum_mod10``
    Compare ``sum(draw.numbers_sorted) mod 10`` against the sum of the first
    15 digits of PI mod 10. Score in {0.0, 1.0}: 1.0 on match, 0.0 otherwise.

- ``position_digit_match``
    For a draw of 15 numbers, score is the fraction of positions where the
    number's ones-digit (``n mod 10``) equals the PI digit at the same
    position. Score in [0.0, 1.0].

Add rules by appending to ``RULES`` and writing a handler. Rules *must* be
deterministic and side-effect-free.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from service.ingestion import DrawHistory, DrawRecord
from service.statistics.base import StatMeta, make_meta

# First 20 digits of PI after the decimal point (enough for NUMBERS_PER_DRAW + headroom).
PI_DIGITS = (1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3, 2, 3, 8, 4, 6)
NUMBERS_PER_DRAW = 15


class PiAlignmentResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    meta: StatMeta
    rule: str
    rule_description: str
    pi_digits_used: str = Field(description="The PI digits consulted, as a string.")
    target: str = Field(description="Human-readable target descriptor.")
    score: float = Field(ge=0.0, le=1.0)
    explanation: str


@dataclass(frozen=True)
class PiRule:
    name: str
    description: str
    pi_digits: tuple[int, ...]
    handler: Callable[[DrawRecord], tuple[float, str]]


def _rule_digit_sum_mod10(record: DrawRecord) -> tuple[float, str]:
    draw_sum = sum(record.numbers_sorted)
    draw_mod = draw_sum % 10
    pi_mod = sum(PI_DIGITS[:NUMBERS_PER_DRAW]) % 10
    score = 1.0 if draw_mod == pi_mod else 0.0
    explanation = (
        f"sum(draw)={draw_sum}, draw_sum mod 10 = {draw_mod}; "
        f"sum(PI digits[0:{NUMBERS_PER_DRAW}]) mod 10 = {pi_mod}. "
        f"score = 1.0 on match, else 0.0 → {score}."
    )
    return score, explanation


def _rule_position_digit_match(record: DrawRecord) -> tuple[float, str]:
    matches = 0
    details: list[str] = []
    for i, n in enumerate(record.numbers_sorted):
        pi_d = PI_DIGITS[i]
        if n % 10 == pi_d:
            matches += 1
            details.append(f"pos {i}: number {n} % 10 == PI digit {pi_d} ✓")
    score = matches / NUMBERS_PER_DRAW
    explanation = (
        f"{matches}/{NUMBERS_PER_DRAW} positions match. "
        f"Matches: {'; '.join(details) if details else 'none'}."
    )
    return score, explanation


RULES: dict[str, PiRule] = {
    "digit_sum_mod10": PiRule(
        name="digit_sum_mod10",
        description=(
            "Compare sum(draw.numbers_sorted) mod 10 with sum of first 15 PI "
            "digits mod 10. Binary match."
        ),
        pi_digits=PI_DIGITS[:NUMBERS_PER_DRAW],
        handler=_rule_digit_sum_mod10,
    ),
    "position_digit_match": PiRule(
        name="position_digit_match",
        description=(
            "Fraction of positions where the sorted-ascending draw number's "
            "ones-digit equals the PI digit at that position."
        ),
        pi_digits=PI_DIGITS[:NUMBERS_PER_DRAW],
        handler=_rule_position_digit_match,
    ),
}


def compute_pi_alignment(
    history: DrawHistory,
    *,
    rule: str,
    target_original_id: int,
) -> PiAlignmentResult:
    """Evaluate *rule* against the draw identified by its upstream id."""
    if rule not in RULES:
        raise ValueError(f"unknown PI rule '{rule}'. Available: {sorted(RULES)}")
    pi_rule = RULES[rule]
    try:
        record = history.by_original_id(target_original_id)
    except KeyError as exc:
        raise ValueError(f"draw with original_id={target_original_id} not found") from exc

    score, explanation = pi_rule.handler(record)
    meta = make_meta(history, descriptor="full", window_size=len(history))
    return PiAlignmentResult(
        meta=meta,
        rule=pi_rule.name,
        rule_description=pi_rule.description,
        pi_digits_used="".join(str(d) for d in pi_rule.pi_digits),
        target=f"draw:original_id={target_original_id}",
        score=score,
        explanation=explanation,
    )
