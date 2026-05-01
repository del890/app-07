"""Unit tests for the dream-oracle symbolic catalog."""

from __future__ import annotations

from service.oracle.catalog import CATALOG, CATALOG_VERSION, BiasRule, lookup


def test_catalog_version_is_nonempty_string() -> None:
    assert isinstance(CATALOG_VERSION, str)
    assert len(CATALOG_VERSION) > 0


def test_lookup_known_element_water() -> None:
    rule = lookup("element", "water")
    assert rule is not None
    assert isinstance(rule, BiasRule)
    assert rule.numbers == list(range(1, 8))
    assert rule.multiplier > 0
    assert len(rule.rationale) > 0


def test_lookup_known_element_fire() -> None:
    rule = lookup("element", "fire")
    assert rule is not None
    assert rule.numbers == list(range(19, 26))


def test_lookup_known_color_blue() -> None:
    rule = lookup("color", "blue")
    assert rule is not None
    assert rule.numbers == list(range(21, 26))


def test_lookup_known_emotion_joy() -> None:
    rule = lookup("emotion", "joy")
    assert rule is not None
    # joy maps to even numbers
    assert all(n % 2 == 0 for n in rule.numbers)


def test_lookup_known_emotion_rage() -> None:
    rule = lookup("emotion", "rage")
    assert rule is not None
    # rage maps to primes
    primes = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    assert set(rule.numbers) == primes


def test_lookup_known_archetype_falling() -> None:
    rule = lookup("archetype", "falling")
    assert rule is not None
    assert rule.numbers == list(range(21, 26))


def test_lookup_count_seven() -> None:
    rule = lookup("count", "7")
    assert rule is not None
    assert rule.numbers == [7]
    assert rule.multiplier >= 4.0


def test_lookup_count_all_integers_1_to_25() -> None:
    for n in range(1, 26):
        rule = lookup("count", str(n))
        assert rule is not None, f"count/{n} missing from catalog"
        assert rule.numbers == [n]


def test_lookup_unknown_returns_none() -> None:
    assert lookup("unknown_category", "unknown_label") is None
    assert lookup("element", "plasma") is None
    assert lookup("color", "purple") is None


def test_lookup_is_case_insensitive() -> None:
    rule_lower = lookup("element", "water")
    rule_upper = lookup("ELEMENT", "WATER")
    rule_mixed = lookup("Element", "Water")
    assert rule_lower is not None
    assert rule_lower == rule_upper
    assert rule_lower == rule_mixed


def test_all_catalog_numbers_in_range() -> None:
    for (cat, label), rule in CATALOG.items():
        for n in rule.numbers:
            assert 1 <= n <= 25, f"({cat}, {label}) has out-of-range number {n}"
