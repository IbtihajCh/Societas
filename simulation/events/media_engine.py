"""Media engine: news generation, fake news, public sentiment, and trust dynamics."""

from dataclasses import dataclass, field
from typing import Any, Optional

from shared.schemas.agent_state import AgentState
from shared.schemas.simulation_state import SimulationState
from shared.constants.defaults import (
    MEDIA_SENSATIONALISM_BASE,
    MEDIA_TRUST_BASE,
    MEDIA_FAKE_NEWS_CHANCE,
    MEDIA_SENTIMENT_DECAY,
)


NEWS_TEMPLATES = {
    "crime_wave": "Crime rates have {direction} by {pct:.0f}%, with {count} incidents reported this month. {commentary}",
    "economic": "The economy is {state}. Unemployment {unemp_dir} to {unemp:.1f}%. {commentary}",
    "protest": "Protests {intensity} across the city as {pct:.0f}% of citizens express dissatisfaction. {commentary}",
    "env_famine": "A severe famine has struck, with food availability dropping to {avail:.0%}. {commentary}",
    "env_drought": "Water shortage continues — availability at just {avail:.0%}. {commentary}",
    "env_abundance": "Abundant harvest reported! Food availability at {avail:.0%}. {commentary}",
    "social": "Social cohesion {direction} as community bonds {verb}. {commentary}",
    "policy": "New policy: {policy_name}. {commentary}",
}


# Fake news templates — designed to manipulate
FAKE_NEWS_TEMPLATES = {
    "crime_exaggeration": "Government statistics {claim} crime has dropped, but independent reports suggest the TRUE crime rate is {exaggerated:.0f}% higher!",
    "gov_coverup": "Leaked documents reveal the government is {claim}. Citizens urged to {action}.",
    "enemy_fabrication": "Unverified sources claim that {group} is planning to {claim}. Public outrage growing.",
}


@dataclass
class NewsArticle:
    tick: int
    headline: str
    body: str
    category: str  # crime, economic, protest, environment, social, policy
    is_fake: bool
    impact: dict  # {"crime_rate": 0.02, "protest_intensity": 0.03, ...}


@dataclass
class MediaState:
    articles: list[NewsArticle] = field(default_factory=list)
    trust_in_media: float = MEDIA_TRUST_BASE  # 0.0 (no trust) to 1.0 (full trust)
    sensationalism: float = MEDIA_SENSATIONALISM_BASE  # how much articles exaggerate
    fake_news_level: float = 0.0  # how much fake news is circulating
    sentiment_gov: float = 0.0  # -1.0 (anti-gov) to 1.0 (pro-gov)
    sentiment_economy: float = 0.0  # -1.0 (pessimistic) to 1.0 (optimistic)


def generate_daily_news(world: SimulationState, tick_number: int, rng) -> list[NewsArticle]:
    """Generate news articles based on current world state.

    Produces 0-3 articles per tick based on significant events.
    """
    if tick_number % 5 != 0:
        return []

    articles: list[NewsArticle] = []

    # 1. Crime article (if crime_rate > 0.2)
    if world.crime_rate > 0.2:
        pct = world.crime_rate * 100
        direction = "rising" if world.crime_rate > 0.3 else "stable"
        count = int(50 * world.crime_rate)
        commentary = "Citizens are increasingly concerned about safety." if world.crime_rate > 0.4 else "Police urge vigilance."
        headline = f"Crime {'Surges' if direction == 'rising' else 'Remains Stable'}: {pct:.0f}% Rate"
        body = NEWS_TEMPLATES["crime_wave"].format(
            direction=direction, pct=pct, count=count, commentary=commentary,
        )
        impact = {"crime_rate": 0.01, "protest_intensity": 0.02 * world.crime_rate}
        articles.append(NewsArticle(tick_number, headline, body, "crime", False, impact))

    # 2. Economic article
    if world.unemployment_rate > 0.15:
        state = "struggling" if world.unemployment_rate > 0.20 else "stabilizing"
        unemp_dir = "rose" if world.unemployment_rate > 0.18 else "held"
        commentary = "Economists recommend policy interventions." if world.unemployment_rate > 0.25 else "Markets remain cautious."
        headline = f"Economy {state.title()}: Unemployment at {world.unemployment_rate:.0%}"
        body = NEWS_TEMPLATES["economic"].format(
            state=state, unemp_dir=unemp_dir, unemp=world.unemployment_rate * 100,
            commentary=commentary,
        )
        impact = {"unemployment_rate": 0.01}
        articles.append(NewsArticle(tick_number, headline, body, "economic", False, impact))

    # 3. Protest article
    if world.protest_intensity > 0.2:
        intensity = "intensify" if world.protest_intensity > 0.4 else "continue"
        pct = world.protest_intensity * 100
        commentary = "Authorities are monitoring the situation closely."
        headline = f"Protests {intensity.title()} as {pct:.0f}% Express Dissatisfaction"
        body = NEWS_TEMPLATES["protest"].format(
            intensity=intensity, pct=pct, commentary=commentary,
        )
        impact = {"protest_intensity": 0.03}
        articles.append(NewsArticle(tick_number, headline, body, "protest", False, impact))

    # 4. Fake news (sometimes)
    if rng.random() < MEDIA_FAKE_NEWS_CHANCE:
        fake_types = list(FAKE_NEWS_TEMPLATES.keys())
        fake_type = fake_types[rng.choice(len(fake_types))]
        if fake_type == "crime_exaggeration":
            claim = "falsely claim"
            exaggerated = world.crime_rate * 100 * (1.5 + rng.random())
            headline = f"SHOCK REPORT: True Crime Rate {exaggerated:.0f}% Higher Than Official Figures!"
            body = FAKE_NEWS_TEMPLATES["crime_exaggeration"].format(claim=claim, exaggerated=exaggerated)
            impact = {"crime_rate": 0.05, "protest_intensity": 0.04, "trust_in_govt": -0.03}
        elif fake_type == "gov_coverup":
            claim = "hiding the true extent of economic damage"
            action = "demand transparency"
            headline = "BREAKING: Government Cover-Up Exposed!"
            body = FAKE_NEWS_TEMPLATES["gov_coverup"].format(claim=claim, action=action)
            impact = {"trust_in_govt": -0.05, "protest_intensity": 0.05}
        else:
            claim = "destabilize the economy"
            group = "foreign interests"
            headline = "ALERT: Foreign Plot to Destabilize Our City!"
            body = FAKE_NEWS_TEMPLATES["enemy_fabrication"].format(group=group, claim=claim)
            impact = {"trust_in_govt": 0.02, "protest_intensity": -0.02}
        articles.append(NewsArticle(
            tick_number, headline, body, "crime" if "crime" in fake_type else "social", True, impact,
        ))

    return articles


def apply_media_effects(world: SimulationState, articles: list[NewsArticle], agents: list[AgentState]) -> None:
    """Apply news article impacts to world state and agent beliefs."""
    if not articles:
        return

    for article in articles:
        # Apply world-level impacts
        for key, value in article.impact.items():
            if hasattr(world, key):
                current = getattr(world, key)
                setattr(world, key, max(0.0, min(1.0, current + value)))

        # Apply agent-level impacts
        for agent in agents:
            if not getattr(agent, 'is_alive', True):
                continue
            # Fake news affects trust and notoriety
            if article.is_fake:
                if hasattr(agent, 'notoriety'):
                    agent.notoriety = max(0.0, min(1.0, agent.notoriety + 0.01))
                # Low morality agents believe fake news more
                if agent.traits.morality < 0.4:
                    if hasattr(agent, 'trust_in_govt'):
                        agent.trust_in_govt = max(-1.0, min(1.0, agent.trust_in_govt + 0.02))


def process_media_tick(
    world: SimulationState,
    tick_number: int,
    agents: list[AgentState],
    rng,
) -> list[NewsArticle]:
    """Run the full media tick: generate news, apply effects, decay sentiment."""
    articles = generate_daily_news(world, tick_number, rng)
    apply_media_effects(world, articles, agents)

    # Decay sentiment back toward zero
    media_state = world.media_state
    media_state["sentiment_gov"] *= (1 - MEDIA_SENTIMENT_DECAY)
    media_state["sentiment_economy"] *= (1 - MEDIA_SENTIMENT_DECAY)

    # Store articles as dicts in the media_state
    media_state["articles"] = [
        {
            "tick": a.tick,
            "headline": a.headline,
            "body": a.body,
            "category": a.category,
            "is_fake": a.is_fake,
            "impact": dict(a.impact),
        }
        for a in articles
    ]

    return articles
