"""
Telephony provider factory.

Reads the configured provider name from application settings and returns
an appropriately initialised :class:`BaseTelephonyProvider` instance.
"""

import os
import structlog

from backend.services.telephony.base import BaseTelephonyProvider

logger = structlog.get_logger(__name__)


def get_telephony_provider(provider_name: str | None = None) -> BaseTelephonyProvider:
    """Return the configured telephony provider.

    Provider selection order:
    1. Explicit *provider_name* argument.
    2. ``settings.telephony_provider`` from application config.
    3. Falls back to ``'mock'`` if config is unavailable.

    Args:
        provider_name: Override the configured provider name.

    Returns:
        An initialised :class:`BaseTelephonyProvider` instance.

    Raises:
        EnvironmentError: If the requested provider requires credentials that
            are missing from the environment.
    """
    try:
        from backend.core.config import settings
        name = provider_name or settings.telephony_provider
    except Exception:
        name = provider_name or os.environ.get("TELEPHONY_PROVIDER", "mock")

    logger.info("Creating telephony provider", provider=name)

    if name == "exotel":
        from backend.services.telephony.exotel_provider import ExotelTelephonyProvider
        return ExotelTelephonyProvider(
            sid=os.environ.get("EXOTEL_SID"),
            token=os.environ.get("EXOTEL_TOKEN"),
            from_number=os.environ.get("EXOTEL_FROM_NUMBER"),
            subdomain=os.environ.get("EXOTEL_SUBDOMAIN"),
        )
    else:
        if name not in ("mock",):
            logger.warning(
                "Unknown telephony provider, falling back to mock",
                requested=name,
            )
        from backend.services.telephony.mock_provider import MockTelephonyProvider
        return MockTelephonyProvider()
