"""
Exotel telephony provider.

STATUS: STUB - Requires EXTERNAL CREDENTIALS

Required environment variables:
    EXOTEL_SID          - Your Exotel Account SID
    EXOTEL_TOKEN        - Your Exotel API Token
    EXOTEL_FROM_NUMBER  - Exotel virtual/ExoPhone number (E.164)
    EXOTEL_SUBDOMAIN    - API subdomain (e.g. api.exotel.com)

Exotel documentation: https://developer.exotel.com/

IMPORTANT: Before production use, verify:
    - Current Exotel API capabilities for real-time audio streaming
    - Exotel pricing and plans for your call volume
    - Indian telecom regulatory requirements (TRAI guidelines)
    - Call recording consent requirements under IT Act / TRAI
    - Data privacy requirements (DPDP Act 2023)

NOTE: Exotel's standard REST API handles call initiation and control but does
NOT natively expose a real-time bidirectional audio WebSocket stream in the
same way Twilio Media Streams does.  Real-time audio integration may require:
    - Exotel Passthru / Conference bridging tricks
    - A custom IVR XML ("ExoML") that connects the leg to your WebSocket
    - Coordination with Exotel support for beta streaming access
These TODOs are marked inline below.
"""

import os
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
import structlog

from backend.services.telephony.base import (
    BaseTelephonyProvider,
    TelephonyCallInfo,
)


class ExotelTelephonyProvider(BaseTelephonyProvider):
    """
    Exotel telephony provider.

    STATUS: STUB - Requires EXTERNAL CREDENTIALS

    Required environment variables:
    - EXOTEL_SID
    - EXOTEL_TOKEN
    - EXOTEL_FROM_NUMBER
    - EXOTEL_SUBDOMAIN
    """

    provider_name = "exotel"
    BASE_URL = "https://{subdomain}/v1/Accounts/{sid}"

    def __init__(
        self,
        sid: str | None = None,
        token: str | None = None,
        from_number: str | None = None,
        subdomain: str | None = None,
    ) -> None:
        super().__init__()
        self.sid = sid or os.environ["EXOTEL_SID"]
        self.token = token or os.environ["EXOTEL_TOKEN"]
        self.from_number = from_number or os.environ["EXOTEL_FROM_NUMBER"]
        self.subdomain = subdomain or os.environ.get(
            "EXOTEL_SUBDOMAIN", "api.exotel.com"
        )
        self.base_url = self.BASE_URL.format(
            subdomain=self.subdomain, sid=self.sid
        )
        self._client = httpx.AsyncClient(
            auth=(self.sid, self.token),
            timeout=30.0,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.logger = structlog.get_logger(
            provider=self.provider_name, sid=self.sid
        )

    # ------------------------------------------------------------------
    # Call lifecycle
    # ------------------------------------------------------------------

    async def answer_call(self, call_id: str) -> bool:
        """Answer an incoming call.

        NOTE: With Exotel, incoming calls are answered automatically when the
        ExoML flow is triggered.  This method can be used to signal readiness
        to the call-flow orchestrator or update internal state.

        TODO: If using Exotel's call-flow API, implement the appropriate
              ExoML response here to accept the incoming call leg.
        """
        self.logger.info("answer_call invoked (Exotel auto-answers via ExoML)", call_id=call_id)
        return True

    async def end_call(self, call_id: str) -> bool:
        """Terminate a call via the Exotel Calls API.

        Reference: https://developer.exotel.com/api/#delete-a-call
        """
        url = f"{self.base_url}/Calls/{call_id}.json"
        try:
            resp = await self._client.delete(url)
            resp.raise_for_status()
            self.logger.info("Call ended via Exotel API", call_id=call_id)
            return True
        except httpx.HTTPStatusError as exc:
            self.logger.error(
                "Failed to end call",
                call_id=call_id,
                status=exc.response.status_code,
                body=exc.response.text,
            )
            return False
        except httpx.RequestError as exc:
            self.logger.error(
                "Network error ending call", call_id=call_id, error=str(exc)
            )
            return False

    async def transfer_call(self, call_id: str, destination: str) -> bool:
        """Transfer a call to *destination*.

        TODO: Verify Exotel live-call transfer capability.
        Possible approach: redirect the call leg using ExoML Dial or
        Exotel's live-call modification API (if available on your plan).

        Reference: https://developer.exotel.com/api/#modify-a-live-call
        """
        url = f"{self.base_url}/Calls/{call_id}.json"
        payload = {
            "Url": f"http://my.exotel.com/{self.sid}/exoml/start_voice/{destination}",
            "Method": "GET",
        }
        try:
            resp = await self._client.post(url, data=payload)
            resp.raise_for_status()
            self.logger.info(
                "Transfer initiated via Exotel API",
                call_id=call_id,
                destination=destination,
            )
            return True
        except httpx.HTTPStatusError as exc:
            self.logger.error(
                "Failed to transfer call",
                call_id=call_id,
                status=exc.response.status_code,
                body=exc.response.text,
            )
            return False
        except httpx.RequestError as exc:
            self.logger.error(
                "Network error transferring call", call_id=call_id, error=str(exc)
            )
            return False

    async def stream_audio(self, call_id: str) -> AsyncIterator[bytes]:
        """Stream incoming audio from the call.

        TODO: Exotel does not yet expose a standard bidirectional audio
              WebSocket stream.  Implement one of the following strategies:
              1. Use Exotel's "Passthru" / "Record" + pull recorded chunks.
              2. Use conference bridging with a media server (e.g. FreeSWITCH).
              3. Use Exotel's ExoML <Stream> verb if/when available.

        Raises:
            NotImplementedError: Until real audio streaming is configured.
        """
        self.logger.error(
            "stream_audio not implemented for Exotel",
            call_id=call_id,
        )
        raise NotImplementedError(
            "Real-time audio streaming from Exotel is not yet implemented. "
            "See module docstring for integration strategies."
        )
        # Make the type-checker happy; this line is unreachable
        yield b""  # type: ignore[misc]

    async def send_audio(self, call_id: str, audio_data: bytes) -> bool:
        """Send audio to the caller.

        TODO: Implement once real-time audio streaming is established.
              Likely via a WebSocket or media server bridge.
        """
        self.logger.warning(
            "send_audio not implemented for Exotel",
            call_id=call_id,
            bytes=len(audio_data),
        )
        raise NotImplementedError(
            "Real-time audio injection into Exotel calls is not yet implemented."
        )

    async def play_tts(self, call_id: str, text: str) -> bool:
        """Play text-to-speech to the caller via Exotel's Say/Play ExoML.

        TODO: Verify the correct Exotel API endpoint for injecting TTS mid-call.
              One approach is to update the call's active ExoML URL to a
              handler that returns a <Say> verb response.
        """
        self.logger.warning(
            "play_tts: mid-call TTS injection not yet implemented for Exotel",
            call_id=call_id,
            text=text,
        )
        raise NotImplementedError(
            "Mid-call TTS via Exotel requires an ExoML <Say> redirect. "
            "See module docstring for integration notes."
        )

    async def get_call_info(self, call_id: str) -> TelephonyCallInfo | None:
        """Fetch call details from the Exotel Calls API.

        Reference: https://developer.exotel.com/api/#fetch-details-of-a-call
        """
        url = f"{self.base_url}/Calls/{call_id}.json"
        try:
            resp = await self._client.get(url)
            resp.raise_for_status()
            data = resp.json()
            call_data = data.get("Call", {})
            return TelephonyCallInfo(
                call_id=call_id,
                caller_number=call_data.get("From", ""),
                virtual_number=call_data.get("PhoneNumberSid", self.from_number),
                provider=self.provider_name,
                started_at=datetime.now(timezone.utc),  # TODO: parse call_data date
                status=call_data.get("Status", "unknown"),
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            self.logger.error(
                "Failed to fetch call info",
                call_id=call_id,
                status=exc.response.status_code,
            )
            return None
        except httpx.RequestError as exc:
            self.logger.error(
                "Network error fetching call info", call_id=call_id, error=str(exc)
            )
            return None

    async def health_check(self) -> bool:
        """Probe the Exotel API to verify credentials and connectivity."""
        url = f"{self.base_url}/Calls.json"
        try:
            resp = await self._client.get(url, params={"PageSize": "1"})
            resp.raise_for_status()
            self.logger.info("Exotel health check passed")
            return True
        except Exception as exc:
            self.logger.error("Exotel health check failed", error=str(exc))
            return False

    async def __aenter__(self) -> "ExotelTelephonyProvider":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()
