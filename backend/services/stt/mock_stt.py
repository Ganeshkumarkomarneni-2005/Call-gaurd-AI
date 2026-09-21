"""
Mock Speech-to-Text provider for development and testing.

Returns predefined transcripts from a fixed list, cycling through them
in a deterministic order. Useful for simulating conversations without
any real API keys.

STATUS: MOCK_IMPLEMENTATION
"""

import asyncio
import random
from typing import AsyncIterator

from backend.services.stt.base import BaseSTTProvider


# Silence threshold: chunks smaller than this many bytes are treated as silence.
_SILENCE_THRESHOLD_BYTES = 160


class MockSTTProvider(BaseSTTProvider):
    """
    Mock Speech-to-Text provider.

    STATUS: MOCK_IMPLEMENTATION
    Returns predefined transcripts for testing.
    """

    provider_name = "mock"

    # Predefined responses for known audio patterns
    MOCK_RESPONSES = [
        "Hello, this is an automated recruitment assistant from ABC Technologies.",
        "I am calling regarding your application for the Data Analyst position.",
        "Your application has been shortlisted. Please pay 5000 rupees to proceed.",
        "Hi, I am calling to offer you an exclusive deal on our premium service.",
        "This is your bank calling. Please verify your OTP immediately.",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._response_index: int = 0

    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> str:
        """Return a cycling mock transcript, or empty string for silence.

        Args:
            audio_data: Raw PCM audio bytes. Very short/silent chunks return ''.
            language: Language tag (ignored in mock mode).

        Returns:
            A mock transcript string.
        """
        await asyncio.sleep(0.05)  # simulate network / processing latency

        # Treat very short chunks as silence
        if len(audio_data) < _SILENCE_THRESHOLD_BYTES:
            return ""

        response = self.MOCK_RESPONSES[self._response_index % len(self.MOCK_RESPONSES)]
        self._response_index += 1
        self.logger.debug(
            "[MOCK STT] Transcribed audio",
            bytes=len(audio_data),
            transcript=response,
        )
        return response

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "en",
    ) -> AsyncIterator[str]:
        """Yield one mock transcript per audio chunk (ignores actual content).

        Args:
            audio_stream: Async iterator of PCM audio chunks.
            language: Language tag (ignored in mock mode).

        Yields:
            Mock transcript strings.
        """
        async for chunk in audio_stream:
            if len(chunk) < _SILENCE_THRESHOLD_BYTES:
                # Silence: yield nothing
                continue
            transcript = await self.transcribe_audio(chunk, language)
            if transcript:
                yield transcript

    async def health_check(self) -> bool:
        """Always healthy in mock mode."""
        return True
