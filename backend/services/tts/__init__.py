"""TTS (Text-to-Speech) service package."""

from backend.services.tts.base import BaseTTSProvider
from backend.services.tts.mock_tts import MockTTSProvider
from backend.services.tts.factory import get_tts_provider

__all__ = ["BaseTTSProvider", "MockTTSProvider", "get_tts_provider"]
