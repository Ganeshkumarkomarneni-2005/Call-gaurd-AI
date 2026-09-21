"""Notification Agent.

Determines whether a push notification should be sent to the user, and if so,
composes the notification payload.

Design principles:
    * Do NOT notify on every routine call — only when user attention is needed.
    * Notification priority tiers: low (info), high (warning), urgent (action required).
    * Returns ``None`` for calls that require no notification.
"""

from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models.enums import NotificationType, RiskLevel
from backend.schemas.analysis import (
    CallerClassificationResult,
    DecisionResult,
    IntentClassificationResult,
    RiskAssessmentResult,
)


class NotificationAgent(BaseAgent):
    """Compose notification payloads based on call analysis results.

    Attributes:
        agent_name:    Identifier surfaced in logs.
        model_version: Semantic version of the notification rules.
    """

    agent_name: str = "NotificationAgent"
    model_version: str = "v1.0-rules"

    def __init__(self) -> None:
        super().__init__()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process(self, input_data: dict) -> dict | None:
        """Determine and compose the notification payload.

        Args:
            input_data: Dictionary containing:
                - ``caller_result``  (:class:`CallerClassificationResult`)
                - ``intent_result``  (:class:`IntentClassificationResult`)
                - ``risk_result``    (:class:`RiskAssessmentResult`)
                - ``decision``       (:class:`DecisionResult`)
                - ``call_id``        (str)

        Returns:
            Dictionary ``{"type": str, "title": str, "body": str,
            "priority": str, "call_id": str}`` or ``None`` if no notification
            is needed.
        """
        caller_result: CallerClassificationResult = input_data["caller_result"]
        intent_result: IntentClassificationResult = input_data["intent_result"]
        risk_result: RiskAssessmentResult = input_data["risk_result"]
        decision: DecisionResult = input_data["decision"]
        call_id: str = input_data.get("call_id", "N/A")

        self._log_event(
            "notification_evaluation_started",
            call_id=call_id,
            risk_level=risk_result.risk_level,
            decision=decision.decision,
        )

        payload = self._select_notification(
            call_id, caller_result, intent_result, risk_result, decision
        )

        self._log_event(
            "notification_evaluation_complete",
            call_id=call_id,
            notification_type=payload["type"] if payload else "none",
        )
        return payload

    # ------------------------------------------------------------------
    # Notification selection logic
    # ------------------------------------------------------------------

    def _select_notification(
        self,
        call_id: str,
        caller: CallerClassificationResult,
        intent: IntentClassificationResult,
        risk: RiskAssessmentResult,
        decision: DecisionResult,
    ) -> dict | None:
        """Apply notification trigger rules in priority order.

        Args:
            call_id: UUID string for the call.
            caller:  Caller classification result.
            intent:  Intent detection result.
            risk:    Risk assessment result.
            decision: Final decision result.

        Returns:
            Notification dict or None.
        """
        risk_level = risk.risk_level.lower()
        intent_str = intent.intent.lower()
        caller_type = caller.caller_type.lower()
        decision_str = decision.decision.lower()

        # --- CRITICAL / HIGH risk: URGENT notification ---
        if risk_level == RiskLevel.CRITICAL.value:
            top_indicator = (
                risk.indicators[0].indicator_type if risk.indicators else "unknown signal"
            )
            return self._make_payload(
                call_id=call_id,
                notif_type=NotificationType.HIGH_RISK,
                title="🚨 Critical Risk Call Detected",
                body=(
                    f"A CRITICAL risk call has been detected and ended. "
                    f"Primary signal: {top_indicator}. "
                    f"Please review the call immediately."
                ),
                priority="urgent",
            )

        if risk_level == RiskLevel.HIGH.value:
            indicator_names = ", ".join(
                i.indicator_type for i in risk.indicators[:3]
            ) or "multiple signals"
            return self._make_payload(
                call_id=call_id,
                notif_type=NotificationType.HIGH_RISK,
                title="⚠️ High Risk Call Detected",
                body=(
                    f"A high-risk call ({intent_str.replace('_', ' ').title()}) "
                    f"was detected. Indicators: {indicator_names}. "
                    f"Action taken: {decision_str.replace('_', ' ')}."
                ),
                priority="high",
            )

        # --- Fraud detected (any risk level below HIGH) ---
        if intent_str == "fraud" and risk_level == RiskLevel.MEDIUM.value:
            return self._make_payload(
                call_id=call_id,
                notif_type=NotificationType.FRAUD_DETECTED,
                title="⚠️ Potential Fraud Call",
                body=(
                    "A call with possible fraud indicators was detected. "
                    f"Risk: {risk_level.upper()}. "
                    "Review the call details to decide if action is needed."
                ),
                priority="high",
            )

        # --- Transfer requested ---
        if decision_str == "transfer":
            return self._make_payload(
                call_id=call_id,
                notif_type=NotificationType.TRANSFER_REQUESTED,
                title="📞 Call Transfer Requested",
                body=(
                    f"An incoming {intent_str.replace('_', ' ')} call is "
                    f"being transferred to you. Caller type: {caller_type.upper()}."
                ),
                priority="high",
            )

        # --- AI recruitment call (low/medium risk) ---
        if intent_str == "recruitment" and risk_level in (
            RiskLevel.LOW.value,
            RiskLevel.MEDIUM.value,
        ):
            return self._make_payload(
                call_id=call_id,
                notif_type=NotificationType.RECRUITMENT_DETECTED,
                title="💼 Recruitment Call Received",
                body=(
                    f"A recruitment call from a "
                    f"{'potential employer' if caller_type == 'human' else 'recruiter AI'} "
                    f"was handled by CallGuard. "
                    f"Risk level: {risk_level.upper()}. Review the summary for details."
                ),
                priority="low",
            )

        # --- Unknown caller requiring review ---
        if caller_type == "unknown" and decision_str == "flag_for_review":
            return self._make_payload(
                call_id=call_id,
                notif_type=NotificationType.UNKNOWN_CALLER,
                title="❓ Unknown Caller Flagged",
                body=(
                    "CallGuard could not confidently classify an incoming caller. "
                    "The call has been flagged for your review."
                ),
                priority="low",
            )

        # --- Routine / low-risk: no notification ---
        return None

    # ------------------------------------------------------------------
    # Payload factory
    # ------------------------------------------------------------------

    @staticmethod
    def _make_payload(
        call_id: str,
        notif_type: NotificationType,
        title: str,
        body: str,
        priority: str,
    ) -> dict:
        """Build the notification payload dict.

        Args:
            call_id:    UUID string for the call.
            notif_type: :class:`NotificationType` enum value.
            title:      Short notification title (< 80 chars).
            body:       Longer notification body text.
            priority:   ``"low"`` | ``"high"`` | ``"urgent"``.

        Returns:
            Notification payload dictionary.
        """
        return {
            "type": notif_type.value,
            "title": title,
            "body": body,
            "priority": priority,
            "call_id": call_id,
        }
