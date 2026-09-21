"""
Google Cloud Text-to-Speech provider.

STATUS: STUB - Requires EXTERNAL CREDENTIAL (GOOGLE_TTS_API_KEY or
                Application Default Credentials via GOOGLE_APPLICATION_CREDENTIALS)

Required environment variables:
    GOOGLE_TTS_API_KEY              - API key (simple key auth)
    -- OR --
    GOOGLE_APPLICATION_CREDENTIALS  - Path to service-account JSON file

Documentation: https://cloud.google.com/text-to-speech/docs

Recommended voices for Indian English:
    en-IN-Neural2-A  (female)
    en-IN-Neural2-B  (male)
    hi-IN-Neural2-A  (Hindi, female)

Install dependencies:
    pip install google-cloud-texttospeech
"""

import os

from backend.services.tts.base import BaseTTSProvider


class GoogleTTSProvider(BaseTTSProvider):
    """
    Google Cloud Text-to-Speech provider.

    STATUS: STUB - Requires EXTERNAL CREDENTIAL (GOOGLE_TTS_API_KEY)
    """

    provider_name = "google"

    DEFAULT_VOICE = "en-IN-Neural2-A"
    DEFAULT_LANGUAGE = "en-IN"
    # Google TTS returns LINEAR16 PCM when audio_encoding=LINEAR16
    SAMPLE_RATE = 8000

    def __init__(
        self,
        api_key: str | None = None,
        credentials_path: str | None = None,
    ) -> None:
        super().__init__()
        self.api_key = api_key or os.environ.get("GOOGLE_TTS_API_KEY")
        self.credentials_path = credentials_path or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        # TODO: Initialise google.cloud.texttospeech.TextToSpeechAsyncClient
        # from google.cloud import texttospeech
        # self._client = texttospeech.TextToSpeechAsyncClient()
        self.logger.warning(
            "GoogleTTSProvider is a stub. Real synthesis is not yet wired up."
        )

    async def synthesize(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        language: str = DEFAULT_LANGUAGE,
    ) -> bytes:
        """Synthesise *text* using Google Cloud TTS.

        TODO: Implement using google.cloud.texttospeech SynthesizeSpeechRequest.

        Args:
            text: Plain text to synthesise.
            voice: Google voice name (e.g. 'en-IN-Neural2-A').
            language: BCP-47 language code.

        Returns:
            Raw LINEAR16 PCM bytes at 8000 Hz.
        """
        raise NotImplementedError(
            "GoogleTTSProvider.synthesize requires a Google Cloud credential. "
            "Set GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_TTS_API_KEY."
        )

    async def health_check(self) -> bool:
        """TODO: Validate Google TTS credentials with a minimal API call."""
        self.logger.warning("GoogleTTSProvider health_check not implemented")
        return False
