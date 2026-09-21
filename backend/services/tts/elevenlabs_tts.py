"""
ElevenLabs Text-to-Speech provider.

STATUS: STUB - Requires EXTERNAL CREDENTIAL (ELEVENLABS_API_KEY)

Required environment variables:
    ELEVENLABS_API_KEY - Your ElevenLabs API key

Documentation: https://docs.elevenlabs.io/

ElevenLabs advantages for CallGuard AI:
    - Extremely natural-sounding voices with emotional range
    - Supports multilingual synthesis including Hindi and Indian English
    - Low-latency streaming synthesis via /v1/text-to-speech/{id}/stream
    - Voice cloning capability for consistent agent persona

Install dependencies:
    pip install elevenlabs
"""

import os

from backend.services.tts.base import BaseTTSProvider


class ElevenLabsTTSProvider(BaseTTSProvider):
    """
    ElevenLabs Text-to-Speech provider.

    STATUS: STUB - Requires EXTERNAL CREDENTIAL (ELEVENLABS_API_KEY)
    """

    provider_name = "elevenlabs"

    # A neutral, professional-sounding ElevenLabs voice
    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    STREAMING_ENDPOINT = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    OUTPUT_FORMAT = "pcm_8000"  # 8 kHz PCM for telephony

    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str | None = None,
    ) -> None:
        super().__init__()
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.environ.get(
            "ELEVENLABS_VOICE_ID", self.DEFAULT_VOICE_ID
        )
        # TODO: Initialise httpx.AsyncClient with auth header
        # self._client = httpx.AsyncClient(
        #     headers={"xi-api-key": self.api_key},
        #     timeout=30.0,
        # )
        self.logger.warning(
            "ElevenLabsTTSProvider is a stub. Real synthesis is not yet wired up."
        )

    async def synthesize(
        self,
        text: str,
        voice: str = DEFAULT_VOICE_ID,
        language: str = "en",
    ) -> bytes:
        """Synthesise *text* using ElevenLabs streaming TTS.

        TODO: Implement using ElevenLabs /v1/text-to-speech/{id}/stream endpoint.
              Stream response body and collect PCM chunks.

        Args:
            text: Plain text to synthesise.
            voice: ElevenLabs voice ID.
            language: BCP-47 language code (ElevenLabs auto-detects language).

        Returns:
            Raw PCM bytes at 8000 Hz.
        """
        raise NotImplementedError(
            "ElevenLabsTTSProvider.synthesize requires ELEVENLABS_API_KEY."
        )

    async def health_check(self) -> bool:
        """TODO: Check ElevenLabs quota/status endpoint."""
        self.logger.warning("ElevenLabsTTSProvider health_check not implemented")
        return False
