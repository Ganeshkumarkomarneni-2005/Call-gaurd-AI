"""Human Handoff Agent.

Prepares a structured handoff summary for the human operator when a call is
transferred.  Responsibilities:

1. Compile all available analysis results into a formatted handoff document.
2. Preserve the full conversation context.
3. Produce a clear recommended action for the receiving operator.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from backend.agents.base import BaseAgent
from backend.schemas.analysis import (
    CallerClassificationResult,
    ConversationTurn,
    DecisionResult,
    HandoffSummary,
    IntentClassificationResult,
    RecruitmentExtractionResult,
    RiskAssessmentResult,
)


class HumanHandoffAgent(BaseAgent):
    """Generate a structured handoff summary for a human operator.

    Attributes:
        agent_name:    Identifier surfaced in logs.
        model_version: Semantic version of the handoff template.
    """

    agent_name: str = "HumanHandoffAgent"
    model_version: str = "v1.0-template"

    def __init__(self) -> None:
        super().__init__()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process(self, input_data: dict) -> HandoffSummary:
        """Generate a :class:`HandoffSummary` for the human operator.

        Args:
            input_data: Dictionary containing:
                - ``call_id``           (str | UUID)
                - ``caller_number``     (str) — E.164 caller number
                - ``conversation``      (list[:class:`ConversationTurn`])
                - ``caller_result``     (:class:`CallerClassificationResult`)
                - ``intent_result``     (:class:`IntentClassificationResult`)
                - ``risk_result``       (:class:`RiskAssessmentResult`)
                - ``recruitment_result``(:class:`RecruitmentExtractionResult` | None)
                - ``decision``          (:class:`DecisionResult`)

        Returns:
            :class:`HandoffSummary` Pydantic model.
        """
        call_id_raw = input_data.get("call_id", "00000000-0000-0000-0000-000000000000")
        call_id = UUID(str(call_id_raw))
        caller_number: str = input_data.get("caller_number", "Unknown")
        conversation: list[ConversationTurn] = input_data.get("conversation", [])
        caller_result: CallerClassificationResult = input_data["caller_result"]
        intent_result: IntentClassificationResult = input_data["intent_result"]
        risk_result: RiskAssessmentResult = input_data["risk_result"]
        recruitment_result: RecruitmentExtractionResult | None = input_data.get(
            "recruitment_result"
        )
        decision: DecisionResult = input_data["decision"]

        self._log_event(
            "handoff_preparation_started",
            call_id=str(call_id),
            risk_level=risk_result.risk_level,
        )

        # Build human-readable formatted document
        formatted_doc = self._build_formatted_document(
            call_id=call_id,
            caller_number=caller_number,
            conversation=conversation,
            caller=caller_result,
            intent=intent_result,
            risk=risk_result,
            recruitment=recruitment_result,
            decision=decision,
        )

        # Build conversation summary (last 5 turns snippet)
        conversation_summary = self._build_conversation_snippet(conversation)

        # Recommended action
        recommendation = self._build_recommendation(risk_result, intent_result, decision)

        result = HandoffSummary(
            call_id=call_id,
            caller_type=caller_result.caller_type,
            intent=intent_result.intent,
            risk_level=risk_result.risk_level,
            company=recruitment_result.company if recruitment_result else None,
            position=recruitment_result.position if recruitment_result else None,
            conversation_summary=formatted_doc,
            recommended_action=recommendation,
        )

        self._log_event(
            "handoff_preparation_complete",
            call_id=str(call_id),
            recommendation=recommendation[:80],
        )
        return result

    # ------------------------------------------------------------------
    # Formatted document builder
    # ------------------------------------------------------------------

    def _build_formatted_document(
        self,
        call_id: UUID,
        caller_number: str,
        conversation: list[ConversationTurn],
        caller: CallerClassificationResult,
        intent: IntentClassificationResult,
        risk: RiskAssessmentResult,
        recruitment: RecruitmentExtractionResult | None,
        decision: DecisionResult,
    ) -> str:
        """Assemble the full handoff document string.

        Args:
            call_id:       UUID of the call.
            caller_number: E.164 phone number string.
            conversation:  Full conversation turns.
            caller:        Caller classification result.
            intent:        Intent detection result.
            risk:          Risk assessment result.
            recruitment:   Recruitment extraction result (or None).
            decision:      Final decision result.

        Returns:
            Multi-section formatted string for the handoff document.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        caller_type_str = caller.caller_type.upper()
        risk_str = risk.risk_level.upper()
        intent_str = intent.intent.replace("_", " ").title()

        lines: list[str] = [
            "CALL HANDOFF SUMMARY",
            "=" * 40,
            f"Call ID  : {call_id}",
            f"Timestamp: {now}",
            "",
            "CALLER INFORMATION",
            "-" * 40,
            f"Type       : {caller_type_str} (confidence: {caller.confidence:.0%})",
            f"Number     : {caller_number}",
        ]
        if caller.evidence:
            lines.append(f"Evidence   : {'; '.join(caller.evidence[:3])}")

        lines += [
            "",
            "INTENT",
            "-" * 40,
            f"Primary    : {intent_str}",
            f"Secondary  : {intent.secondary_intent or 'None'}",
            f"Confidence : {intent.confidence:.0%}",
        ]
        if intent.evidence:
            lines.append(f"Evidence   : {'; '.join(intent.evidence[:3])}")

        lines += [
            "",
            "RISK ASSESSMENT",
            "-" * 40,
            f"Level      : {risk_str}",
            f"Confidence : {risk.confidence:.0%}",
            f"Explanation: {risk.explanation}",
        ]
        if risk.indicators:
            lines.append("Indicators :")
            for ind in risk.indicators:
                lines.append(
                    f"  [{ind.severity.upper()}] {ind.indicator_type}: {ind.description}"
                )

        if recruitment:
            lines += [
                "",
                "RECRUITMENT DETAILS",
                "-" * 40,
                f"Company    : {recruitment.company or 'Not extracted'}",
                f"Position   : {recruitment.position or 'Not extracted'}",
                f"Recruiter  : {recruitment.recruiter_name or 'Not extracted'}",
                f"Stage      : {recruitment.interview_stage or 'Not extracted'}",
                f"Date       : {recruitment.interview_date or 'Not extracted'}",
                f"Time       : {recruitment.interview_time or 'Not extracted'}",
                f"Next Step  : {recruitment.next_step or 'Not extracted'}",
                f"Legitimate : {'YES' if recruitment.is_legitimate else 'NO — ' + (recruitment.legitimacy_reason or '')}",
            ]

        lines += [
            "",
            "DECISION TAKEN BY AI",
            "-" * 40,
            f"Decision   : {decision.decision.replace('_', ' ').title()}",
            f"Reason     : {decision.reason}",
            f"Confidence : {decision.confidence:.0%}",
        ]

        lines += [
            "",
            "CONVERSATION TRANSCRIPT (last 10 turns)",
            "-" * 40,
        ]
        for turn in conversation[-10:]:
            speaker = turn.speaker.upper().ljust(8)
            lines.append(f"  [{speaker}] {turn.text}")

        lines += ["", "=" * 40]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_conversation_snippet(self, conversation: list[ConversationTurn]) -> str:
        """Build a short conversation snippet (last 5 caller turns).

        Args:
            conversation: Full conversation turn list.

        Returns:
            Multi-line snippet string.
        """
        caller_turns = [t for t in conversation if t.speaker.lower() == "caller"]
        recent = caller_turns[-5:]
        if not recent:
            return "No caller speech recorded."
        return "\n".join(f"  Caller: {t.text}" for t in recent)

    def _build_recommendation(
        self,
        risk: RiskAssessmentResult,
        intent: IntentClassificationResult,
        decision: DecisionResult,
    ) -> str:
        """Generate a concrete action recommendation for the operator.

        Args:
            risk:     Risk assessment result.
            intent:   Intent detection result.
            decision: Final decision.

        Returns:
            One-sentence recommendation string.
        """
        risk_level = risk.risk_level.lower()
        intent_str = intent.intent.lower()

        if risk_level == "critical":
            return (
                "URGENT: This call exhibited CRITICAL risk signals. "
                "Do not engage; escalate to your security team immediately."
            )
        if risk_level == "high" and intent_str == "fraud":
            return (
                "This call showed strong fraud indicators. "
                "Do not provide any information. Advise the user not to respond further."
            )
        if risk_level == "high" and intent_str == "recruitment":
            return (
                "This recruitment call showed suspicious indicators (possible recruitment fraud). "
                "Verify the company's identity independently before advising the user."
            )
        if intent_str == "recruitment":
            return (
                "Legitimate recruitment call detected. "
                "Share recruitment details with the user and confirm if they wish to proceed."
            )
        if intent_str == "personal":
            return "Personal call — transfer to the user immediately."
        if risk_level == "medium":
            return (
                "Moderate risk detected. "
                "Review the call details with the user before taking further action."
            )
        return (
            "Routine call. Review the transcript and advise the user as appropriate."
        )
