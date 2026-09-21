"""
Deepgram Speech-to-Text provider.

STATUS: STUB - Requires EXTERNAL CREDENTIAL (DEEPGRAM_API_KEY)

Required environment variables:
    DEEPGRAM_API_KEY - Your Deepgram API key

Documentation: https://developers.deepgram.com/docs

Deepgram advantages for CallGuard AI:
    - Very low latency (< 300 ms) streaming transcription
    - Excellent support for Indian-accented English
    - Nova-2 model achieves high accuracy on phone audio (8 kHz)
    - Built-in punctuation, numerals, and profanity filtering

Install dependencies:
    pip install deepgram-sdk
"""

import os
from typing import AsyncIterator

from backend.services.stt.base import BaseSTTProvider


class DeepgramSTTProvider(BaseSTTProvider):
    """
    Deepgram Speech-to-Text provider.

    STATUS: STUB - Requires EXTERNAL CREDENTIAL (DEEPGRAM_API_KEY)
    """

    provider_name = "deepgram"

    DEFAULT_MODEL = "nova-2"
    DEFAULT_LANGUAGE = "en-IN"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
    ) -> None:
        super().__init__()
        self.api_key = api_key or os.environ.get("DEEPGRAM_API_KEY")
        self.model = model
        # TODO: Initialise Deepgram async client
        # from deepgram import DeepgramClient, PrerecordedOptions, LiveOptions
        # self._client = DeepgramClient(api_key=self.api_key)
        self.logger.warning(
            "DeepgramSTTProvider is a stub. Real transcription is not yet wired up."
        )

    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> str:
        """Transcribe a complete audio clip via Deepgram pre-recorded API.

        TODO: Implement using deepgram.DeepgramClient.listen.prerecorded.v1.transcribe_file.

        Args:
            audio_data: Raw PCM audio bytes.
            language: BCP-47 language tag (e.g. 'en-IN').

        Returns:
            Transcribed text string.
        """
        raise NotImplementedError(
            "DeepgramSTTProvider.transcribe_audio requires DEEPGRAM_API_KEY."
        )

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "en",
    ) -> AsyncIterator[str]:
        """Stream audio to Deepgram for real-time transcription.

        TODO: Implement using deepgram.DeepgramClient.listen.live.v1.

        Args:
            audio_stream: Async iterator of PCM audio chunks.
            language: BCP-47 language tag.

        Yields:
            Partial and final transcript strings.
        """
        raise NotImplementedError(
            "DeepgramSTTProvider.transcribe_stream requires DEEPGRAM_API_KEY."
        )
        yield ""  # type: ignore[misc]

    async def health_check(self) -> bool:
        """Probe the Deepgram API to validate the API key.

        TODO: Make a minimal balance/usage API call.
        """
        self.logger.warning("DeepgramSTTProvider health_check not implemented")
        return False
