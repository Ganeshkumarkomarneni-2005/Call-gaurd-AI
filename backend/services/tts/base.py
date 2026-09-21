"""
Abstract base class for Text-to-Speech (TTS) providers.

All TTS implementations must satisfy this interface so the voice pipeline
can swap synthesis backends without code changes.
"""

from abc import ABC, abstractmethod
import structlog


class BaseTTSProvider(ABC):
    """Abstract Text-to-Speech provider interface."""

    provider_name: str = "base"

    def __init__(self) -> None:
        self.logger = structlog.get_logger(provider=self.provider_name)

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str = "default",
        language: str = "en",
    ) -> bytes:
        """Synthesise *text* into raw PCM audio bytes.

        Args:
            text: Plain-text string to convert to speech.
            voice: Provider-specific voice identifier or 'default'.
            language: BCP-47 language tag, e.g. 'en', 'hi', 'en-IN'.

        Returns:
            Raw PCM audio bytes (8 kHz, 16-bit, mono) ready for telephony.
        """

    async def health_check(self) -> bool:
        """Verify that the TTS provider is reachable and operational."""
        return True
