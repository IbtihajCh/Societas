"""
AI Configuration
================

Configuration parameters for AI model routing.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AIConfig:
    """
    Configuration for AI model routing.
    
    Attributes:
        vllm_base_url: Base URL for vLLM API
        model_name: Model name to use (e.g., "gemma-2-9b-it")
        request_timeout: HTTP request timeout in seconds
        max_retries: Maximum number of retries on failure
        batch_size: Maximum batch size for parallel requests
        enable_caching: Whether to cache AI responses
        cache_ttl: Cache time-to-live in seconds
    """
    
    vllm_base_url: str = "http://localhost:8001"
    model_name: str = "gemma-2-9b-it"
    request_timeout: float = 30.0
    max_retries: int = 3
    batch_size: int = 10
    enable_caching: bool = True
    cache_ttl: int = 3600
