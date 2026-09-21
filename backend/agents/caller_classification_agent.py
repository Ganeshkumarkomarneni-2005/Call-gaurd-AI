"""Caller Classification Agent.

Classifies the calling party as HUMAN, AI, ROBOCALL, or UNKNOWN by analysing
conversation-level features.  The implementation uses a rule-based scoring
approach that is intentionally designed to be replaced or augmented by an
ML model without changing the public interface.

Scoring methodology:
    * Positive AI score  → higher probability of AI/ROBOCALL
    * Positive HUMAN score → pushes toward HUMAN
    * Final label chosen by highest aggregate score after all features evaluated
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.enums import CallerType
from backend.schemas.analysis import CallerClassificationResult, ClassificationInput, ConversationTurn


# ---------------------------------------------------------------------------
# Phrase / pattern banks
# ---------------------------------------------------------------------------

_AI_SELF_ID_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(i am|i'm)\s+(an?\s+)?(ai|bot|automated|virtual assistant|robot|machine)\b", re.I),
    re.compile(r"\b(this is|speaking with)\s+(an?\s+)?(automated|ai|virtual)\b", re.I),
    re.compile(r"\bautomatic(ally)?\s+(calling|dialling|speaking)\b", re.I),
    re.compile(r"\bpowered by (ai|machine learning|artificial intelligence)\b", re.I),
]

_SCRIPTED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bpress\s+\d\b", re.I),
    re.compile(r"\bplease\s+(listen|press|hold|stay|wait)\b", re.I),
    re.compile(r"\bour records show\b", re.I),
    re.compile(r"\bspecially selected\b", re.I),
    re.compile(r"\bcongratulations[\.,!\s]+you\s+(have|'ve)\b", re.I),
    re.compile(r"\bnot hang up\b", re.I),
    re.compile(r"\bdo not disconnect\b", re.I),
]

_ROBOCALL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bpress\s+1\s+to\b", re.I),
    re.compile(r"\bopt out\b", re.I),
    re.compile(r"\bremove\s+(you|your number)\s+from\b", re.I),
    re.compile(r"\bthis\s+(is\s+)?a\s+(pre[-\s]?recorded|recorded)\s+(message|call)\b", re.I),
]

_NATURAL_SPEECH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\buh+\b", re.I),
    re.compile(r"\bum+\b", re.I),
    re.compile(r"\byou know\b", re.I),
    re.compile(r"\bactually\b", re.I),
    re.compile(r"\bsorry[\?,\.]*\b", re.I),
    re.compile(r"\bjust checking\b", re.I),
]


# ---------------------------------------------------------------------------
# Feature dataclass (lightweight dict-like namespace)
# ---------------------------------------------------------------------------


class _Features:
    """Intermediate feature bundle extracted from a conversation."""

    def __init__(self) -> None:
        self.caller_turns: list[str] = []
        self.total_caller_words: int = 0
        self.repeated_phrase_count: int = 0
        self.ai_self_id: bool = False
        self.scripted_match_count: int = 0
        self.robocall_match_count: int = 0
        self.natural_speech_count: int = 0
        self.silence_turn_count: int = 0  # empty or very short turns
        self.turn_count: int = 0
        self.avg_turn_length: float = 0.0


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class CallerClassificationAgent(BaseAgent):
    """Classify the calling party as HUMAN, AI, ROBOCALL, or UNKNOWN.

    In *mock/rule-based* mode the agent analyses text features of caller turns.
    To plug in an ML model, override :meth:`_ml_predict` and return a tuple of
    ``(CallerType, float)``; the scoring engine will respect it.

    Attributes:
        agent_name:    Identifier surfaced in logs.
        model_version: Semantic version of the scoring rules.
    """

    agent_name: str = "CallerClassificationAgent"
    model_version: str = "v1.0-rules"

    # Weights used by the scoring engine
    _W_AI_SELF_ID: float = 0.60
    _W_SCRIPTED: float = 0.15
    _W_ROBOCALL: float = 0.20
    _W_REPETITION: float = 0.10
    _W_NATURAL: float = -0.12  # negative → reduces AI score
    _W_SILENCE: float = 0.12

    def __init__(self) -> None:
        super().__init__()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process(self, input_data: ClassificationInput) -> CallerClassificationResult:
        """Classify the caller type from the conversation transcript.

        Args:
            input_data: :class:`ClassificationInput` containing the call UUID
                        and list of :class:`ConversationTurn` objects.

        Returns:
            :class:`CallerClassificationResult` with caller type, confidence,
            supporting evidence, and model version.
        """
        self._log_event(
            "caller_classification_started",
            call_id=str(input_data.call_id),
            turn_count=len(input_data.conversation),
        )

        features = self._extract_features(input_data.conversation)
        caller_type, confidence, evidence = self._score_ai_indicators(features)

        result = CallerClassificationResult(
            caller_type=caller_type.value,
            confidence=round(confidence, 4),
            evidence=evidence,
            model_version=self.model_version,
        )

        self._log_event(
            "caller_classification_complete",
            call_id=str(input_data.call_id),
            caller_type=caller_type.value,
            confidence=result.confidence,
        )
        return result

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    def _extract_features(self, conversation: list[ConversationTurn]) -> _Features:
        """Extract signals from all caller turns.

        Args:
            conversation: Ordered list of conversation turns.

        Returns:
            Populated :class:`_Features` bundle.
        """
        features = _Features()
        caller_turns = [t for t in conversation if t.speaker.lower() == "caller"]
        features.turn_count = len(caller_turns)

        if not caller_turns:
            return features

        # Raw text collection
        for turn in caller_turns:
            text = turn.text.strip()
            features.caller_turns.append(text)
            features.total_caller_words += len(text.split())

            if len(text.split()) <= 1:
                features.silence_turn_count += 1

        features.avg_turn_length = features.total_caller_words / max(1, features.turn_count)

        # Concatenated text for pattern matching
        full_text = " ".join(features.caller_turns)

        # AI self-identification (highest-value signal)
        for pattern in _AI_SELF_ID_PATTERNS:
            if pattern.search(full_text):
                features.ai_self_id = True
                break

        # Scripted language patterns
        for pattern in _SCRIPTED_PATTERNS:
            if pattern.search(full_text):
                features.scripted_match_count += 1

        # Robocall-specific patterns
        for pattern in _ROBOCALL_PATTERNS:
            if pattern.search(full_text):
                features.robocall_match_count += 1

        # Natural speech disfluencies
        for pattern in _NATURAL_SPEECH_PATTERNS:
            if pattern.search(full_text):
                features.natural_speech_count += 1

        # Repetition — repeated 4-gram phrases (sign of scripted delivery)
        words = re.findall(r"\b\w+\b", full_text.lower())
        ngrams = [" ".join(words[i : i + 4]) for i in range(len(words) - 3)]
        counter = Counter(ngrams)
        features.repeated_phrase_count = sum(v - 1 for v in counter.values() if v > 1)

        return features

    # ------------------------------------------------------------------
    # Scoring engine
    # ------------------------------------------------------------------

    def _score_ai_indicators(
        self, features: _Features
    ) -> tuple[CallerType, float, list[str]]:
        """Compute caller-type scores from extracted features.

        The engine maintains four accumulators (human / ai / robocall / unknown)
        and applies weighted additive scores.  Confidence is derived from the
        margin between the winner and runner-up scores.

        Args:
            features: Pre-extracted :class:`_Features` bundle.

        Returns:
            Tuple of (CallerType, confidence, list-of-evidence-strings).
        """
        evidence: list[str] = []

        ai_score: float = 0.0
        human_score: float = 0.0
        robocall_score: float = 0.0

        # --- No caller turns at all → UNKNOWN ---
        if features.turn_count == 0:
            return CallerType.UNKNOWN, 0.5, ["No caller turns detected in conversation"]

        # --- AI self-identification ---
        if features.ai_self_id:
            ai_score += self._W_AI_SELF_ID
            evidence.append("Caller explicitly identified itself as an AI or automated system")

        # --- Scripted patterns ---
        if features.scripted_match_count >= 2:
            ai_score += self._W_SCRIPTED
            evidence.append(
                f"Scripted language detected in {features.scripted_match_count} patterns"
            )
        elif features.scripted_match_count == 1:
            ai_score += self._W_SCRIPTED * 0.5
            evidence.append("Mild scripted language patterns detected")

        # --- Robocall patterns ---
        if features.robocall_match_count >= 1:
            robocall_score += self._W_ROBOCALL * features.robocall_match_count
            evidence.append(
                f"Robocall pattern(s) detected ({features.robocall_match_count} match(es))"
            )

        # --- Phrase repetition ---
        if features.repeated_phrase_count >= 3:
            ai_score += self._W_REPETITION
            evidence.append(
                f"High phrase repetition detected ({features.repeated_phrase_count} repeated n-grams)"
            )
        elif features.repeated_phrase_count >= 1:
            ai_score += self._W_REPETITION * 0.4
            evidence.append("Mild phrase repetition detected")

        # --- Natural speech disfluencies ---
        if features.natural_speech_count >= 2:
            human_score += abs(self._W_NATURAL) * 1.5
            evidence.append(
                "Natural speech disfluencies present (um/uh/actually etc.) suggesting human speaker"
            )
        elif features.natural_speech_count == 1:
            human_score += abs(self._W_NATURAL)
            evidence.append("Mild natural speech indicators detected")

        # --- Silence / no response ---
        silence_ratio = features.silence_turn_count / max(1, features.turn_count)
        if silence_ratio >= 0.6:
            robocall_score += self._W_SILENCE
            evidence.append(
                f"High silence ratio ({silence_ratio:.0%}) — possible robocall or dead air"
            )

        # --- Short avg turn length (robocall / scripted) ---
        if 0 < features.avg_turn_length < 4:
            robocall_score += 0.08
            evidence.append(f"Very short average turn length ({features.avg_turn_length:.1f} words)")

        # --- Determine winner ---
        scores: dict[CallerType, float] = {
            CallerType.AI: ai_score,
            CallerType.ROBOCALL: robocall_score,
            CallerType.HUMAN: human_score,
        }
        winner = max(scores, key=lambda k: scores[k])
        winner_score = scores[winner]

        # If no signal fires at all → UNKNOWN
        if winner_score <= 0.0:
            return CallerType.UNKNOWN, 0.40, ["Insufficient signals to classify caller type"]

        # Confidence = winner score clamped to [0, 1], adjusted by margin
        sorted_scores = sorted(scores.values(), reverse=True)
        margin = sorted_scores[0] - sorted_scores[1]
        raw_confidence = min(winner_score + margin * 0.3, 1.0)
        confidence = max(0.30, round(raw_confidence, 4))

        return winner, confidence, evidence

    # ------------------------------------------------------------------
    # Extension point: ML model hook
    # ------------------------------------------------------------------

    def _ml_predict(
        self, features: _Features, audio_features: dict[str, Any] | None
    ) -> tuple[CallerType, float] | None:
        """Hook for plugging in an ML model.

        Override this method in a subclass to use a trained classifier.
        Return ``None`` to fall back to rule-based scoring.

        Args:
            features:       Extracted text features.
            audio_features: Raw audio feature dict from the telephony layer.

        Returns:
            Tuple of ``(CallerType, confidence)`` or ``None`` for fallback.
        """
        return None
