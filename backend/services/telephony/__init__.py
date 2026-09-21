"""
Telephony service package.

Exports all available telephony provider implementations and the factory
function used to obtain the configured provider at runtime.
"""

from backend.services.telephony.base import (
    BaseTelephonyProvider,
    CallEvent,
    TelephonyCallInfo,
)
from backend.services.telephony.mock_provider import MockTelephonyProvider
from backend.services.telephony.exotel_provider import ExotelTelephonyProvider
from backend.services.telephony.factory import get_telephony_provider

__all__ = [
    "BaseTelephonyProvider",
    "CallEvent",
    "TelephonyCallInfo",
    "MockTelephonyProvider",
    "ExotelTelephonyProvider",
    "get_telephony_provider",
]
