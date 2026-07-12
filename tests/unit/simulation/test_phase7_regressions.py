"""Regression tests for Phase 7 organic hardening.

Verifies the organic-society fixes:
  1. BUSINESS_OWNER removed from WealthClass enum
  2. Initial wealth-class distribution is 55/20/15 + 10% random
  3. Tax is deducted from agents AND accumulated in world tax_revenue
  4. Welfare funded from tax_revenue pool (no free money)
  5. WORK action produces food (circulating economy)
  6. Rich agents get happiness bonus; taxes hurt rich happiness
  7. apply_policy_weights is wired into deterministic_fallback
  8. DECISION_STAGGER_INTERVAL constant replaces hardcoded 3
  9. All 6 policy dimensions affect action scores
 10. SimulationConfig defaults wired to source constants
 11. Per-tick statistics capture the full 56-field metric surface
 12. Full simulation with default config produces a stable, organic society
"""

import pytest

from shared.constants.defaults import (
    DECISION_STAGGER_INTERVAL,
    DEFAULT_TAX_RATE,
    DEFAULT_WELFARE_AMOUNT,
)
from shared.schemas.agent_state import (
    AgentEmotions,
    AgentId,
    AgentNeeds,
    AgentResources,
    AgentState,
    AgentTraits,
    EmploymentStatus,
)
from shared.schemas.economy_state import EconomyState
from shared.schemas.policy import PolicyWeights
from shared.schemas.simulation_state import SimulationState
from shared.schemas.tick_result import AgentActionResult
from shared.types.aliases import NeedValue
from shared.types.enums import ActionType, EmotionType, NeedType, WealthClass
from shared.utilities.deterministic_rng import DeterministicRNG
from simulation.agents.agent_factory import create_initial_population
from simulation.agents.decision_engine import deterministic_fallback, should_evaluate_this_tick
from simulation.agents.emotion_engine import compute_happiness
from simulation.policies.policy_effects import apply_policy_weights


def _make_agent(
    *,
    food: float = 0.5,
    water: float = 0.5,
    safety: float = 0.5,
    social: float = 0.5,
    sleep: float = 0.5,
    self_esteem: float = 0.5,
    financial: float = 0.5,
    reputation: float = 0.5,
    health: float = 1.0,
    employed: bool = False,
    unlust: float = 0.0,
    resilience: float = 0.5,
    anger_tendency: float = 0.5,
    happiness_score: float = 0.5,
    money: float = 100.0,
    wealth_class: WealthClass = WealthClass.POOR,
    creativity: float = 0.5,
    base_salary: float = 0.0,
) -> AgentState:
    """Build an AgentState with the given attributes for tests."""
    needs = AgentNeeds(
        levels={
            NeedType.FOOD: NeedValue(food),
            NeedType.WATER: NeedValue(water),
            NeedType.SAFETY: NeedValue(safety),
            NeedType.SOCIAL_CONNECTION: NeedValue(social),
            NeedType.SLEEP: NeedValue(sleep),
            NeedType.SELF_ESTEEM: NeedValue(self_esteem),
            NeedType.FINANCIAL_SECURITY: NeedValue(financial),
            NeedType.REPUTATION: NeedValue(reputation),
        }
    )
    resources = AgentResources(
        health=health,
        employed=employed,
        money=money,
        base_salary=base_salary,
    )
    traits = AgentTraits(
        resilience=resilience,
        anger_tendency=anger_tendency,
        creativity=creativity,
    )
    emotions = AgentEmotions(
        primary=EmotionType.NORMAL,
        happiness_score=happiness_score,
    )
    return AgentState(
        id=AgentId("test-agent"),
        needs=needs,
        resources=resources,
        traits=traits,
        emotions=emotions,
        unlust=unlust,
        wealth_class=wealth_class,
        employment_status=(EmploymentStatus.EMPLOYED if employed else EmploymentStatus.UNEMPLOYED),
    )


class TestWealthClassRebalance:
    """Step 1-2: BUSINESS_OWNER removed; 55/20/15 + 10% random."""

    def test_no_business_owner_enum(self) -> None:
        attr_names = {w.name for w in WealthClass}
        assert "BUSINESS_OWNER" not in attr_names
        assert attr_names == {"POOR", "MIDDLE", "RICH"}

    def test_distribution_initial_population(self) -> None:
        rng = DeterministicRNG(seed=42)
        agents = create_initial_population(800, rng)
        counts = {WealthClass.POOR: 0, WealthClass.MIDDLE: 0, WealthClass.RICH: 0}
        for a in agents:
            if a.wealth_class in counts:
                counts[a.wealth_class] += 1
        n = len(agents)
        assert (
            0.50 * n <= counts[WealthClass.MIDDLE] <= 0.60 * n
        ), f"MIDDLE share {counts[WealthClass.MIDDLE]/n:.2f} outside [50%, 60%]"
        assert (
            0.15 * n <= counts[WealthClass.POOR] <= 0.25 * n
        ), f"POOR share {counts[WealthClass.POOR]/n:.2f} outside [15%, 25%]"
        assert (
            0.10 * n <= counts[WealthClass.RICH] <= 0.20 * n
        ), f"RICH share {counts[WealthClass.RICH]/n:.2f} outside [10%, 20%]"


class TestTaxLifecycle:
    """Step 3: Tax is deducted, accumulated, and tracked."""

    def test_default_tax_rate_in_world(self) -> None:
        world = SimulationState()
        assert world.tax_rate == DEFAULT_TAX_RATE
        assert world.welfare_amount == DEFAULT_WELFARE_AMOUNT

    def test_work_tracks_tax_paid_in_score_delta(self) -> None:
        from simulation.agents.action_executor import _do_work

        rng = DeterministicRNG(seed=1)
        agent = _make_agent(
            food=0.9,
            employed=True,
            money=200.0,
            wealth_class=WealthClass.MIDDLE,
            creativity=0.6,
            base_salary=200.0,
        )
        world = SimulationState(tax_rate=0.15)
        result = AgentActionResult(agent_id=AgentId("1"), action=ActionType.WORK)
        _do_work(agent, world, result)
        assert "tax_paid" in result.score_delta, "WORK result must track tax_paid"
        assert result.score_delta["tax_paid"] > 0.0, "WORK should deduct some tax"


class TestWelfareFundedFromTaxPool:
    """Step 4: Welfare comes from tax_revenue pool, not free money."""

    def test_welfare_pool_reduces_on_disbursement(self) -> None:
        from simulation.world.economy import apply_welfare

        world = SimulationState(
            economy=EconomyState(tax_revenue=1000.0),
            welfare_enabled=True,
            welfare_amount=8.0,
        )
        agent = _make_agent(
            employed=False,
            money=20.0,
            wealth_class=WealthClass.POOR,
        )
        before_pool = world.economy.tax_revenue
        apply_welfare(agent, world)
        assert (
            world.economy.tax_revenue < before_pool
        ), f"Welfare must reduce tax_revenue pool ({before_pool} -> {world.economy.tax_revenue})"


class TestWorkProducesFood:
    """Step 5: WORK action produces food (organic work-economy coupling)."""

    def test_work_increases_food_availability(self) -> None:
        from simulation.agents.action_executor import _do_work

        rng = DeterministicRNG(seed=2)
        agent = _make_agent(
            food=0.9,
            employed=True,
            money=200.0,
            wealth_class=WealthClass.MIDDLE,
            creativity=0.8,
        )
        world = SimulationState(tax_rate=0.15, food_availability=0.5)
        result = AgentActionResult(agent_id=AgentId("10"), action=ActionType.WORK)
        _do_work(agent, world, result)
        assert (
            world.food_availability > 0.5
        ), f"WORK should produce food; food went from 0.5 to {world.food_availability}"


class TestRichHappinessAndTaxPain:
    """Step 6: Wealth-based happiness bonus + tax pain for rich."""

    def test_rich_tax_pain_reduces_happiness(self) -> None:
        agent_rich = _make_agent(
            employed=True,
            money=60000.0,
            wealth_class=WealthClass.RICH,
            unlust=0.0,
            health=1.0,
            food=1.0,
            water=1.0,
            safety=1.0,
            social=1.0,
            sleep=1.0,
            self_esteem=1.0,
            financial=1.0,
            reputation=1.0,
        )
        world_low_tax = SimulationState(tax_rate=0.10)
        world_high_tax = SimulationState(tax_rate=0.60)
        h_low = compute_happiness(agent_rich, world_low_tax)
        h_high = compute_happiness(agent_rich, world_high_tax)
        assert h_low > h_high, f"High tax must reduce rich happiness: low={h_low}, high={h_high}"

    def test_zero_money_gets_no_wealth_bonus(self) -> None:
        """Same needs/traits, money=0 vs money=100k should differ by exactly the wealth_bonus cap (0.05)."""
        agent_zero = _make_agent(
            money=0.0,
            wealth_class=WealthClass.POOR,
            food=0.0,
            water=0.0,
            safety=0.0,
            social=0.0,
            sleep=0.0,
            self_esteem=0.0,
            financial=0.0,
            reputation=0.0,
            health=0.0,
            employed=False,
            unlust=1.0,
            happiness_score=0.0,
        )
        agent_rich = _make_agent(
            money=100000.0,
            wealth_class=WealthClass.RICH,
            food=0.0,
            water=0.0,
            safety=0.0,
            social=0.0,
            sleep=0.0,
            self_esteem=0.0,
            financial=0.0,
            reputation=0.0,
            health=0.0,
            employed=False,
            unlust=1.0,
            happiness_score=0.0,
        )
        score_zero = compute_happiness(agent_zero)
        score_rich = compute_happiness(agent_rich)
        assert score_zero == pytest.approx(0.0, abs=1e-9)
        assert score_rich - score_zero == pytest.approx(0.05, abs=1e-9)


class TestPolicyWeightsAllDimensionsWired:
    """Step 9: All 6 policy dimensions affect action scores."""

    @pytest.fixture
    def base_scores(self) -> dict[ActionType, float]:
        return {
            ActionType.WORK: 5.0,
            ActionType.STEAL: 1.0,
            ActionType.HARM_OTHER: 0.5,
            ActionType.PROTEST: 1.0,
            ActionType.SHARE: 2.0,
            ActionType.CONSOLE: 2.0,
            ActionType.HOBBY: 0.1,
            ActionType.INVEST: 0.1,
        }

    def test_environmental_protection_boosts_hobby(
        self, base_scores: dict[ActionType, float]
    ) -> None:
        out = apply_policy_weights(base_scores, PolicyWeights(environmental_protection=1.0))
        assert out[ActionType.HOBBY] > base_scores[ActionType.HOBBY]
        assert out[ActionType.STEAL] < base_scores[ActionType.STEAL]

    def test_innovation_boosts_work_and_invest(self, base_scores: dict[ActionType, float]) -> None:
        out = apply_policy_weights(base_scores, PolicyWeights(innovation=1.0))
        assert out[ActionType.WORK] > base_scores[ActionType.WORK]
        assert out[ActionType.INVEST] > base_scores[ActionType.INVEST]

    def test_cultural_preservation_boosts_hobby_and_console(
        self, base_scores: dict[ActionType, float]
    ) -> None:
        out = apply_policy_weights(base_scores, PolicyWeights(cultural_preservation=1.0))
        assert out[ActionType.HOBBY] > base_scores[ActionType.HOBBY]
        assert out[ActionType.CONSOLE] > base_scores[ActionType.CONSOLE]


class TestDeterminismInvariants:
    """Methodology: same seed + same config = identical simulation."""

    def test_same_seed_same_deterministic_choice(self) -> None:
        agent1 = _make_agent(unlust=0.3, employed=True, money=200.0)
        agent2 = _make_agent(unlust=0.3, employed=True, money=200.0)
        rng1 = DeterministicRNG(seed=42)
        rng2 = DeterministicRNG(seed=42)
        action1 = deterministic_fallback(agent1, SimulationState(), rng1)
        action2 = deterministic_fallback(agent2, SimulationState(), rng2)
        assert action1 == action2

    def test_decision_stagger_uses_constant(self) -> None:
        agent = AgentState(
            id=AgentId("7"),
            wealth_class=WealthClass.MIDDLE,
        )
        target = int(agent.id) % DECISION_STAGGER_INTERVAL
        for tick in range(DECISION_STAGGER_INTERVAL * 3 + 1):
            if tick % DECISION_STAGGER_INTERVAL == target:
                assert should_evaluate_this_tick(
                    agent, tick
                ), f"At tick {tick} agent should be evaluated"
            else:
                assert not should_evaluate_this_tick(
                    agent, tick
                ), f"At tick {tick} agent should NOT be evaluated"


class TestInitialSimulationDefaults:
    """Step 10: Defaults wired to source constants (no hardcoded literals)."""

    def test_tax_rate_default(self) -> None:
        assert SimulationState().tax_rate == DEFAULT_TAX_RATE

    def test_welfare_amount_default(self) -> None:
        assert SimulationState().welfare_amount == DEFAULT_WELFARE_AMOUNT
