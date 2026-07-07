"""
SOCIETAS AI Models Module
==========================

AI model routing and inference for SOCIETAS.

This module handles all AI-related functionality:
- Model routing to vLLM/Gemma
- Policy translation (goals to utility weights)
- Narrative generation (news dispatches)
- Persona generation (agent personas)
- Tie-breaking (ambiguous decision resolution)
- Evaluation metrics

All AI calls go through the router, which manages:
- Model selection
- Prompt templating
- Response parsing
- Error handling
- Batching
"""

from models.router.ai_router import AIRouter
from models.router.config import AIConfig

__version__ = "0.1.0"
__all__ = [
    "AIRouter",
    "AIConfig",
]
