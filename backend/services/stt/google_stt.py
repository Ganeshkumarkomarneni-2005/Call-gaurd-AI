"""
Google Cloud Speech-to-Text provider.

STATUS: STUB - Requires EXTERNAL CREDENTIAL (GOOGLE_SPEECH_API_KEY or
                Application Default Credentials via GOOGLE_APPLICATION_CREDENTIALS)

Required environment variables:
    GOOGLE_SPEECH_API_KEY           - API key (simple key auth)
    -- OR --
    GOOGLE_APPLICATION_CREDENTIALS  - Path to service-account JSON file

Documentation: https://cloud.google.com/speech-to-text/docs
"""

import os
from typing import AsyncIterator

from backend.services.stt.base import BaseSTTProvider


class GoogleSTTProvider(BaseSTTProvider):
    """
    Google Cloud Speech-to-Text provider.

    STATUS: STUB - Requires EXTERNAL CREDENTIAL (GOOGLE_SPEECH_API_KEY)

    Supports:
    - Synchronous audio transcription (short audio < 60 s)
    - Streaming recognition via gRPC (google-cloud-speech SDK)
    - Indian English and Hindi (hi-IN) out-of-the-box

    Install dependencies:
        pip install google-cloud-speech
    """

    provider_name = "google"

    def __init__(
        self,
        api_key: str | None = None,
        credentials_path: str | None = None,
    ) -> None:
        super().__init__()
        self.api_key = api_key or os.environ.get("GOOGLE_SPEECH_API_KEY")
        self.credentials_path = credentials_path or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        # TODO: Initialise google.cloud.speech.SpeechAsyncClient
        # from google.cloud import speech
        # if self.credentials_path:
        #     self._client = speech.SpeechAsyncClient.from_service_account_json(
        #         self.credentials_path
        #     )
        # else:
        #     self._client = speech.SpeechAsyncClient()
        self.logger.warning(
            "GoogleSTTProvider is a stub. Real transcription is not yet wired up."
        )

    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> str:
        """Transcribe a complete audio clip via Google Speech-to-Text REST/gRPC.

        TODO: Implement using google.cloud.speech RecognizeRequest.

        Args:
            audio_data: Raw PCM audio bytes (LINEAR16, 8000 Hz, mono).
            language: BCP-47 language tag (e.g. 'en-IN', 'hi-IN').

        Returns:
            Transcribed text string.
        """
        raise NotImplementedError(
            "GoogleSTTProvider.transcribe_audio requires a Google Cloud credential. "
            "Set GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_SPEECH_API_KEY."
        )

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "en",
    ) -> AsyncIterator[str]:
        """Stream audio to Google Speech-to-Text for real-time transcription.

        TODO: Implement using google.cloud.speech StreamingRecognizeRequest.

        Args:
            audio_stream: Async iterator of PCM chunks.
            language: BCP-47 language tag.

        Yields:
            Partial and final transcript strings.
        """
        raise NotImplementedError(
            "GoogleSTTProvider.transcribe_stream requires a Google Cloud credential."
        )
        yield ""  # type: ignore[misc]

    async def health_check(self) -> bool:
        """Probe Google Speech API for credential validity.

        TODO: Make a minimal API call to verify credentials.
        """
        self.logger.warning("GoogleSTTProvider health_check not implemented")
        return False
