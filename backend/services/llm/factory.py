"""
LLM provider factory.

Returns the configured Large Language Model provider based on application
settings or the LLM_PROVIDER environment variable.
"""

import os
import structlog

from backend.services.llm.base import BaseLLMProvider

logger = structlog.get_logger(__name__)


def get_llm_provider(provider_name: str | None = None) -> BaseLLMProvider:
    """Return the configured LLM provider.

    Args:
        provider_name: Override the configured provider name.

    Returns:
        An initialised :class:`BaseLLMProvider` instance.
    """
    try:
        from backend.core.config import settings
        name = provider_name or settings.llm_provider
    except Exception:
        name = provider_name or os.environ.get("LLM_PROVIDER", "mock")

    logger.info("Creating LLM provider", provider=name)

    if name == "openai":
        from backend.services.llm.openai_llm import OpenAILLMProvider
        return OpenAILLMProvider()
    elif name == "gemini":
        from backend.services.llm.gemini_llm import GeminiLLMProvider
        return GeminiLLMProvider()
    else:
        if name not in ("mock",):
            logger.warning(
                "Unknown LLM provider, falling back to mock", requested=name
            )
        from backend.services.llm.mock_llm import MockLLMProvider
        return MockLLMProvider()
