"""Risk Assessment Agent.

Aggregates signals from the Caller Classification, Intent Detection, Fraud
Detection, and Recruitment agents into a single :class:`RiskAssessmentResult`
with an explainable risk level.

Scoring rules (applied in priority order):
    1. Any CRITICAL fraud indicator            → CRITICAL risk
    2. Any HIGH fraud indicator               → at least HIGH risk
    3. ≥2 MEDIUM fraud indicators             → HIGH risk
    4. 1 MEDIUM fraud indicator               → MEDIUM risk
    5. Recruitment + low legitimacy           → HIGH risk (already caught by fraud)
    6. Low intent confidence + unknown caller → at least MEDIUM risk
    7. Clean recruitment + company identity   → LOW risk (may override)
    8. No indicators at all                   → LOW risk
"""

from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models.enums import RiskLevel, Severity
from backend.schemas.analysis import (
    CallerClassificationResult,
    IntentClassificationResult,
    RecruitmentExtractionResult,
    RiskAssessmentResult,
    RiskIndicator,
)


class RiskAssessmentAgent(BaseAgent):
    """Combine all analysis signals into a single explainable risk level.

    Attributes:
        agent_name:    Identifier surfaced in logs.
        model_version: Semantic version of the risk-scoring rules.
    """

    agent_name: str = "RiskAssessmentAgent"
    model_version: str = "v1.0-rules"

    def __init__(self) -> None:
        super().__init__()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process(self, input_data: dict) -> RiskAssessmentResult:
        """Compute the overall call risk level.

        Args:
            input_data: Dictionary containing:
                - ``caller_result``     (:class:`CallerClassificationResult`)
                - ``intent_result``     (:class:`IntentClassificationResult`)
                - ``fraud_indicators``  (list[:class:`RiskIndicator`])
                - ``recruitment_result``(:class:`RecruitmentExtractionResult` | None)

        Returns:
            :class:`RiskAssessmentResult` with level, confidence, indicators,
            and a human-readable explanation.
        """
        caller_result: CallerClassificationResult = input_data["caller_result"]
        intent_result: IntentClassificationResult = input_data["intent_result"]
        fraud_indicators: list[RiskIndicator] = input_data.get("fraud_indicators", [])
        recruitment_result: RecruitmentExtractionResult | None = input_data.get(
            "recruitment_result"
        )

        self._log_event(
            "risk_assessment_started",
            caller_type=caller_result.caller_type,
            intent=intent_result.intent,
            fraud_indicator_count=len(fraud_indicators),
        )

        risk_level, confidence, explanation = self._compute_risk(
            caller_result, intent_result, fraud_indicators, recruitment_result
        )

        result = RiskAssessmentResult(
            risk_level=risk_level.value,
            confidence=round(confidence, 4),
            indicators=fraud_indicators,
            explanation=explanation,
        )

        self._log_event(
            "risk_assessment_complete",
            risk_level=risk_level.value,
            confidence=confidence,
        )
        return result

    # ------------------------------------------------------------------
    # Core scoring logic
    # ------------------------------------------------------------------

    def _compute_risk(
        self,
        caller: CallerClassificationResult,
        intent: IntentClassificationResult,
        indicators: list[RiskIndicator],
        recruitment: RecruitmentExtractionResult | None,
    ) -> tuple[RiskLevel, float, str]:
        """Evaluate all signals and produce a risk level + explanation.

        Args:
            caller:      Caller classification result.
            intent:      Intent detection result.
            indicators:  List of fraud indicators.
            recruitment: Recruitment extraction result (if applicable).

        Returns:
            Tuple of (RiskLevel, confidence, explanation_string).
        """
        explanation_parts: list[str] = []
        risk_level = RiskLevel.LOW
        confidence: float = 0.70

        # --- Rule 1: CRITICAL indicator → CRITICAL ---
        critical_inds = [i for i in indicators if i.severity == Severity.CRITICAL.value]
        if critical_inds:
            risk_level = RiskLevel.CRITICAL
            confidence = max(i.confidence for i in critical_inds)
            for ind in critical_inds:
                explanation_parts.append(
                    f"CRITICAL risk signal: {ind.indicator_type} — {ind.description}"
                )

        # --- Rule 2: HIGH indicator → at least HIGH ---
        high_inds = [i for i in indicators if i.severity == Severity.HIGH.value]
        if high_inds and risk_level.value not in ("CRITICAL",):
            risk_level = RiskLevel.HIGH
            confidence = max(i.confidence for i in high_inds)
            for ind in high_inds:
                explanation_parts.append(
                    f"High risk signal: {ind.indicator_type} — {ind.description}"
                )

        # --- Rule 3: ≥2 MEDIUM indicators → HIGH ---
        medium_inds = [i for i in indicators if i.severity == Severity.MEDIUM.value]
        if len(medium_inds) >= 2 and risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM):
            risk_level = RiskLevel.HIGH
            confidence = sum(i.confidence for i in medium_inds) / len(medium_inds)
            explanation_parts.append(
                f"Multiple medium-severity signals detected ({len(medium_inds)}), "
                f"combined to HIGH risk"
            )
        elif medium_inds and risk_level == RiskLevel.LOW:
            # Rule 4: Single MEDIUM → MEDIUM
            risk_level = RiskLevel.MEDIUM
            confidence = medium_inds[0].confidence
            explanation_parts.append(
                f"Medium-severity signal: {medium_inds[0].indicator_type} — "
                f"{medium_inds[0].description}"
            )

        # --- Rule 5: Recruitment + illegitimate → HIGH (if not already higher) ---
        if (
            recruitment is not None
            and not recruitment.is_legitimate
            and risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)
        ):
            risk_level = RiskLevel.HIGH
            confidence = max(confidence, 0.85)
            explanation_parts.append(
                f"Recruitment call assessed as NOT legitimate: {recruitment.legitimacy_reason}"
            )

        # --- Rule 6: Low intent confidence + unknown caller → MEDIUM ---
        if (
            risk_level == RiskLevel.LOW
            and intent.confidence < 0.35
            and caller.caller_type == "unknown"
        ):
            risk_level = RiskLevel.MEDIUM
            confidence = 0.55
            explanation_parts.append(
                "Low intent confidence combined with unknown caller type raises risk to MEDIUM"
            )

        # --- Rule 7: Legitimate recruitment company, no issues → LOW (override down) ---
        if (
            recruitment is not None
            and recruitment.is_legitimate
            and recruitment.company is not None
            and not indicators
        ):
            risk_level = RiskLevel.LOW
            confidence = max(confidence, 0.75)
            explanation_parts.append(
                f"Confirmed legitimate recruitment from {recruitment.company!r} "
                f"with no suspicious requests"
            )

        # --- Rule 8: No signals at all ---
        if not indicators and not explanation_parts:
            explanation_parts.append("No fraud indicators detected; call appears routine")

        # Build explanation
        explanation = " | ".join(explanation_parts)

        return risk_level, confidence, explanation
