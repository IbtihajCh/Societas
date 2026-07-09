# vLLM + Gemma 4 API Testing Guide

**Server:** AMD MI300X (192GB HBM3)  
**Model:** google/gemma-4-31B  
**Framework:** vLLM with ROCm  
**API:** OpenAI-compatible REST endpoint  

---

## 1. Verify Server is Running

After launching vLLM (see `docs/progress-report-mi300x-setup.md`), check it's alive:

```bash
# Check if vLLM process is running
ps aux | grep vllm

# Check if port 8000 is listening
curl http://localhost:8000/health

# Expected response: {"status": "healthy"}
```

If the health check fails:
- Check vLLM logs for errors
- Verify ROCm is working: `rocminfo`
- Check GPU memory: `rocm-smi`

---

## 2. OpenAI-Compatible API Endpoints

vLLM exposes an OpenAI-compatible API. You can use any OpenAI client library or raw HTTP requests.

### Base URL
```
http://localhost:8000/v1
```

### List Available Models
```bash
curl http://localhost:8000/v1/models
```

Expected response:
```json
{
  "data": [
    {
      "id": "google/gemma-4-31B",
      "object": "model",
      "created": 1234567890,
      "owned_by": "vllm"
    }
  ]
}
```

---

## 3. Test Basic Chat Completion

### Using curl
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-4-31B",
    "messages": [
      {"role": "user", "content": "Hello, what is 2+2?"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

### Using Python (OpenAI SDK)
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # vLLM doesn't require auth
)

response = client.chat.completions.create(
    model="google/gemma-4-31B",
    messages=[
        {"role": "user", "content": "Hello, what is 2+2?"}
    ],
    temperature=0.7,
    max_tokens=100
)

print(response.choices[0].message.content)
```

Expected response:
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "google/gemma-4-31B",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "2+2 equals 4."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 5,
    "total_tokens": 15
  }
}
```

---

## 4. Test SOCIETAS Prompts

The 6 SOCIETAS prompts are in `prompts/`. Each has a specific Input/Output schema.

### 4.1 Tie-Break Prompt
**File:** `prompts/tie-break.md`  
**Purpose:** Resolve ambiguous decisions  
**Temperature:** 0.2 (near-deterministic)

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-4-31B",
    "messages": [
      {
        "role": "system",
        "content": "You are the final arbiter in a governance simulation. Two or more policy options have been scored as equally viable by the deterministic engine. Analyze the context and break the tie. Output only valid JSON."
      },
      {
        "role": "user",
        "content": "{\"id\": \"decision-001\", \"state\": \"Economy stable, unemployment 8%\", \"unlust\": 0.3, \"morality\": 0.6, \"options\": [{\"id\": \"opt1\", \"label\": \"Increase UBI\", \"utility_scores\": {\"economic\": 0.7, \"social\": 0.8}}, {\"id\": \"opt2\", \"label\": \"Tax Cut\", \"utility_scores\": {\"economic\": 0.7, \"social\": 0.6}}]}"
      }
    ],
    "temperature": 0.2,
    "max_tokens": 200
  }'
```

**Expected Output:**
```json
{
  "selected_action": "opt1",
  "confidence": 0.85,
  "reasoning": "UBI has higher social utility with equal economic impact",
  "scores": {
    "opt1": 0.75,
    "opt2": 0.65
  }
}
```

---

### 4.2 Policy Translation Prompt
**File:** `prompts/policy-translation.md`  
**Purpose:** Convert natural language policy goals to utility weights  
**Temperature:** 0.3

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-4-31B",
    "messages": [
      {
        "role": "system",
        "content": "Convert the policy goal into utility weights for each need dimension. Output only valid JSON."
      },
      {
        "role": "user",
        "content": "{\"persona\": \"Economist focused on growth\", \"goal\": \"Stimulate economic growth through infrastructure investment\", \"context\": {\"current_gdp_growth\": 2.0, \"unemployment\": 8.0}}"
      }
    ],
    "temperature": 0.3,
    "max_tokens": 200
  }'
```

**Expected Output:**
```json
{
  "weights": {
    "food": 0.1,
    "shelter": 0.2,
    "safety": 0.1,
    "social": 0.1,
    "leisure": 0.0,
    "economic": 0.8,
    "innovation": 0.6
  }
}
```

---

### 4.3 Persona Generation Prompt
**File:** `prompts/persona-generation.md`  
**Purpose:** Generate agent personas from traits  
**Temperature:** 0.7

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-4-31B",
    "messages": [
      {
        "role": "system",
        "content": "Generate a 1-2 sentence persona description from the agent traits. Be specific and vivid."
      },
      {
        "role": "user",
        "content": "{\"traits\": {\"extraversion\": 0.8, \"neuroticism\": 0.2, \"openness\": 0.7, \"conscientiousness\": 0.6, \"agreeableness\": 0.9, \"morality\": 0.8, \"risk_tolerance\": 0.3, \"curiosity\": 0.7}}"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

**Expected Output:**
```
"A warm, socially active community organizer who carefully considers risks but remains optimistic and curious about new ideas."
```

---

### 4.4 Narrative Generation Prompt
**File:** `prompts/narrative-generation.md`  
**Purpose:** Generate news articles from simulation events  
**Temperature:** 0.8

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-4-31B",
    "messages": [
      {
        "role": "system",
        "content": "Generate a news dispatch from the simulation events. Output only valid JSON."
      },
      {
        "role": "user",
        "content": "{\"events\": [{\"type\": \"policy_enacted\", \"policy\": \"Universal Basic Income\", \"tick\": 100}, {\"type\": \"crime_spike\", \"location\": \"District 7\", \"tick\": 105}], \"context\": {\"tick\": 110, \"population\": 1000, \"unemployment\": 6.0}}"
      }
    ],
    "temperature": 0.8,
    "max_tokens": 300
  }'
```

**Expected Output:**
```json
{
  "headline": "UBI Implementation Shows Mixed Results as Crime Rises in District 7",
  "content": "Following the enactment of Universal Basic Income at tick 100, early data shows unemployment has dropped to 6%. However, District 7 has experienced a notable crime spike, raising questions about the policy's unintended consequences.",
  "category": "POLITICAL",
  "sentiment": "NEUTRAL"
}
```

---

### 4.5 Governance Advisor Prompt
**File:** `prompts/governance-advisor.md`  
**Purpose:** Strategic policy advice (stretch goal)  
**Temperature:** 0.5

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-4-31B",
    "messages": [
      {
        "role": "system",
        "content": "You are a strategic governance advisor. Analyze the current state and recommend policy actions."
      },
      {
        "role": "user",
        "content": "{\"state\": {\"gdp_growth\": 1.5, \"unemployment\": 10.0, \"crime_rate\": 8.0, \"happiness\": 0.5}, \"recent_policies\": [\"Tax Increase\", \"Police Funding Cut\"]}"
      }
    ],
    "temperature": 0.5,
    "max_tokens": 400
  }'
```

**Expected Output:**
```json
{
  "recommendations": [
    {
      "policy": "Job Training Program",
      "rationale": "High unemployment requires active labor market intervention",
      "priority": "HIGH"
    },
    {
      "policy": "Community Policing Initiative",
      "rationale": "Crime rising after police funding cut; rebuild trust through community engagement",
      "priority": "MEDIUM"
    }
  ]
}
```

---

### 4.6 System Prompts
**File:** `prompts/system-prompts.md`  
**Purpose:** Shared reusable prompt components  
**Usage:** These are fragments to prepend to other prompts, not standalone

Test by prepending to another prompt:
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-4-31B",
    "messages": [
      {
        "role": "system",
        "content": "You operate within a hybrid system where the deterministic engine retains final decision authority. Your output is advisory — the engine validates all responses before execution. All outputs must be grounded in the provided simulation state. Do not add information, events, or entities that were not present in the input."
      },
      {
        "role": "user",
        "content": "What is the current unemployment rate?"
      }
    ],
    "temperature": 0.2,
    "max_tokens": 100
  }'
```

**Expected Output:**
```
The current unemployment rate is 10.0%.
```

---

## 5. Performance Benchmarking

### Latency Test
```bash
# Measure time for 100 completions
for i in {1..100}; do
  curl -s -o /dev/null -w "%{time_total}\n" \
    http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "google/gemma-4-31B", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50}'
done | awk '{sum+=$1} END {print "Average latency: " sum/NR " seconds"}'
```

**Target:** < 2 seconds per completion for 31B model on MI300X

### Throughput Test
```bash
# Send 10 concurrent requests
for i in {1..10}; do
  curl -s http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "google/gemma-4-31B", "messages": [{"role": "user", "content": "Test"}], "max_tokens": 100}' &
done
wait
echo "All requests completed"
```

### Memory Usage
```bash
# Monitor GPU memory during load
rocm-smi --showmeminfo vram
```

**Expected:** ~65GB VRAM for 31B model at 90% utilization

---

## 6. Integration with SOCIETAS Backend

Once prompts are tested, the AI Systems Engineer should update the backend config:

**File:** `backend/app/config/settings.py`

Add vLLM endpoint:
```python
@dataclass(frozen=True)
class Settings:
    # ... existing fields ...
    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_model: str = "google/gemma-4-31B"
```

**File:** `models/router/config.py`

Update AI config:
```python
@dataclass
class AIConfig:
    vllm_base_url: str = "http://localhost:8000/v1"
    model_name: str = "google/gemma-4-31B"
    request_timeout: int = 30
    max_retries: int = 3
```

---

## 7. Troubleshooting

### Issue: "CUDA out of memory"
**Cause:** Model too large for available VRAM  
**Fix:** Use smaller model (26B-A4B or 12B) or reduce `--max-model-len`

### Issue: "Connection refused" on port 8000
**Cause:** vLLM not running or crashed  
**Fix:** Check logs, restart with `vllm serve google/gemma-4-31B --device rocm`

### Issue: Slow responses (>5 seconds)
**Cause:** Model loading or first request cold start  
**Fix:** Wait for initial load, or enable `--enable-prefix-caching`

### Issue: "Model not found" error
**Cause:** Model not downloaded  
**Fix:** Run `huggingface-cli download google/gemma-4-31B`

### Issue: ROCm errors
**Cause:** ROCm not properly installed  
**Fix:** Run `rocminfo` to verify, reinstall ROCm if needed

---

## 8. Quick Reference

| Task | Command |
|------|---------|
| Health check | `curl http://localhost:8000/health` |
| List models | `curl http://localhost:8000/v1/models` |
| Test chat | See Section 3 |
| Test SOCIETAS prompts | See Section 4 |
| Benchmark latency | See Section 5 |
| Monitor GPU | `rocm-smi` |
| Check VRAM | `rocm-smi --showmeminfo vram` |
| View vLLM logs | Check terminal where vLLM was launched |

---

## Next Steps

1. **AI Systems Engineer:** Run all 6 prompt tests above
2. **AI Systems Engineer:** Benchmark latency and throughput
3. **AI Systems Engineer:** Update `models/router/config.py` with vLLM endpoint
4. **Tech Lead:** Verify backend can call vLLM API
5. **Tech Lead:** Run end-to-end test: simulation → ambiguity → vLLM → decision

---

**Document Version:** 1.0  
**Last Updated:** 2026-07-08  
**Author:** Tech Lead  
**Status:** Active
