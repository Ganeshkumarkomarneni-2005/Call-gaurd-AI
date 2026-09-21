"""Call Summary Agent.

Generates a human-readable, structured call summary from all upstream analysis
results and the raw conversation transcript.

In mock/rule-based mode the summary is composed from template strings populated
with extracted values.  This can be replaced by an LLM-powered summariser by
overriding :meth:`_llm_summarise`.

Output format:
    A formatted string containing:
    * One-paragraph natural language summary
    * Key points bullet list
    * Caller information section
    * Intent, risk, and decision sections
    * Recruitment details (if applicable)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.agents.base import BaseAgent
from backend.schemas.analysis import (
    CallerClassificationResult,
    ConversationTurn,
    DecisionResult,
    IntentClassificationResult,
    RecruitmentExtractionResult,
    RiskAssessmentResult,
)


class CallSummaryAgent(BaseAgent):
    """Generate a concise, structured plain-text call summary.

    Attributes:
        agent_name:    Identifier surfaced in logs.
        model_version: Semantic version of the summary template.
    """

    agent_name: str = "CallSummaryAgent"
    model_version: str = "v1.0-template"

    def __init__(self) -> None:
        super().__init__()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process(self, input_data: dict) -> str:
        """Generate a formatted call summary.

        Args:
            input_data: Dictionary containing:
                - ``conversation``      (list[:class:`ConversationTurn`])
                - ``caller_result``     (:class:`CallerClassificationResult`)
                - ``intent_result``     (:class:`IntentClassificationResult`)
                - ``risk_result``       (:class:`RiskAssessmentResult`)
                - ``recruitment_result``(:class:`RecruitmentExtractionResult` | None)
                - ``decision``          (:class:`DecisionResult`)
                - ``call_id``           (str)

        Returns:
            Formatted multi-section summary string.
        """
        conversation: list[ConversationTurn] = input_data.get("conversation", [])
        caller_result: CallerClassificationResult = input_data["caller_result"]
        intent_result: IntentClassificationResult = input_data["intent_result"]
        risk_result: RiskAssessmentResult = input_data["risk_result"]
        recruitment_result: RecruitmentExtractionResult | None = input_data.get(
            "recruitment_result"
        )
        decision: DecisionResult = input_data["decision"]
        call_id: str = input_data.get("call_id", "N/A")

        self._log_event("summary_generation_started", call_id=call_id)

        # Try LLM hook first
        llm_summary = self._llm_summarise(input_data)
        if llm_summary is not None:
            return llm_summary

        summary = self._build_summary(
            call_id,
            conversation,
            caller_result,
            intent_result,
            risk_result,
            recruitment_result,
            decision,
        )

        self._log_event(
            "summary_generation_complete",
            call_id=call_id,
            summary_length=len(summary),
        )
        return summary

    # ------------------------------------------------------------------
    # Template builder
    # ------------------------------------------------------------------

    def _build_summary(
        self,
        call_id: str,
        conversation: list[ConversationTurn],
        caller: CallerClassificationResult,
        intent: IntentClassificationResult,
        risk: RiskAssessmentResult,
        recruitment: RecruitmentExtractionResult | None,
        decision: DecisionResult,
    ) -> str:
        """Assemble the multi-section summary string.

        Args:
            call_id:     UUID string for the call.
            conversation: Full conversation turn list.
            caller:      Caller classification result.
            intent:      Intent detection result.
            risk:        Risk assessment result.
            recruitment: Recruitment extraction result (or None).
            decision:    Final decision result.

        Returns:
            Formatted summary string.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        caller_turns = [t for t in conversation if t.speaker.lower() == "caller"]
        total_turns = len(conversation)

        # --- Natural language paragraph ---
        intent_str = intent.intent.replace("_", " ").title()
        secondary_str = (
            f" with secondary intent of {intent.secondary_intent.replace('_', ' ').title()}"
            if intent.secondary_intent
            else ""
        )
        caller_type_str = caller.caller_type.upper()
        risk_str = risk.risk_level.upper()
        decision_str = decision.decision.replace("_", " ").title()
        action_phrase = self._decision_phrase(decision.decision)

        paragraph = (
            f"An incoming call was received and analysed by CallGuard AI on {now}. "
            f"The calling party was classified as a {caller_type_str} caller "
            f"(confidence: {caller.confidence:.0%}). "
            f"The primary intent was detected as {intent_str}{secondary_str} "
            f"(confidence: {intent.confidence:.0%}). "
            f"The overall risk level was assessed as {risk_str}. "
            f"The system decided to {action_phrase}. "
            f"The conversation comprised {total_turns} turns, "
            f"of which {len(caller_turns)} were from the caller."
        )

        # --- Key points ---
        key_points: list[str] = [
            f"Caller type: {caller_type_str} ({caller.confidence:.0%} confidence)",
            f"Intent: {intent_str}{secondary_str}",
            f"Risk level: {risk_str}",
            f"Decision: {decision_str}",
        ]
        if caller.evidence:
            key_points.append(f"Caller evidence: {'; '.join(caller.evidence[:2])}")
        if risk.indicators:
            top_indicators = [i.indicator_type for i in risk.indicators[:3]]
            key_points.append(f"Risk indicators: {', '.join(top_indicators)}")
        if recruitment and recruitment.company:
            key_points.append(
                f"Recruitment: {recruitment.company!r} — "
                f"{'LEGITIMATE' if recruitment.is_legitimate else 'POTENTIALLY FRAUDULENT'}"
            )

        key_points_str = "\n".join(f"  • {pt}" for pt in key_points)

        # --- Sections ---
        sections: list[str] = [
            "=" * 60,
            "CALLGUARD AI — CALL SUMMARY",
            "=" * 60,
            f"Call ID  : {call_id}",
            f"Timestamp: {now}",
            "",
            "OVERVIEW",
            "-" * 40,
            paragraph,
            "",
            "KEY POINTS",
            "-" * 40,
            key_points_str,
            "",
            "CALLER INFORMATION",
            "-" * 40,
            f"  Type       : {caller_type_str}",
            f"  Confidence : {caller.confidence:.0%}",
            f"  Evidence   : {'; '.join(caller.evidence) if caller.evidence else 'None'}",
            "",
            "INTENT",
            "-" * 40,
            f"  Primary    : {intent_str}",
            f"  Secondary  : {intent.secondary_intent or 'None'}",
            f"  Confidence : {intent.confidence:.0%}",
            "",
            "RISK ASSESSMENT",
            "-" * 40,
            f"  Level      : {risk_str}",
            f"  Confidence : {risk.confidence:.0%}",
            f"  Explanation: {risk.explanation}",
        ]

        if risk.indicators:
            sections.append("  Indicators :")
            for ind in risk.indicators:
                sections.append(
                    f"    [{ind.severity.upper()}] {ind.indicator_type}: {ind.description}"
                )

        sections += [
            "",
            "ACTION TAKEN",
            "-" * 40,
            f"  Decision   : {decision_str}",
            f"  Reason     : {decision.reason}",
            f"  Confidence : {decision.confidence:.0%}",
            f"  Human Review Required: {'YES' if decision.requires_human_review else 'NO'}",
        ]

        # --- Recruitment details ---
        if recruitment:
            sections += [
                "",
                "RECRUITMENT DETAILS",
                "-" * 40,
                f"  Company         : {recruitment.company or 'Not extracted'}",
                f"  Recruiter       : {recruitment.recruiter_name or 'Not extracted'}",
                f"  Position        : {recruitment.position or 'Not extracted'}",
                f"  Interview Stage : {recruitment.interview_stage or 'Not extracted'}",
                f"  Interview Date  : {recruitment.interview_date or 'Not extracted'}",
                f"  Interview Time  : {recruitment.interview_time or 'Not extracted'}",
                f"  Next Step       : {recruitment.next_step or 'Not extracted'}",
                f"  Legitimate      : {'YES' if recruitment.is_legitimate else 'NO — ' + (recruitment.legitimacy_reason or '')}",
            ]

        sections.append("=" * 60)
        return "\n".join(sections)

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _decision_phrase(self, decision: str) -> str:
        """Convert a decision enum value to a readable phrase."""
        mapping = {
            "ai_handle": "continue handling the call autonomously",
            "notify": "notify the user and continue handling the call",
            "transfer": "transfer the call to a human operator",
            "end": "end the call",
            "flag_for_review": "flag the call for human review",
        }
        return mapping.get(decision.lower(), decision)

    # ------------------------------------------------------------------
    # LLM extension point
    # ------------------------------------------------------------------

    def _llm_summarise(self, input_data: dict) -> str | None:
        """Hook for plugging in an LLM-based summariser.

        Override in a subclass to use GPT-4 / Gemini / local LLM.
        Return ``None`` to fall back to the template-based summary.

        Args:
            input_data: Full input dict as passed to :meth:`process`.

        Returns:
            Formatted summary string or ``None`` for fallback.
        """
        return None
