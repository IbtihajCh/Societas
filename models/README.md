# AI Model Router

Inference routing and response handling for the SOCIETAS 3× Gemma 4 cluster on AMD MI300X.

## Key Files

- `ai_router.py` — `IAIRouter` implementation, request dispatch
- `vllm_client.py` — vLLM API client (ROCm / AMD GPU)
- `prompt_renderer.py` — Jinja2 prompt template rendering
- `response_parser.py` — Structured output parsing and validation
- `cache.py` — Inference result cache layer

## How to Test

```bash
pytest tests/unit/models/ -v
```

## Dependencies

- `shared/`, `prompts/`
- httpx, jinja2
