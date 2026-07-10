from typing import Any, Dict, List, Optional

from shared.schemas.simulation_state import SimulationState


def analyze_world(
    world: SimulationState,
    agents: List[Any],
    policies: List[Any],
) -> Dict[str, Any]:
    indicators: Dict[str, Any] = {}
    indicators['famine_risk'] = world.food_availability < 0.4
    indicators['crime_wave'] = world.crime_rate > 0.3
    indicators['protest_risk'] = world.protest_intensity > 0.3

    rich_wealth = 0.0
    poor_wealth = 0.0
    wealth_dist = getattr(world, 'economy', None)
    if wealth_dist is not None:
        wd = wealth_dist.wealth_distribution if hasattr(wealth_dist, 'wealth_distribution') else {}
        if wd:
            rich_wealth = wd.get('rich', wd.get('high', 0.0))
            poor_wealth = wd.get('poor', wd.get('low', 0.0))

    if rich_wealth > 0 and poor_wealth > 0:
        indicators['inequality_gap'] = rich_wealth / poor_wealth
    else:
        indicators['inequality_gap'] = 1.0

    indicators['unemployment_crisis'] = world.unemployment_rate > 0.25
    avg_morality = getattr(world, 'morality', 0.5)
    indicators['morality_crisis'] = avg_morality < 0.3

    return indicators


def generate_suggestions(
    analysis: Dict[str, Any],
    world: SimulationState,
    rng: Any,
    ai_router: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    if ai_router is not None and hasattr(ai_router, 'is_available') and ai_router.is_available():
        try:
            policies = getattr(world, 'active_policy_ids', [])
            advisory = ai_router.governance_advisory(world, policies)
            return [
                {
                    'action': 'ai_advisory',
                    'policy_description': advisory.get('recommendation', ''),
                    'priority': 0.85,
                    'assessment': advisory.get('assessment', ''),
                    'watch_items': advisory.get('watch_items', []),
                }
            ]
        except Exception:
            pass

    suggestions = []
    if analysis.get('famine_risk'):
        suggestions.append({'action': 'subsidize_food', 'policy_description': 'Increase food subsidies by 20%', 'priority': 0.9})
    if analysis.get('crime_wave'):
        suggestions.append({'action': 'increase_policing', 'policy_description': 'Increase public order spending by 15%', 'priority': 0.8})
    if analysis.get('protest_risk'):
        suggestions.append({'action': 'increase_welfare', 'policy_description': 'Increase welfare by 5 money', 'priority': 0.7})
    if isinstance(analysis.get('inequality_gap'), (int, float)) and analysis['inequality_gap'] > 2.0:
        suggestions.append({'action': 'progressive_tax', 'policy_description': 'Raise tax on rich, lower on poor', 'priority': 0.6})
    if analysis.get('unemployment_crisis'):
        suggestions.append({'action': 'job_creation', 'policy_description': 'Government job creation program', 'priority': 0.75})

    return suggestions


def prioritize_suggestions(
    suggestions: List[Dict[str, Any]],
    world: SimulationState,
) -> List[Dict[str, Any]]:
    sorted_suggestions = sorted(suggestions, key=lambda x: x.get('priority', 0.0), reverse=True)
    return sorted_suggestions[:5]
