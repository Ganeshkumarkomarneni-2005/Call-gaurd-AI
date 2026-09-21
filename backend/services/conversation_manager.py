"""
Conversation state manager for active calls.

Maintains per-call conversation history and arbitrary key-value state
in memory. Thread-safe for concurrent asyncio access within a single process.

For multi-process / distributed deployments, replace the in-memory dicts
with a Redis-backed store.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ConversationTurn:
    """A single utterance in a conversation."""
    speaker: str          # 'agent' | 'caller'
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)


class ConversationManager:
    """
    Manages conversation state for active calls.

    Stores per-call conversation history and arbitrary running analysis state.
    All methods are synchronous and safe for use in async contexts (no I/O).
    """

    def __init__(self) -> None:
        self._conversations: dict[str, list[ConversationTurn]] = {}
        self._call_state: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_conversation(self, call_id: str) -> None:
        """Initialise a new conversation for *call_id*.

        Args:
            call_id: Unique identifier of the call.

        Raises:
            ValueError: If a conversation for *call_id* already exists.
        """
        if call_id in self._conversations:
            logger.warning("start_conversation: already exists", call_id=call_id)
            return
        self._conversations[call_id] = []
        self._call_state[call_id] = {}
        logger.info("Conversation started", call_id=call_id)

    def end_conversation(self, call_id: str) -> list[ConversationTurn]:
        """Finalise and remove the conversation, returning its full history.

        Args:
            call_id: Unique identifier of the call.

        Returns:
            Complete list of :class:`ConversationTurn` objects for the call.
        """
        history = self._conversations.pop(call_id, [])
        self._call_state.pop(call_id, None)
        logger.info(
            "Conversation ended",
            call_id=call_id,
            turns=len(history),
        )
        return history

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def add_turn(
        self,
        call_id: str,
        speaker: str,
        text: str,
        metadata: dict | None = None,
    ) -> ConversationTurn:
        """Append a new utterance to the conversation history.

        Args:
            call_id: Unique identifier of the call.
            speaker: ``'agent'`` or ``'caller'``.
            text: Spoken text for this turn.
            metadata: Optional extra data (e.g. confidence scores).

        Returns:
            The newly created :class:`ConversationTurn`.

        Raises:
            KeyError: If no conversation exists for *call_id*.
        """
        if call_id not in self._conversations:
            raise KeyError(f"No conversation found for call_id={call_id!r}")
        turn = ConversationTurn(
            speaker=speaker,
            text=text,
            metadata=metadata or {},
        )
        self._conversations[call_id].append(turn)
        logger.debug(
            "Turn added",
            call_id=call_id,
            speaker=speaker,
            text_preview=text[:60],
        )
        return turn

    def get_conversation(self, call_id: str) -> list[ConversationTurn]:
        """Return the full conversation history for *call_id*.

        Args:
            call_id: Unique identifier of the call.

        Returns:
            List of :class:`ConversationTurn` objects (may be empty).
        """
        return list(self._conversations.get(call_id, []))

    def get_conversation_as_text(self, call_id: str) -> str:
        """Return a human-readable transcript string.

        Args:
            call_id: Unique identifier of the call.

        Returns:
            Formatted transcript with speaker labels.
        """
        turns = self.get_conversation(call_id)
        lines = []
        for turn in turns:
            label = "Agent" if turn.speaker == "agent" else "Caller"
            lines.append(f"{label}: {turn.text}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def set_state(self, call_id: str, key: str, value: Any) -> None:
        """Set an arbitrary state value for the call.

        Useful for storing running analysis results, flags, or counters.

        Args:
            call_id: Unique identifier of the call.
            key: State key name.
            value: Value to store (must be JSON-serialisable).
        """
        if call_id not in self._call_state:
            self._call_state[call_id] = {}
        self._call_state[call_id][key] = value

    def get_state(self, call_id: str, key: str, default: Any = None) -> Any:
        """Retrieve a state value for the call.

        Args:
            call_id: Unique identifier of the call.
            key: State key name.
            default: Value to return if *key* is not found.

        Returns:
            Stored value or *default*.
        """
        return self._call_state.get(call_id, {}).get(key, default)

    def get_all_state(self, call_id: str) -> dict[str, Any]:
        """Return the full state dict for *call_id*.

        Args:
            call_id: Unique identifier of the call.

        Returns:
            Copy of the call state dictionary.
        """
        return dict(self._call_state.get(call_id, {}))

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def active_calls(self) -> list[str]:
        """Return all currently active call IDs."""
        return list(self._conversations.keys())

    def turn_count(self, call_id: str) -> int:
        """Return the number of turns recorded for *call_id*."""
        return len(self._conversations.get(call_id, []))
