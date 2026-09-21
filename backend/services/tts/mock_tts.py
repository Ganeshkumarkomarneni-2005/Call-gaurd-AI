"""
Mock Text-to-Speech provider for development and testing.

Returns silence bytes instead of real synthesised audio, allowing the
voice pipeline to function end-to-end without any TTS API credentials.

STATUS: MOCK_IMPLEMENTATION
"""

import asyncio

from backend.services.tts.base import BaseTTSProvider


# 20 ms of PCM silence at 8 kHz, 16-bit mono = 320 bytes
_SILENCE_CHUNK = b"\x00\x00" * 160


def _make_silence(duration_ms: int = 500) -> bytes:
    """Return *duration_ms* milliseconds of PCM silence."""
    samples = int(8000 * duration_ms / 1000)
    return b"\x00\x00" * samples


class MockTTSProvider(BaseTTSProvider):
    """
    Mock Text-to-Speech provider.

    STATUS: MOCK_IMPLEMENTATION
    Returns silence bytes instead of synthesised audio.
    Logs the text that would have been spoken.
    """

    provider_name = "mock"

    async def synthesize(
        self,
        text: str,
        voice: str = "default",
        language: str = "en",
    ) -> bytes:
        """Return silence bytes proportional to text length.

        Simulates a ~150 WPM speaking rate to produce a plausible duration.

        Args:
            text: Text that would be spoken.
            voice: Ignored in mock mode.
            language: Ignored in mock mode.

        Returns:
            Raw PCM silence bytes.
        """
        await asyncio.sleep(0.02)  # simulate tiny synthesis latency
        word_count = len(text.split())
        # Approximate: 150 words/min -> 400 ms/word
        duration_ms = max(200, word_count * 400)
        audio = _make_silence(duration_ms)
        self.logger.info(
            "[MOCK TTS] Would synthesise text",
            text=text,
            voice=voice,
            language=language,
            audio_bytes=len(audio),
        )
        return audio

    async def health_check(self) -> bool:
        """Always healthy in mock mode."""
        return True
