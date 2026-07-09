"""
AI Configuration
================

Configuration parameters for AI model routing.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIConfig:
    vllm_base_url: str = "http://localhost:8001"
    amd_base_url: str = os.getenv("AMD_API_BASE_URL", "")
    model_name: str = "gemma-2-9b-it"
    request_timeout: float = 30.0
    max_retries: int = 3
    batch_size: int = 10
    enable_caching: bool = True
    cache_ttl: int = 3600
