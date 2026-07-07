FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir vllm

ENV MODEL_NAME=google/gemma-2-9b-it
ENV GPU_MEMORY_UTILIZATION=0.90

EXPOSE 8001

ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
CMD ["--model", "${MODEL_NAME}", "--port", "8001", "--gpu-memory-utilization", "${GPU_MEMORY_UTILIZATION}"]
