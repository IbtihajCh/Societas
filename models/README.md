# AI Models Module

**Owner:** AI Engineer

## Purpose

AI model routing and inference for SOCIETAS. Handles all interactions with the Gemma 2 9B IT model via vLLM.

## Responsibilities

- Route requests to appropriate AI models
- Manage prompt templates and rendering
- Parse and validate AI responses
- Handle batching and caching
- Provide fallback behavior when AI unavailable

## Dependencies

- `shared/` - Shared schemas, types, and interfaces
- `prompts/` - Prompt templates
- `httpx` - HTTP client for vLLM API
- `jinja2` - Prompt template rendering

## Public Interfaces

### AIRouter
- `translate_policy()` - Translate goals to utility weights
- `tie_break()` - Resolve ambiguous decisions
- `generate_news()` - Generate news articles
- `generate_persona()` - Generate agent personas
- `generate_narration()` - Generate spotlight narrations
- `is_available()` - Check AI availability

## Prompt Templates

- `prompts/policy-translation.md` - Goal to weight translation (temp 0.3)
- `prompts/tie-break.md` - Ambiguous decision resolution (temp 0.2)
- `prompts/narrative-generation.md` - News generation (temp 0.8)
- `prompts/persona-generation.md` - Persona creation (temp 0.7)

## Future Work

- Implement vLLM API client
- Add prompt template rendering
- Implement response parsing and validation
- Add batching support
- Add caching layer
- Implement error handling and retries
- Add evaluation metrics
