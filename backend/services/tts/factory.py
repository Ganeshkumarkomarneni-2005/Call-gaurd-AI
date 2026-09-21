"""
TTS provider factory.

Returns the configured Text-to-Speech provider based on application settings
or the TTS_PROVIDER environment variable.
"""

import os
import structlog

from backend.services.tts.base import BaseTTSProvider

logger = structlog.get_logger(__name__)


def get_tts_provider(provider_name: str | None = None) -> BaseTTSProvider:
    """Return the configured TTS provider.

    Args:
        provider_name: Override the configured provider name.

    Returns:
        An initialised :class:`BaseTTSProvider` instance.
    """
    try:
        from backend.core.config import settings
        name = provider_name or settings.tts_provider
    except Exception:
        name = provider_name or os.environ.get("TTS_PROVIDER", "mock")

    logger.info("Creating TTS provider", provider=name)

    if name == "google":
        from backend.services.tts.google_tts import GoogleTTSProvider
        return GoogleTTSProvider()
    elif name == "elevenlabs":
        from backend.services.tts.elevenlabs_tts import ElevenLabsTTSProvider
        return ElevenLabsTTSProvider()
    else:
        if name not in ("mock",):
            logger.warning(
                "Unknown TTS provider, falling back to mock", requested=name
            )
        from backend.services.tts.mock_tts import MockTTSProvider
        return MockTTSProvider()
