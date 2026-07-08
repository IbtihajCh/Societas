FROM rocm/vllm-dev:rocm6.2_ubuntu22.04

# Or use the official vLLM ROCm image if available:
# FROM vllm/vllm-rocm:latest

ENV MODEL_NAME=google/gemma-4-31B
ENV GPU_MEMORY_UTILIZATION=0.90

EXPOSE 8001

ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
CMD ["--model", "${MODEL_NAME}", "--port", "8001", "--gpu-memory-utilization", "${GPU_MEMORY_UTILIZATION}", "--device", "rocm"]
