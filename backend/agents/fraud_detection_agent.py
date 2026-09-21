"""Fraud Detection Agent.

Scans conversation turns for explicit fraud signals across nine indicator
categories.  Each detected indicator is returned with a type, description,
severity level, and confidence score.

Context matters:
    * A bank legitimately asking "can I confirm the last 4 digits of your card
      number?" is low risk.
    * An unknown caller demanding a full card number + CVV + PIN is CRITICAL.

The agent uses this contextual logic:
    1. Match keyword/phrase patterns.
    2. Look for mitigating context (e.g., caller already identified as bank).
    3. Assign severity based on specificity + combination of flags.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from backend.agents.base import BaseAgent
from backend.models.enums import FraudIndicatorType, Severity
from backend.schemas.analysis import ClassificationInput, RiskIndicator


# ---------------------------------------------------------------------------
# Internal pattern descriptor
# ---------------------------------------------------------------------------


@dataclass
class _IndicatorSpec:
    """Specification for a single fraud indicator category."""

    indicator_type: FraudIndicatorType
    patterns: list[re.Pattern[str]]
    base_severity: Severity
    base_confidence: float
    description_template: str


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

def _cp(pattern: str, flags: int = re.I) -> re.Pattern[str]:
    """Compile a regex pattern with default flags."""
    return re.compile(pattern, flags)


_INDICATOR_SPECS: list[_IndicatorSpec] = [
    _IndicatorSpec(
        indicator_type=FraudIndicatorType.OTP_REQUEST,
        patterns=[
            _cp(r"\b(otp|one[\s\-]?time\s+(?:password|passcode|pin|code))\b"),
            _cp(r"\bverification\s+code\b"),
            _cp(r"\bauth(?:entication)?\s+code\b"),
        ],
        base_severity=Severity.HIGH,
        base_confidence=0.88,
        description_template="Caller requested OTP / one-time password",
    ),
    _IndicatorSpec(
        indicator_type=FraudIndicatorType.PAYMENT_REQUEST,
        patterns=[
            _cp(r"\b(send|transfer|pay|wire)\s+(?:money|funds|cash|amount|inr|rs\.?|₹|\$|usd)\b"),
            _cp(r"\bmake\s+a\s+payment\b"),
            _cp(r"\bpay\s+(?:us|me|now|immediately|right\s+now)\b"),
            _cp(r"\b(?:payment|fee|amount)\s+of\s+(?:inr|rs\.?|₹|\$)?[\d,]+\b"),
        ],
        base_severity=Severity.HIGH,
        base_confidence=0.85,
        description_template="Caller requested a payment or money transfer",
    ),
    _IndicatorSpec(
        indicator_type=FraudIndicatorType.CREDENTIAL_REQUEST,
        patterns=[
            _cp(r"\b(password|pin|secret\s+(?:key|code)|mpin)\b"),
            _cp(r"\b(card\s+(?:number|no|details)|credit\s+card|debit\s+card)\b"),
            _cp(r"\b(cvv|cvc|card\s+verification)\b"),
            _cp(r"\bbank\s+(account\s+(?:number|details)|details|info)\b"),
            _cp(r"\b(internet\s+banking\s+(?:password|credentials)|net\s+banking)\b"),
        ],
        base_severity=Severity.CRITICAL,
        base_confidence=0.92,
        description_template="Caller requested credentials or sensitive banking details",
    ),
    _IndicatorSpec(
        indicator_type=FraudIndicatorType.URGENCY,
        patterns=[
            _cp(r"\b(urgent|urgently|immediately|right\s+now|right\s+away)\b"),
            _cp(r"\btoday\s+only\b"),
            _cp(r"\blimited\s+time\b"),
            _cp(r"\b(expire|expires|expiring)\s+(?:soon|today|in\s+\d+\s+(?:hour|minute|day))\b"),
            _cp(r"\bwithin\s+\d+\s+(?:hours?|minutes?|days?)\b"),
            _cp(r"\blast\s+chance\b"),
        ],
        base_severity=Severity.MEDIUM,
        base_confidence=0.72,
        description_template="Excessive urgency language used to pressure the recipient",
    ),
    _IndicatorSpec(
        indicator_type=FraudIndicatorType.IMPERSONATION,
        patterns=[
            _cp(r"\b(calling|calling\s+on\s+behalf)\s+(?:from\s+)?(?:the\s+)?(?:rbi|reserve\s+bank|income\s+tax|cbi|irs|fbi|police|government|tax\s+(?:department|authority)|social\s+security)\b"),
            _cp(r"\b(government\s+(?:official|agent|officer|department))\b"),
            _cp(r"\bfraud\s+(?:investigation|department|team)\s+(?:of|at|from)\s+(?:your\s+)?bank\b"),
        ],
        base_severity=Severity.HIGH,
        base_confidence=0.80,
        description_template="Caller may be impersonating a government agency, bank, or authority",
    ),
    _IndicatorSpec(
        indicator_type=FraudIndicatorType.THREAT,
        patterns=[
            _cp(r"\b(legal\s+action|court\s+case|arrest\s+warrant|arrest\s+you)\b"),
            _cp(r"\b(your\s+account\s+(?:will\s+be\s+)?(?:blocked|frozen|suspended))\b"),
            _cp(r"\b(penalty|fine\s+of|imprisonment)\b"),
            _cp(r"\b(police\s+will|send\s+police|file\s+(?:an?\s+)?fir)\b"),
        ],
        base_severity=Severity.HIGH,
        base_confidence=0.85,
        description_template="Caller used threats of legal action, arrest, or account blocking",
    ),
    _IndicatorSpec(
        indicator_type=FraudIndicatorType.SENSITIVE_PII,
        patterns=[
            _cp(r"\b(aadhar|aadhaar)\s*(?:number|card|id)?\b"),
            _cp(r"\bpan\s+(?:number|card)\b"),
            _cp(r"\b(passport\s+(?:number|details))\b"),
            _cp(r"\b(ssn|social\s+security\s+(?:number|card))\b"),
            _cp(r"\bnational\s+id\s+(?:number|card)?\b"),
        ],
        base_severity=Severity.HIGH,
        base_confidence=0.82,
        description_template="Caller requested sensitive government-issued identity document number",
    ),
    _IndicatorSpec(
        indicator_type=FraudIndicatorType.SUSPICIOUS_LINK,
        patterns=[
            _cp(r"\bclick\s+(?:on\s+)?this\s+link\b"),
            _cp(r"\bvisit\s+(?:our\s+)?(?:website|portal|page)\s+(?:at\s+)?http"),
            _cp(r"\bdownload\s+(?:our\s+|this\s+)?app\b"),
            _cp(r"\b(?:bit\.ly|tinyurl|t\.me|wa\.me|rb\.gy)/\S+\b"),
        ],
        base_severity=Severity.MEDIUM,
        base_confidence=0.75,
        description_template="Caller directed recipient to a suspicious link or download",
    ),
    _IndicatorSpec(
        indicator_type=FraudIndicatorType.JOB_REGISTRATION_FEE,
        patterns=[
            _cp(r"\b(?:registration|joining|processing|application|training)\s+fee\b"),
            _cp(r"\bpay\s+(?:for|before)\s+(?:your\s+)?(?:interview|joining|onboarding|training)\b"),
            _cp(r"\brefundable\s+(?:deposit|security|amount)\b"),
            _cp(r"\bkit\s+(?:fee|deposit|charges?)\b"),
        ],
        base_severity=Severity.CRITICAL,
        base_confidence=0.95,
        description_template="Caller requested payment as a precondition for employment",
    ),
]

# Mitigating patterns — when present, reduce severity by one level
_MITIGATING_PATTERNS: list[re.Pattern[str]] = [
    _cp(r"\bdo\s+not\s+share\b"),        # Agent warning caller not to share
    _cp(r"\bnever\s+share\b"),
    _cp(r"\bwe\s+will\s+never\s+ask\b"),
    _cp(r"\bdo\s+not\s+provide\b"),
]


class FraudDetectionAgent(BaseAgent):
    """Detect fraud indicators from conversation text.

    Each indicator is scored independently.  Multiple firing indicators in
    the same call compound the overall risk — but that final aggregation is
    handled by :class:`RiskAssessmentAgent`.

    Attributes:
        agent_name:    Identifier surfaced in logs.
        model_version: Semantic version of the detection rules.
    """

    agent_name: str = "FraudDetectionAgent"
    model_version: str = "v1.0-patterns"

    def __init__(self) -> None:
        super().__init__()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process(self, input_data: ClassificationInput) -> list[RiskIndicator]:
        """Scan the conversation for fraud indicators.

        Args:
            input_data: :class:`ClassificationInput` with call UUID and turns.

        Returns:
            List of :class:`RiskIndicator` objects (possibly empty for clean calls).
        """
        self._log_event(
            "fraud_detection_started",
            call_id=str(input_data.call_id),
            turn_count=len(input_data.conversation),
        )

        caller_text = self._build_caller_text(input_data.conversation)
        full_text = " ".join(t.text for t in input_data.conversation)
        has_mitigation = self._check_mitigation(full_text)

        indicators: list[RiskIndicator] = []
        for spec in _INDICATOR_SPECS:
            indicator = self._evaluate_indicator(spec, caller_text, has_mitigation)
            if indicator is not None:
                indicators.append(indicator)

        self._log_event(
            "fraud_detection_complete",
            call_id=str(input_data.call_id),
            indicator_count=len(indicators),
            indicator_types=[i.indicator_type for i in indicators],
        )
        return indicators

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_caller_text(self, conversation: list) -> str:
        """Concatenate all caller turns."""
        return " ".join(
            t.text.strip()
            for t in conversation
            if t.speaker.lower() == "caller"
        )

    def _check_mitigation(self, full_text: str) -> bool:
        """Return True if the conversation contains mitigating language."""
        for pattern in _MITIGATING_PATTERNS:
            if pattern.search(full_text):
                return True
        return False

    def _evaluate_indicator(
        self,
        spec: _IndicatorSpec,
        caller_text: str,
        has_mitigation: bool,
    ) -> RiskIndicator | None:
        """Test a single indicator spec against the caller text.

        Args:
            spec:           The :class:`_IndicatorSpec` to evaluate.
            caller_text:    Concatenated caller-side text.
            has_mitigation: Whether the full conversation contains mitigation.

        Returns:
            :class:`RiskIndicator` if the indicator fires, ``None`` otherwise.
        """
        matched_phrases: list[str] = []
        for pattern in spec.patterns:
            m = pattern.search(caller_text)
            if m:
                matched_phrases.append(m.group().strip())

        if not matched_phrases:
            return None

        # Build description
        unique_phrases = list(dict.fromkeys(matched_phrases))  # preserve order, deduplicate
        description = (
            spec.description_template
            + f". Matched: {', '.join(repr(p) for p in unique_phrases[:3])}"
        )

        # Adjust severity if mitigating language present
        severity = spec.base_severity
        confidence = spec.base_confidence
        if has_mitigation and severity in (Severity.HIGH, Severity.MEDIUM):
            severity = Severity.MEDIUM if severity == Severity.HIGH else Severity.LOW
            confidence = round(confidence * 0.75, 4)
            description += " [severity reduced: mitigating language detected]"

        # Boost confidence if multiple distinct patterns fired
        if len(matched_phrases) >= 2:
            confidence = round(min(confidence + 0.05, 1.0), 4)

        return RiskIndicator(
            indicator_type=spec.indicator_type.value,
            description=description,
            severity=severity.value,
            confidence=confidence,
        )
