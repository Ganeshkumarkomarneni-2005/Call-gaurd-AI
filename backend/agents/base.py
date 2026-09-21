"""Base agent class for all CallGuard AI agents.

Every concrete agent inherits from :class:`BaseAgent` and must implement
the :meth:`process` coroutine.  The base class provides:

* A shared ``structlog`` logger bound with the agent name and version.
* A convenience :meth:`_log_event` helper.
* Standard ``agent_name`` / ``model_version`` class attributes that
  subclasses override.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog


class BaseAgent(ABC):
    """Base class for all CallGuard AI agents.

    Subclasses must:
    1. Set ``agent_name`` and ``model_version`` as class attributes.
    2. Implement the async :meth:`process` coroutine with strongly-typed
       input/output signatures.
    3. Never raise unhandled exceptions — catch internally and return a
       degraded but valid result where possible.
    """

    agent_name: str = "BaseAgent"
    model_version: str = "v1"

    def __init__(self) -> None:
        self.logger: structlog.BoundLogger = structlog.get_logger(
            agent=self.agent_name,
            model_version=self.model_version,
        )

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process *input_data* and return a typed result.

        Args:
            input_data: Agent-specific input.  Concrete agents annotate this
                        with a Pydantic schema or ``dict``.

        Returns:
            Agent-specific output — a Pydantic model, primitive, or dict.
        """

    def _log_event(self, event: str, **kwargs: Any) -> None:
        """Emit a structured log event bound with this agent's metadata.

        Args:
            event:   Human-readable event description.
            **kwargs: Arbitrary key-value pairs merged into the log record.
        """
        self.logger.info(event, agent=self.agent_name, **kwargs)
