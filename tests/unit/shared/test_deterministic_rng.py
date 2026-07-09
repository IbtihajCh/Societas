"""Tests for shared/utilities/deterministic_rng.py — verify new methods and determinism."""

import pytest

from shared.utilities.deterministic_rng import DeterministicRNG


class TestBeta:
    def test_returns_value_in_range(self) -> None:
        rng = DeterministicRNG(seed=42)
        for _ in range(100):
            val = rng.beta(2, 2)
            assert 0.0 <= val <= 1.0

    def test_deterministic(self) -> None:
        rng1 = DeterministicRNG(seed=42)
        rng2 = DeterministicRNG(seed=42)
        for _ in range(10):
            assert rng1.beta(2, 2) == rng2.beta(2, 2)

    def test_skewed_distribution(self) -> None:
        rng = DeterministicRNG(seed=42)
        values = [rng.beta(2, 5) for _ in range(1000)]
        mean = sum(values) / len(values)
        # Beta(2,5) has mean ~0.286, should be less than 0.5
        assert mean < 0.5


class TestWeightedChoice:
    def test_basic_choice(self) -> None:
        rng = DeterministicRNG(seed=42)
        items = ["a", "b", "c"]
        weights = [0.1, 0.8, 0.1]
        result = rng.weighted_choice(items, weights)
        assert result in items

    def test_deterministic(self) -> None:
        rng1 = DeterministicRNG(seed=42)
        rng2 = DeterministicRNG(seed=42)
        items = ["a", "b", "c"]
        weights = [0.2, 0.5, 0.3]
        for _ in range(10):
            assert rng1.weighted_choice(items, weights) == rng2.weighted_choice(items, weights)

    def test_heavy_weight_dominates(self) -> None:
        rng = DeterministicRNG(seed=42)
        items = ["rare", "common"]
        weights = [0.01, 0.99]
        counts = {"rare": 0, "common": 0}
        for _ in range(1000):
            result = rng.weighted_choice(items, weights)
            counts[result] += 1
        assert counts["common"] > counts["rare"] * 10

    def test_mismatched_lengths_raises(self) -> None:
        rng = DeterministicRNG(seed=42)
        with pytest.raises(ValueError, match="must match"):
            rng.weighted_choice(["a", "b"], [1.0])

    def test_empty_list_raises(self) -> None:
        rng = DeterministicRNG(seed=42)
        with pytest.raises(ValueError, match="empty"):
            rng.weighted_choice([], [])

    def test_zero_weights_raises(self) -> None:
        rng = DeterministicRNG(seed=42)
        with pytest.raises(ValueError, match="positive"):
            rng.weighted_choice(["a", "b"], [0.0, 0.0])


class TestIntegers:
    def test_single_value(self) -> None:
        rng = DeterministicRNG(seed=42)
        val = rng.integers(0, 10)
        assert isinstance(val, int)
        assert 0 <= val < 10

    def test_range_only(self) -> None:
        rng = DeterministicRNG(seed=42)
        val = rng.integers(5)
        assert isinstance(val, int)
        assert 0 <= val < 5

    def test_multiple_values(self) -> None:
        rng = DeterministicRNG(seed=42)
        vals = rng.integers(0, 100, size=5)
        assert isinstance(vals, list)
        assert len(vals) == 5
        for v in vals:
            assert 0 <= v < 100

    def test_deterministic(self) -> None:
        rng1 = DeterministicRNG(seed=42)
        rng2 = DeterministicRNG(seed=42)
        for _ in range(10):
            assert rng1.integers(0, 100) == rng2.integers(0, 100)


class TestDeterminism:
    def test_same_seed_same_sequence(self) -> None:
        rng1 = DeterministicRNG(seed=123)
        rng2 = DeterministicRNG(seed=123)
        for _ in range(50):
            assert rng1.random() == rng2.random()

    def test_reset_restores_sequence(self) -> None:
        rng = DeterministicRNG(seed=42)
        first = [rng.random() for _ in range(10)]
        rng.reset()
        second = [rng.random() for _ in range(10)]
        assert first == second

    def test_different_seeds_different_sequence(self) -> None:
        rng1 = DeterministicRNG(seed=1)
        rng2 = DeterministicRNG(seed=2)
        vals1 = [rng1.random() for _ in range(10)]
        vals2 = [rng2.random() for _ in range(10)]
        assert vals1 != vals2
