"""Unit tests for simulation.policies.policy_fallback.

Tests the deterministic keyword-matching fallback for policy translation,
covering all keywords, category detection, determinism, and edge cases.
"""

import pytest

from shared.types.enums import PolicyCategory, WealthClass
from shared.types.aliases import PolicyId
from shared.schemas.policy import GovernmentPolicy
from simulation.policies.policy_fallback import (
    FALLBACK_KEYWORD_POLICIES,
    translate_policy_fallback,
)


class TestTranslatePolicyFallback:
    """Tests for the translate_policy_fallback function."""

    # ------------------------------------------------------------------
    # Individual keyword matches — delta values
    # ------------------------------------------------------------------

    def test_tax_increase(self):
        """Tax increase → poor money_delta=-2, rich money_delta=-50."""
        result = translate_policy_fallback(
            "implement a tax increase of 10%", PolicyId("test-tax-inc")
        )
        assert result.impact_deltas[WealthClass.POOR].money_delta == -2.0
        assert result.impact_deltas[WealthClass.RICH].money_delta == -50.0

    def test_tax_cut(self):
        """Tax cut → poor money_delta=+2, rich money_delta=+50."""
        result = translate_policy_fallback(
            "implement a tax cut for everyone", PolicyId("test-tax-cut")
        )
        assert result.impact_deltas[WealthClass.POOR].money_delta == 2.0
        assert result.impact_deltas[WealthClass.RICH].money_delta == 50.0

    def test_welfare(self):
        """Welfare → poor money_delta=+8, safety_delta=+0.05."""
        result = translate_policy_fallback(
            "introduce welfare program", PolicyId("test-welfare")
        )
        assert result.impact_deltas[WealthClass.POOR].money_delta == 8.0
        assert result.impact_deltas[WealthClass.POOR].safety_delta == 0.05

    def test_food_subsidy(self):
        """Food subsidy → poor food_delta=+0.10."""
        result = translate_policy_fallback(
            "food subsidy for poor", PolicyId("test-food")
        )
        assert result.impact_deltas[WealthClass.POOR].food_delta == 0.10

    def test_police(self):
        """Police → poor safety_delta=+0.10."""
        result = translate_policy_fallback(
            "more police funding", PolicyId("test-police")
        )
        assert result.impact_deltas[WealthClass.POOR].safety_delta == 0.10

    def test_education(self):
        """Education → poor money_delta=+5."""
        result = translate_policy_fallback(
            "fund education", PolicyId("test-edu")
        )
        assert result.impact_deltas[WealthClass.POOR].money_delta == 5.0

    def test_housing(self):
        """Housing → poor safety_delta=+0.08."""
        result = translate_policy_fallback(
            "build housing", PolicyId("test-housing")
        )
        assert result.impact_deltas[WealthClass.POOR].safety_delta == 0.08

    def test_minimum_wage(self):
        """Minimum wage → poor money_delta=+5."""
        result = translate_policy_fallback(
            "raise minimum wage", PolicyId("test-min-wage")
        )
        assert result.impact_deltas[WealthClass.POOR].money_delta == 5.0

    # ------------------------------------------------------------------
    # No-match / edge cases
    # ------------------------------------------------------------------

    def test_no_match(self):
        """No keyword matched → neutral policy with no deltas."""
        result = translate_policy_fallback(
            "fly to mars", PolicyId("test-no-match")
        )
        assert result.impact_deltas == {}

    # ------------------------------------------------------------------
    # Category detection
    # ------------------------------------------------------------------

    def test_category_detection_economic(self):
        """Tax policy → ECONOMIC category."""
        result = translate_policy_fallback(
            "increase tax", PolicyId("test-cat-econ")
        )
        assert result.policy.category == PolicyCategory.ECONOMIC

    def test_category_detection_social(self):
        """Welfare policy → SOCIAL category."""
        result = translate_policy_fallback(
            "welfare program", PolicyId("test-cat-social")
        )
        assert result.policy.category == PolicyCategory.SOCIAL

    def test_category_detection_public_order(self):
        """Police policy → PUBLIC_ORDER category."""
        result = translate_policy_fallback(
            "police funding", PolicyId("test-cat-order")
        )
        assert result.policy.category == PolicyCategory.PUBLIC_ORDER

    def test_category_detection_education(self):
        """Education policy → EDUCATION category."""
        result = translate_policy_fallback(
            "education reform", PolicyId("test-cat-edu")
        )
        assert result.policy.category == PolicyCategory.EDUCATION

    # ------------------------------------------------------------------
    # Weight assertions
    # ------------------------------------------------------------------

    def test_weights_applied(self):
        """Tax increase → economic_freedom=-0.3, public_order=0.1."""
        result = translate_policy_fallback(
            "tax increase", PolicyId("test-weights")
        )
        assert result.policy.weights.economic_freedom == -0.3
        assert result.policy.weights.public_order == 0.1

    # ------------------------------------------------------------------
    # Policy identity
    # ------------------------------------------------------------------

    def test_policy_id_preserved(self):
        """Policy ID passed through to the result."""
        pid = PolicyId("my-unique-policy-42")
        result = translate_policy_fallback("police funding", pid)
        assert result.policy.id == pid

    # ------------------------------------------------------------------
    # Longest-match wins
    # ------------------------------------------------------------------

    def test_multiple_keywords(self):
        """"tax increase and welfare" → longest match "tax increase" (12 chars) wins."""
        result = translate_policy_fallback(
            "tax increase and welfare", PolicyId("test-multi")
        )
        # "tax increase" (12 chars) is longer than "welfare" (7 chars)
        # Should use tax increase weights: economic_freedom=-0.3, public_order=0.1
        assert result.policy.weights.economic_freedom == -0.3
        assert result.policy.weights.public_order == 0.1
        # Tax increase deltas: poor money=-2
        assert result.impact_deltas[WealthClass.POOR].money_delta == -2.0
        # Category is based on full text: "welfare" in text → SOCIAL
        assert result.policy.category == PolicyCategory.SOCIAL

    # ------------------------------------------------------------------
    # Case insensitivity
    # ------------------------------------------------------------------

    def test_case_insensitive(self):
        """Uppercase input "TAX INCREASE" matches "tax increase"."""
        result = translate_policy_fallback(
            "TAX INCREASE", PolicyId("test-case")
        )
        assert result.impact_deltas[WealthClass.POOR].money_delta == -2.0
        assert result.policy.weights.economic_freedom == -0.3

    # ------------------------------------------------------------------
    # Determinism
    # ------------------------------------------------------------------

    def test_deterministic(self):
        """Same input twice → identical output."""
        text = "fund education for all children"
        pid = PolicyId("test-det")
        result_a = translate_policy_fallback(text, pid)
        result_b = translate_policy_fallback(text, pid)

        assert result_a.policy.weights == result_b.policy.weights
        assert result_a.impact_deltas == result_b.impact_deltas
        assert result_a.policy.category == result_b.policy.category
        assert result_a.policy.name == result_b.policy.name

    # ------------------------------------------------------------------
    # Safety: truncation
    # ------------------------------------------------------------------

    def test_name_truncated_to_50_chars(self):
        """Policy name is truncated to 50 characters."""
        long_text = "a" * 100
        result = translate_policy_fallback(long_text, PolicyId("test-trunc"))
        assert len(result.policy.name) == 50
        assert result.policy.name == "a" * 50
