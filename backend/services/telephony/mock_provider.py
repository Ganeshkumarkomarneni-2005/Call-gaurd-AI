"""
Mock telephony provider for local development and automated testing.

Simulates the full telephony lifecycle in-memory without any real
infrastructure or external credentials.

STATUS: MOCK_IMPLEMENTATION
Real telephony requires EXTERNAL CREDENTIAL (Exotel / other provider).
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator

from backend.services.telephony.base import (
    BaseTelephonyProvider,
    CallEvent,
    TelephonyCallInfo,
)


# ---------------------------------------------------------------------------
# Silence audio: 20 ms of PCM silence at 8 kHz, 16-bit mono
# (320 bytes = 8000 samples/s * 0.02 s * 2 bytes/sample)
# ---------------------------------------------------------------------------
_SILENCE_CHUNK: bytes = b"\x00\x00" * 160  # 320 bytes


class MockTelephonyProvider(BaseTelephonyProvider):
    """
    Mock telephony provider for local development.

    Simulates incoming calls without real telephony infrastructure.
    Useful for:
    - Local development
    - Automated testing
    - Demo scenarios

    STATUS: MOCK_IMPLEMENTATION
    Real telephony requires EXTERNAL CREDENTIAL (Exotel/other provider).
    """

    provider_name = "mock"

    # Class-level in-memory call stores (shared across instances in a process)
    _active_calls: dict[str, TelephonyCallInfo] = {}
    _call_events: dict[str, list[CallEvent]] = {}
    _audio_buffers: dict[str, list[bytes]] = {}
    # Simulated text utterances queued per call for transcription consumers
    _text_queue: dict[str, asyncio.Queue] = {}

    # ------------------------------------------------------------------
    # Abstract method implementations
    # ------------------------------------------------------------------

    async def answer_call(self, call_id: str) -> bool:
        """Set the call status to 'active' in the in-memory store."""
        if call_id not in self._active_calls:
            self.logger.warning("answer_call: unknown call", call_id=call_id)
            return False
        self._active_calls[call_id].status = "active"
        event = CallEvent(
            event_type="answered",
            call_id=call_id,
            timestamp=datetime.now(timezone.utc),
            data={"status": "active"},
        )
        self._call_events.setdefault(call_id, []).append(event)
        self.logger.info("Call answered", call_id=call_id)
        return True

    async def end_call(self, call_id: str) -> bool:
        """Remove the call from active calls and log termination."""
        if call_id not in self._active_calls:
            self.logger.warning("end_call: unknown call", call_id=call_id)
            return False
        self._active_calls[call_id].status = "ended"
        event = CallEvent(
            event_type="ended",
            call_id=call_id,
            timestamp=datetime.now(timezone.utc),
            data={},
        )
        self._call_events.setdefault(call_id, []).append(event)
        # Signal any streaming generators to stop
        if call_id in self._text_queue:
            await self._text_queue[call_id].put(None)  # sentinel
        # Defer cleanup so callers can still read final state
        self.logger.info("Call ended", call_id=call_id)
        self._active_calls.pop(call_id, None)
        return True

    async def transfer_call(self, call_id: str, destination: str) -> bool:
        """Simulate call transfer with a 1-second propagation delay."""
        if call_id not in self._active_calls:
            self.logger.warning("transfer_call: unknown call", call_id=call_id)
            return False
        self.logger.info(
            "Simulating transfer", call_id=call_id, destination=destination
        )
        await asyncio.sleep(1.0)  # simulate network round-trip
        self._active_calls[call_id].status = "transferred"
        event = CallEvent(
            event_type="transfer_complete",
            call_id=call_id,
            timestamp=datetime.now(timezone.utc),
            data={"destination": destination},
        )
        self._call_events.setdefault(call_id, []).append(event)
        self.logger.info(
            "Transfer complete", call_id=call_id, destination=destination
        )
        return True

    async def stream_audio(self, call_id: str) -> AsyncIterator[bytes]:
        """Yield silence chunks at real-time pace until the call ends.

        Each chunk represents 20 ms of audio (320 bytes of PCM silence).
        Consumers can replace individual chunks by pre-loading audio via
        :py:meth:`send_audio` (stored in *_audio_buffers*).
        """
        if call_id not in self._active_calls:
            self.logger.warning("stream_audio: unknown call", call_id=call_id)
            return

        chunk_duration_s = 0.02  # 20 ms per chunk
        while call_id in self._active_calls:
            # Drain any pre-loaded audio first
            buffer = self._audio_buffers.get(call_id, [])
            if buffer:
                chunk = buffer.pop(0)
                yield chunk
            else:
                yield _SILENCE_CHUNK
            await asyncio.sleep(chunk_duration_s)

    async def send_audio(self, call_id: str, audio_data: bytes) -> bool:
        """Store audio in the call-specific buffer (simulates playback)."""
        if call_id not in self._active_calls:
            self.logger.warning("send_audio: unknown call", call_id=call_id)
            return False
        self._audio_buffers.setdefault(call_id, []).append(audio_data)
        self.logger.debug(
            "Audio buffered",
            call_id=call_id,
            bytes=len(audio_data),
        )
        return True

    async def play_tts(self, call_id: str, text: str) -> bool:
        """Log the text that would be spoken (no real synthesis in mock mode)."""
        if call_id not in self._active_calls:
            self.logger.warning("play_tts: unknown call", call_id=call_id)
            return False
        self.logger.info(
            "[MOCK TTS] Would speak text",
            call_id=call_id,
            text=text,
        )
        return True

    async def get_call_info(self, call_id: str) -> TelephonyCallInfo | None:
        """Return call information from the in-memory store."""
        return self._active_calls.get(call_id)

    # ------------------------------------------------------------------
    # Mock-specific helpers
    # ------------------------------------------------------------------

    async def simulate_incoming_call(
        self,
        caller_number: str,
        virtual_number: str = "+911234567890",
    ) -> str:
        """Create a fake incoming call and return its call_id.

        Args:
            caller_number: Simulated caller phone number (E.164 preferred).
            virtual_number: The virtual/DID number that was dialled.

        Returns:
            Newly generated call_id string.
        """
        call_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        info = TelephonyCallInfo(
            call_id=call_id,
            caller_number=caller_number,
            virtual_number=virtual_number,
            provider=self.provider_name,
            started_at=now,
            status="ringing",
        )
        self._active_calls[call_id] = info
        self._call_events[call_id] = [
            CallEvent(
                event_type="incoming",
                call_id=call_id,
                timestamp=now,
                data={"caller": caller_number, "virtual": virtual_number},
            )
        ]
        self._audio_buffers[call_id] = []
        self._text_queue[call_id] = asyncio.Queue()
        self.logger.info(
            "Simulated incoming call",
            call_id=call_id,
            caller=caller_number,
            virtual=virtual_number,
        )
        return call_id

    async def simulate_conversation_turn(
        self, call_id: str, text: str
    ) -> None:
        """Simulate the caller saying something during the call.

        Enqueues *text* so that an STT consumer watching this call
        can retrieve it as a transcribed utterance.

        Args:
            call_id: Target call identifier.
            text: Text representing what the caller said.
        """
        if call_id not in self._active_calls:
            self.logger.warning(
                "simulate_conversation_turn: unknown call", call_id=call_id
            )
            return
        queue = self._text_queue.get(call_id)
        if queue is None:
            self.logger.warning(
                "simulate_conversation_turn: no text queue", call_id=call_id
            )
            return
        await queue.put(text)
        self.logger.info(
            "Simulated caller utterance",
            call_id=call_id,
            text=text,
        )

    def get_events(self, call_id: str) -> list[CallEvent]:
        """Return all recorded events for *call_id* (test helper)."""
        return self._call_events.get(call_id, [])
