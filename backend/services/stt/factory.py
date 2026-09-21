"""
STT provider factory.

Returns the configured Speech-to-Text provider based on application settings
or the TELEPHONY_STT_PROVIDER environment variable.
"""

import os
import structlog

from backend.services.stt.base import BaseSTTProvider

logger = structlog.get_logger(__name__)


def get_stt_provider(provider_name: str | None = None) -> BaseSTTProvider:
    """Return the configured STT provider.

    Provider selection order:
    1. Explicit *provider_name* argument.
    2. ``settings.stt_provider`` from application config.
    3. Falls back to ``'mock'`` if config is unavailable.

    Args:
        provider_name: Override the configured provider name.

    Returns:
        An initialised :class:`BaseSTTProvider` instance.
    """
    try:
        from backend.core.config import settings
        name = provider_name or settings.stt_provider
    except Exception:
        name = provider_name or os.environ.get("STT_PROVIDER", "mock")

    logger.info("Creating STT provider", provider=name)

    if name == "google":
        from backend.services.stt.google_stt import GoogleSTTProvider
        return GoogleSTTProvider()
    elif name == "deepgram":
        from backend.services.stt.deepgram_stt import DeepgramSTTProvider
        return DeepgramSTTProvider()
    else:
        if name not in ("mock",):
            logger.warning(
                "Unknown STT provider, falling back to mock", requested=name
            )
        from backend.services.stt.mock_stt import MockSTTProvider
        return MockSTTProvider()
