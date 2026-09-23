"""Intent Detection Agent.

Detects the primary (and optional secondary) intent of an incoming call by
scoring caller-turn text against intent-specific keyword sets.

The implementation is intentionally rule-based so it works without any
external API.  The interface is designed so that a trained ML model (TF-IDF +
logistic regression, or a transformer-based classifier) can be plugged in by
overriding :meth:`_ml_predict` without touching any calling code.

Supported intents (see :class:`backend.models.enums.Intent`):
    RECRUITMENT, PROMOTIONAL, FRAUD, CUSTOMER_SERVICE, DELIVERY, PERSONAL,
    OTHER, UNKNOWN
"""

from __future__ import annotations

import re
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.enums import Intent
from backend.schemas.analysis import ClassificationInput, IntentClassificationResult

# ---------------------------------------------------------------------------
# Keyword banks keyed by Intent
# ---------------------------------------------------------------------------

_INTENT_KEYWORDS: dict[Intent, list[str]] = {
    Intent.RECRUITMENT: [
        "job",
        "application",
        "position",
        "role",
        "interview",
        "hiring",
        "recruiter",
        "vacancy",
        "resume",
        "cv",
        "shortlisted",
        "company",
        "offer",
        "candidate",
        "employment",
        "onboard",
        "opening",
        "profile",
        "joining",
    ],
    Intent.PROMOTIONAL: [
        "offer",
        "discount",
        "deal",
        "sale",
        "savings",
        "percent off",
        "limited time",
        "subscribe",
        "free trial",
        "buy now",
        "exclusive",
        "promotion",
        "cashback",
        "reward",
        "special price",
        "membership",
    ],
    Intent.FRAUD: [
        "urgent",
        "otp",
        "verify",
        "pin",
        "password",
        "bank account",
        "pay",
        "transfer",
        "fee",
        "register",
        "advance",
        "deposit",
        "suspicious",
        "kyc",
        "aadhar",
        "pan",
        "card number",
        "cvv",
        "one-time password",
        "verification code",
        "legal action",
        "arrest",
        "police",
        "freeze",
        "blocked",
    ],
    Intent.CUSTOMER_SERVICE: [
        "account",
        "order",
        "support",
        "help",
        "issue",
        "problem",
        "ticket",
        "service",
        "complaint",
        "refund",
        "billing",
        "invoice",
        "cancel",
        "subscription",
        "query",
    ],
    Intent.DELIVERY: [
        "parcel",
        "package",
        "courier",
        "delivery",
        "ship",
        "track",
        "address",
        "logistics",
        "dispatch",
        "out for delivery",
        "shipment",
    ],
    Intent.PERSONAL: [
        "friend",
        "family",
        "personal",
        "calling you",
        "know you",
        "colleague",
        "relative",
        "mom",
        "dad",
        "brother",
        "sister",
    ],
}

# Phrases that boost the score for an intent when found as exact substrings
_INTENT_PHRASES: dict[Intent, list[str]] = {
    Intent.RECRUITMENT: [
        "job opportunity",
        "career opportunity",
        "job offer",
        "shortlisted for",
        "interview scheduled",
        "resume review",
    ],
    Intent.FRAUD: [
        "registration fee",
        "training fee",
        "pay for interview",
        "send money",
        "click this link",
        "download this app",
        "one time password",
        "do not share",
    ],
    Intent.PROMOTIONAL: [
        "limited time offer",
        "percent off",
        "free trial",
        "buy one get",
    ],
    Intent.CUSTOMER_SERVICE: [
        "raise a ticket",
        "our support team",
        "your query",
    ],
    Intent.DELIVERY: [
        "out for delivery",
        "track your parcel",
        "delivery address",
    ],
}


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class IntentDetectionAgent(BaseAgent):
    """Detect primary and secondary call intent using keyword scoring.

    The agent assigns a weighted score to each :class:`Intent` based on
    keyword hits across all *caller* turns.  The intent with the highest
    score becomes the primary intent; the second-highest (if it clears a
    minimum threshold) becomes the secondary intent.

    To replace with an ML model, override :meth:`_ml_predict`.

    Attributes:
        agent_name:    Identifier surfaced in logs.
        model_version: Semantic version of the scoring rules.
    """

    agent_name: str = "IntentDetectionAgent"
    model_version: str = "v1.0-keywords"

    # Minimum normalised score a runner-up must reach to be reported
    _SECONDARY_THRESHOLD: float = 0.20
    # A primary intent is reported as UNKNOWN below this score
    _UNKNOWN_THRESHOLD: float = 0.05

    def __init__(self) -> None:
        super().__init__()
        # Pre-compile patterns once for efficiency
        self._keyword_patterns: dict[Intent, list[re.Pattern[str]]] = {
            intent: [re.compile(rf"\b{re.escape(kw)}\b", re.I) for kw in keywords]
            for intent, keywords in _INTENT_KEYWORDS.items()
        }

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process(self, input_data: ClassificationInput) -> IntentClassificationResult:
        """Detect primary and secondary intent from conversation turns.

        Args:
            input_data: :class:`ClassificationInput` with call UUID and turns.

        Returns:
            :class:`IntentClassificationResult` with primary intent, optional
            secondary intent, confidence, evidence, and model version.
        """
        self._log_event(
            "intent_detection_started",
            call_id=str(input_data.call_id),
            turn_count=len(input_data.conversation),
        )

        # Try ML hook first
        ml_result = self._ml_predict(input_data)
        if ml_result is not None:
            return ml_result

        caller_text = self._build_caller_text(input_data.conversation)
        scores, evidence = self._score_intents(caller_text)

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        total = sum(scores.values()) or 1.0  # avoid division by zero

        primary_intent, primary_raw = ranked[0]
        primary_normalised = primary_raw / total

        if primary_normalised < self._UNKNOWN_THRESHOLD:
            primary_intent = Intent.UNKNOWN
            primary_normalised = 0.40

        secondary_intent: Intent | None = None
        if len(ranked) > 1:
            sec_intent, sec_raw = ranked[1]
            sec_normalised = sec_raw / total
            if (
                sec_normalised >= self._SECONDARY_THRESHOLD
                and sec_intent != primary_intent
                and sec_intent != Intent.UNKNOWN
            ):
                secondary_intent = sec_intent

        confidence = round(min(primary_normalised, 1.0), 4)
        result = IntentClassificationResult(
            intent=primary_intent.value,
            secondary_intent=secondary_intent.value if secondary_intent else None,
            confidence=confidence,
            evidence=evidence.get(primary_intent, []),
            model_version=self.model_version,
        )

        self._log_event(
            "intent_detection_complete",
            call_id=str(input_data.call_id),
            intent=result.intent,
            secondary_intent=result.secondary_intent,
            confidence=result.confidence,
        )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_caller_text(self, conversation: list[Any]) -> str:
        """Concatenate all caller turns into a single lowercase string.

        Args:
            conversation: List of :class:`ConversationTurn` objects.

        Returns:
            Normalised combined text from all caller turns.
        """
        parts = [
            turn.text.strip()
            for turn in conversation
            if turn.speaker.lower() == "caller"
        ]
        return " ".join(parts).lower()

    def _score_intents(
        self, text: str
    ) -> tuple[dict[Intent, float], dict[Intent, list[str]]]:
        """Score each intent against the caller text.

        Args:
            text: Normalised concatenation of caller turns.

        Returns:
            Tuple of (scores dict, evidence dict) keyed by Intent.
        """
        scores: dict[Intent, float] = {intent: 0.0 for intent in _INTENT_KEYWORDS}
        evidence: dict[Intent, list[str]] = {intent: [] for intent in _INTENT_KEYWORDS}

        # Keyword matches (1 point each)
        for intent, patterns in self._keyword_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    scores[intent] += 1.0
                    evidence[intent].append(f"Keyword match: '{match.group()}'")

        # Phrase matches (3 points each — stronger signal)
        for intent, phrases in _INTENT_PHRASES.items():
            for phrase in phrases:
                if phrase.lower() in text:
                    scores[intent] += 3.0
                    evidence[intent].append(f"Phrase match: '{phrase}'")

        return scores, evidence

    # ------------------------------------------------------------------
    # ML extension point
    # ------------------------------------------------------------------

    def _ml_predict(
        self, input_data: ClassificationInput
    ) -> IntentClassificationResult | None:
        """Hook for plugging in a trained intent classifier.

        Attempts to load and run inference with the trained LinearSVC + TF-IDF model
        located in `ml/models/intent_classifier_v1.0.0.joblib`.
        Returns ``None`` to fall back to keyword scoring if model or dependencies
        are not loaded.

        Args:
            input_data: Full classification input including conversation turns.

        Returns:
            :class:`IntentClassificationResult` or ``None`` for fallback.
        """
        try:
            import joblib
            from pathlib import Path

            model_path = Path("ml/models/intent_classifier_v1.0.0.joblib")
            if not model_path.exists():
                return None

            bundle = joblib.load(model_path)
            vectorizer = bundle.get("vectorizer")
            model = bundle.get("model")
            classes = bundle.get("classes", [])

            if not vectorizer or not model:
                return None

            caller_text = self._build_caller_text(input_data.conversation)
            if not caller_text.strip():
                return None

            X = vectorizer.transform([caller_text])
            predicted_label = model.predict(X)[0]

            # Label mapping from dataset tags to domain Intent enum
            label_map = {
                "recruitment": Intent.RECRUITMENT.value,
                "interview_scheduling": Intent.RECRUITMENT.value,
                "fraud_scam": Intent.FRAUD.value,
                "otp_theft": Intent.FRAUD.value,
                "promotional": Intent.PROMOTIONAL.value,
                "customer_service": Intent.CUSTOMER_SERVICE.value,
                "delivery": Intent.DELIVERY.value,
                "unknown": Intent.UNKNOWN.value,
            }

            intent_value = label_map.get(str(predicted_label).lower(), Intent.UNKNOWN.value)

            # Confidence estimation from decision function if available
            confidence = 0.95
            if hasattr(model, "decision_function"):
                try:
                    df = model.decision_function(X)
                    if len(df.shape) > 1:
                        import numpy as np
                        # Softmax approximation over decision scores
                        exp_scores = np.exp(df[0] - np.max(df[0]))
                        probs = exp_scores / np.sum(exp_scores)
                        confidence = float(np.max(probs))
                except Exception:
                    confidence = 0.95

            confidence = round(float(confidence), 4)

            # Top TF-IDF evidence words
            evidence: list[str] = []
            try:
                feature_names = vectorizer.get_feature_names_out()
                row = X.toarray()[0]
                top_indices = row.argsort()[-4:][::-1]
                for idx in top_indices:
                    if row[idx] > 0:
                        evidence.append(f"ML feature cue: '{feature_names[idx]}'")
            except Exception:
                evidence.append(f"ML Model classification: '{predicted_label}'")

            return IntentClassificationResult(
                intent=intent_value,
                secondary_intent=None,
                confidence=confidence,
                evidence=evidence,
                model_version="v1.0.0-linear_svc",
            )
        except Exception:
            return None

