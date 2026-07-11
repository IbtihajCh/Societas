import os
from dataclasses import dataclass, field


_DEFAULT_BASE = "http://165.245.130.202:8000/v1"


@dataclass
class VLLMConfig:
    base_url: str = field(default_factory=lambda: os.getenv("VLLM_BASE_URL", _DEFAULT_BASE))
    base_url_e2b: str = field(default_factory=lambda: os.getenv("VLLM_BASE_URL_E2B", ""))
    base_url_moe_26b: str = field(default_factory=lambda: os.getenv("VLLM_BASE_URL_MOE_26B", ""))
    base_url_dense_31b: str = field(default_factory=lambda: os.getenv("VLLM_BASE_URL_DENSE_31B", ""))

    api_key_e2b: str = field(default_factory=lambda: os.getenv("API_KEY_E2B", ""))
    api_key_moe_26b: str = field(default_factory=lambda: os.getenv("API_KEY_MOE_26B", ""))
    api_key_dense_31b: str = field(default_factory=lambda: os.getenv("API_KEY_DENSE_31B", ""))

    model_e2b: str = "google/gemma-4-e2b-it"
    model_moe_26b: str = "google/gemma-4-26b-a4b-it"
    model_dense_31b: str = "google/gemma-4-31B-it"

    temperature_e2b: float = 0.0
    temperature_moe: float = 0.2
    temperature_dense: float = 0.3

    max_tokens_e2b: int = 64
    max_tokens_moe: int = 256
    max_tokens_dense: int = 512

    timeout_seconds: int = 60
    max_retries: int = 1
