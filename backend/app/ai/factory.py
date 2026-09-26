"""Provider selection."""
from __future__ import annotations

from functools import lru_cache

from ..config import settings
from .base import AIProvider
from .providers.deepseek import DeepSeekProvider
from .providers.null_provider import NullProvider


@lru_cache(maxsize=1)
def get_provider() -> AIProvider:
    if settings.ai_provider == "deepseek" and settings.deepseek_api_key:
        return DeepSeekProvider()
    return NullProvider()


__all__ = ["get_provider"]