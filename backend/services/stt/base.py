"""
Abstract base class for Speech-to-Text (STT) providers.

All STT implementations must satisfy this interface, keeping the core
voice pipeline independent of the chosen transcription backend.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator
import structlog


class BaseSTTProvider(ABC):
    """Abstract Speech-to-Text provider interface.

    Implement this class to integrate a new STT backend (Google, Deepgram,
    Whisper, etc.) without touching the voice pipeline.
    """

    provider_name: str = "base"

    def __init__(self) -> None:
        self.logger = structlog.get_logger(provider=self.provider_name)

    @abstractmethod
    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> str:
        """Transcribe a complete audio clip to text.

        Args:
            audio_data: Raw PCM audio bytes (8 kHz, 16-bit, mono).
            language: BCP-47 language tag, e.g. 'en', 'hi', 'en-IN'.

        Returns:
            Transcribed text string, or empty string if nothing was detected.
        """

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "en",
    ) -> AsyncIterator[str]:
        """Transcribe a live audio stream, yielding partial/final transcripts.

        Args:
            audio_stream: Async iterator of raw PCM audio byte chunks.
            language: BCP-47 language tag.

        Yields:
            Transcript strings (may be partial results followed by a final one).
        """

    async def health_check(self) -> bool:
        """Verify that the STT provider is reachable and operational.

        Returns:
            True if healthy.
        """
        return True
