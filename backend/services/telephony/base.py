"""
Abstract base class for telephony providers.

Defines the interface that all telephony provider implementations must satisfy,
enabling provider-independent core application logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator
from datetime import datetime
import structlog


@dataclass
class CallEvent:
    """Represents a telephony event during a call lifecycle."""
    event_type: str  # 'incoming', 'answered', 'ended', 'audio', 'dtmf', 'transfer_complete'
    call_id: str
    timestamp: datetime
    data: dict = field(default_factory=dict)


@dataclass
class TelephonyCallInfo:
    """Snapshot of a call current state."""
    call_id: str
    caller_number: str
    virtual_number: str
    provider: str
    started_at: datetime
    status: str  # 'ringing', 'active', 'on_hold', 'transferred', 'ended'


class BaseTelephonyProvider(ABC):
    """Abstract telephony provider interface.

    Implement this to support new telephony providers
    without changing the core application logic.

    All async methods must be safe to call concurrently for different call_ids.
    """

    provider_name: str = "base"

    def __init__(self) -> None:
        self.logger = structlog.get_logger(provider=self.provider_name)

    # ------------------------------------------------------------------
    # Call lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    async def answer_call(self, call_id: str) -> bool:
        """Answer an incoming call.

        Args:
            call_id: Unique identifier of the call to answer.

        Returns:
            True if the call was successfully answered, False otherwise.
        """

    @abstractmethod
    async def end_call(self, call_id: str) -> bool:
        """Terminate a call.

        Args:
            call_id: Unique identifier of the call to terminate.

        Returns:
            True if the call was successfully ended, False otherwise.
        """

    @abstractmethod
    async def transfer_call(self, call_id: str, destination: str) -> bool:
        """Transfer call to a destination number.

        Args:
            call_id: Unique identifier of the call to transfer.
            destination: E.164-formatted destination phone number.

        Returns:
            True if the transfer was initiated successfully, False otherwise.
        """

    # ------------------------------------------------------------------
    # Audio I/O
    # ------------------------------------------------------------------

    @abstractmethod
    async def stream_audio(self, call_id: str) -> AsyncIterator[bytes]:
        """Stream incoming audio from the call.

        Yields raw PCM audio chunks (8 kHz, 16-bit, mono by default).
        The generator ends when the call is terminated.

        Args:
            call_id: Unique identifier of the call to stream.

        Yields:
            Raw audio bytes chunks.
        """

    @abstractmethod
    async def send_audio(self, call_id: str, audio_data: bytes) -> bool:
        """Send audio to the caller.

        Args:
            call_id: Unique identifier of the target call.
            audio_data: Raw PCM audio bytes to send.

        Returns:
            True if the audio was accepted by the provider, False otherwise.
        """

    @abstractmethod
    async def play_tts(self, call_id: str, text: str) -> bool:
        """Play text-to-speech to the caller.

        Args:
            call_id: Unique identifier of the target call.
            text: Plain-text string to speak.

        Returns:
            True if playback was initiated successfully, False otherwise.
        """

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_call_info(self, call_id: str) -> TelephonyCallInfo | None:
        """Get current call information.

        Args:
            call_id: Unique identifier of the call.

        Returns:
            A TelephonyCallInfo snapshot, or None if the call is not found.
        """

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Check if the provider is available.

        Subclasses should override this to make a lightweight API probe.

        Returns:
            True if the provider is reachable and operational.
        """
        return True
