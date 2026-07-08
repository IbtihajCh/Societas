# Progress Report: AMD MI300X Server Setup for SOCIETAS

**Date:** 2026-07-08  
**Author:** Technical Lead  
**Status:** Infrastructure Ready for AI Systems Engineer

---

## Server Specifications

| Component | Details |
|-----------|---------|
| GPU | AMD MI300X (192GB HBM3 VRAM) |
| OS | Ubuntu 22.04/24.04 |
| ROCm | Installed and verified |
| Access | SSH (under Tech Lead account) |

---

## vLLM Installation

### Direct Deployment (Recommended for Testing)

```bash
# Create virtual environment
python3 -m venv vllm-env
source vllm-env/bin/activate

# Install vLLM with ROCm support
pip install vllm-rocm

# Verify installation
python3 -c "import vllm; print(vllm.__version__)"
```

**Critical:** Use `vllm-rocm`, not `vllm`. The standard vLLM package is CUDA-only.

---

## Model Selection: Gemma 4

### Recommended Models

| Model | Params | VRAM Usage | Context | Use Case |
|-------|--------|------------|---------|----------|
| `google/gemma-4-31B` | 30.7B | ~65GB | 256K | **Production** (recommended) |
| `google/gemma-4-26B-A4B` | 25.2B (3.8B active) | ~50GB | 256K | Fast inference (MoE) |
| `google/gemma-4-12B` | 11.95B | ~28GB | 256K | Multimodal, faster iteration |

### Download Commands

```bash
# Install huggingface-cli
pip install huggingface_hub

# Download Gemma 4 31B (recommended)
huggingface-cli download google/gemma-4-31B --local-dir /opt/models/gemma-4-31B

# OR download MoE variant for faster inference
huggingface-cli download google/gemma-4-26B-A4B --local-dir /opt/models/gemma-4-26B-A4B

# OR download multimodal variant
huggingface-cli download google/gemma-4-12B --local-dir /opt/models/gemma-4-12B
```

---

## Server Launch Commands

### Production Configuration

```bash
python3 -m vllm.entrypoints.openai.api_server \
  --model /opt/models/gemma-4-31B \
  --host 0.0.0.0 \
  --port 8001 \
  --device rocm \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32768 \
  --tensor-parallel-size 1 \
  --enable-prefix-caching \
  --max-num-seqs 256
```

### Key Flags

- `--device rocm` — **required** for AMD GPUs
- `--gpu-memory-utilization 0.90` — use 90% of 192GB (~173GB)
- `--max-model-len 32768` — leverage Gemma 4's 256K context
- `--enable-prefix-caching` — cache system prompts for efficiency

---

## API Verification

```bash
# Test the OpenAI-compatible API
curl http://localhost:8001/v1/models

# Test a completion
curl http://localhost:8001/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/opt/models/gemma-4-31B",
    "prompt": "Hello, world!",
    "max_tokens": 50
  }'

# Test chat completion (for policy translation)
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/opt/models/gemma-4-31B",
    "messages": [
      {"role": "system", "content": "You are a policy translator..."},
      {"role": "user", "content": "Translate: Increase universal basic income"}
    ],
    "max_tokens": 200,
    "temperature": 0.3
  }'
```

---

## Docker Deployment (For Production)

### ROCm-based vLLM Dockerfile

Create `docker/vllm-rocm.Dockerfile`:

```dockerfile
FROM rocm/vllm-dev:rocm6.2_ubuntu22.04

ENV MODEL_NAME=google/gemma-4-31B
ENV GPU_MEMORY_UTILIZATION=0.90

EXPOSE 8001

ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
CMD ["--model", "${MODEL_NAME}", "--port", "8001", "--gpu-memory-utilization", "${GPU_MEMORY_UTILIZATION}", "--device", "rocm"]
```

### Updated docker-compose.yml (vllm service)

```yaml
vllm:
  build:
    context: ..
    file: docker/vllm-rocm.Dockerfile
  container_name: societas-vllm
  ports:
    - "${VLLM_PORT:-8001}:8001"
  environment:
    - MODEL_NAME=${VLLM_MODEL:-google/gemma-4-31B}
    - GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.90}
  devices:
    - /dev/kfd
    - /dev/dri
  group_add:
    - video
    - render
  shm_size: '8gb'
  restart: unless-stopped
  networks:
    - societas-net
```

---

## Next Steps for AI Systems Engineer

1. **Verify server access** — SSH to the MI300X and confirm ROCm is working:
   ```bash
   rocminfo
   rocm-smi
   ```

2. **Install vLLM and download Gemma 4** — follow the commands above

3. **Launch the vLLM server** — use the production configuration

4. **Test prompt schemas** — verify all 6 SOCIETAS prompts work with Gemma 4:
   - `tie-break.md` — decision arbitration (temperature 0.2)
   - `policy-translation.md` — goal → utility weights (temperature 0.3)
   - `persona-generation.md` — traits → personas (temperature 0.7)
   - `narrative-generation.md` — events → news articles (temperature 0.8)
   - `governance-advisor.md` — strategic policy advice (temperature 0.5)
   - `system-prompts.md` — shared components

5. **Benchmark performance** — measure latency and throughput for each prompt type

6. **Report findings** — document any prompt adjustments needed for Gemma 4

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `vllm-rocm` not found | Use `pip install vllm --extra-index-url https://download.pytorch.org/whl/rocm6.2` |
| GPU not detected | Run `rocminfo` to verify ROCm sees the MI300X |
| Out of memory | Reduce `--gpu-memory-utilization` to 0.80 |
| Slow inference | Enable `--enable-prefix-caching` and increase `--max-num-seqs` |
| Backend can't connect | Check `VLLM_HOST` env var points to the vLLM server |

---

## References

- [Gemma 4 Model Card](https://ai.google.dev/gemma/docs/core/model_card_4)
- [vLLM ROCm Documentation](https://docs.vllm.ai/en/latest/getting_started/amd-installation.html)
- [SOCIETAS Prompts](../prompts/)
- [SOCIETAS Architecture](./references/architecture-overview.md)
