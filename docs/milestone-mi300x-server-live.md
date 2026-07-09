# Milestone: MI300X Server Live

**Date:** 2026-07-08  
**Status:** ✅ vLLM + Gemma 4 31B running  

---

## Server Details

| Field | Value |
|-------|-------|
| IP | `165.245.130.202` |
| API Base URL | `http://165.245.130.202:8000/v1` |
| Model | `google/gemma-4-31B` |
| Framework | vLLM with ROCm |
| GPU | AMD MI300X (192GB HBM3) |

---

## Verification

```bash
# Health check
curl http://165.245.130.202:8000/health

# List models
curl http://165.245.130.202:8000/v1/models

# Test inference
curl http://165.245.130.202:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-4-31B",
    "messages": [{"role": "user", "content": "Hello in 5 words"}],
    "max_tokens": 50
  }'
```

---

## Config for Each Team Member

### AI Systems Engineer — `models/router/config.py`
```python
@dataclass
class AIConfig:
    vllm_base_url: str = "http://165.245.130.202:8000/v1"
    model_name: str = "google/gemma-4-31B"
    request_timeout: int = 30
    max_retries: int = 3
```

### Backend Engineer — `backend/app/config/settings.py`
```python
@dataclass(frozen=True)
class Settings:
    # ... existing fields ...
    vllm_base_url: str = "http://165.245.130.202:8000/v1"
    vllm_model: str = "google/gemma-4-31B"
```

### Frontend — `frontend/next.config.js` (no change needed)
The frontend proxies through the backend, not directly to vLLM.

---

## Action Items

- [ ] **AI Systems Engineer:** Update `models/router/config.py` with the endpoint
- [ ] **Backend Engineer:** Update `backend/app/config/settings.py` with the endpoint
- [ ] **Tech Lead:** Update `docs/testing-guide-vllm-gemma4.md` port references from 8001 → 8000
- [ ] **AI Systems Engineer:** Test all 6 prompt schemas against the live endpoint
- [ ] **Tech Lead:** Update `.env.example` with the new port
