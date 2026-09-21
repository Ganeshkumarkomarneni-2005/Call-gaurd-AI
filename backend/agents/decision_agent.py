"""Decision Agent.

Makes the final call-handling decision by evaluating the outputs of all
preceding agents against a configurable, priority-ordered rule set.

Decision vocabulary (see :class:`backend.models.enums.Decision`):
    * AI_HANDLE       – AI continues handling the call autonomously.
    * NOTIFY          – Inform the user in-app and continue handling.
    * TRANSFER        – Transfer the call to a human operator.
    * END             – End the call immediately.
    * FLAG_FOR_REVIEW – Take no drastic action; mark for manual review.

Design principles:
    * Never end a call solely because the caller is an AI.
    * Low-confidence signals default to FLAG_FOR_REVIEW, not END.
    * Every rule is documented with its rationale.
    * Rules are evaluated in priority order; first match wins.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from backend.agents.base import BaseAgent
from backend.models.enums import CallerType, Decision, Intent, RiskLevel
from backend.schemas.analysis import (
    CallerClassificationResult,
    DecisionResult,
    IntentClassificationResult,
    RecruitmentExtractionResult,
    RiskAssessmentResult,
)


# ---------------------------------------------------------------------------
# Policy rule type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _PolicyRule:
    """A single decision policy rule.

    Attributes:
        name:        Human-readable rule identifier (for logging).
        description: Why this rule exists (documentation).
        predicate:   Function that takes the context dict and returns bool.
        decision:    :class:`Decision` to apply when predicate is True.
        confidence:  Base confidence for this decision (0.0 – 1.0).
        requires_review: Whether to set ``requires_human_review=True``.
    """

    name: str
    description: str
    predicate: Callable[[dict], bool]
    decision: Decision
    confidence: float
    requires_review: bool = False


# ---------------------------------------------------------------------------
# Policy table (evaluated top-to-bottom; first match wins)
# ---------------------------------------------------------------------------

_POLICY: list[_PolicyRule] = [
    _PolicyRule(
        name="CRITICAL_RISK_END",
        description=(
            "CRITICAL risk calls (e.g., credential theft, active extortion) are "
            "ended immediately to protect the user.  This is the only case where "
            "END is the primary action — still flagged for review."
        ),
        predicate=lambda ctx: ctx["risk_level"] == RiskLevel.CRITICAL.value,
        decision=Decision.END,
        confidence=0.95,
        requires_review=True,
    ),
    _PolicyRule(
        name="HIGH_RISK_FRAUD_END",
        description=(
            "HIGH-risk calls whose PRIMARY intent is FRAUD are ended. "
            "Continuing would expose the user to active fraud."
        ),
        predicate=lambda ctx: (
            ctx["risk_level"] == RiskLevel.HIGH.value
            and ctx["intent"] == Intent.FRAUD.value
        ),
        decision=Decision.END,
        confidence=0.90,
        requires_review=True,
    ),
    _PolicyRule(
        name="HIGH_RISK_RECRUITMENT_FLAG",
        description=(
            "HIGH-risk recruitment calls (recruitment fraud pattern detected) "
            "should not be ended outright — the caller may still be legitimate "
            "but suspicious.  Flag for human review instead."
        ),
        predicate=lambda ctx: (
            ctx["risk_level"] == RiskLevel.HIGH.value
            and ctx["intent"] == Intent.RECRUITMENT.value
        ),
        decision=Decision.FLAG_FOR_REVIEW,
        confidence=0.85,
        requires_review=True,
    ),
    _PolicyRule(
        name="HIGH_RISK_GENERIC_TRANSFER",
        description=(
            "Any other HIGH-risk call (not specifically fraud/recruitment) is "
            "transferred to a human operator who can make a final judgement."
        ),
        predicate=lambda ctx: ctx["risk_level"] == RiskLevel.HIGH.value,
        decision=Decision.TRANSFER,
        confidence=0.80,
        requires_review=True,
    ),
    _PolicyRule(
        name="MEDIUM_RISK_FRAUD_FLAG",
        description=(
            "MEDIUM-risk calls with fraud intent are flagged for review rather "
            "than ended — they may be borderline (e.g., a real bank calling)."
        ),
        predicate=lambda ctx: (
            ctx["risk_level"] == RiskLevel.MEDIUM.value
            and ctx["intent"] == Intent.FRAUD.value
        ),
        decision=Decision.FLAG_FOR_REVIEW,
        confidence=0.78,
        requires_review=True,
    ),
    _PolicyRule(
        name="RECRUITMENT_LOW_MEDIUM_NOTIFY",
        description=(
            "Recruitment calls with LOW or MEDIUM risk are safe enough for the "
            "AI to continue handling, but the user should be notified so they "
            "can intervene if desired."
        ),
        predicate=lambda ctx: (
            ctx["intent"] == Intent.RECRUITMENT.value
            and ctx["risk_level"] in (RiskLevel.LOW.value, RiskLevel.MEDIUM.value)
        ),
        decision=Decision.NOTIFY,
        confidence=0.82,
        requires_review=False,
    ),
    _PolicyRule(
        name="UNKNOWN_LOW_CONFIDENCE_FLAG",
        description=(
            "Calls where intent OR caller confidence is low and the caller type "
            "is UNKNOWN carry too much uncertainty for automated action. "
            "Flag for human review — never make destructive decisions under "
            "high uncertainty."
        ),
        predicate=lambda ctx: (
            ctx["caller_type"] == CallerType.UNKNOWN.value
            and ctx["intent_confidence"] < 0.40
        ),
        decision=Decision.FLAG_FOR_REVIEW,
        confidence=0.60,
        requires_review=True,
    ),
    _PolicyRule(
        name="PROMOTIONAL_LOW_RISK_HANDLE",
        description=(
            "Promotional calls with LOW risk (no fraud indicators) can be "
            "handled entirely by the AI.  Typical telemarketing scenario."
        ),
        predicate=lambda ctx: (
            ctx["intent"] == Intent.PROMOTIONAL.value
            and ctx["risk_level"] == RiskLevel.LOW.value
        ),
        decision=Decision.AI_HANDLE,
        confidence=0.88,
        requires_review=False,
    ),
    _PolicyRule(
        name="PROMOTIONAL_MEDIUM_RISK_NOTIFY",
        description="Promotional calls with some risk signals get flagged to the user.",
        predicate=lambda ctx: (
            ctx["intent"] == Intent.PROMOTIONAL.value
            and ctx["risk_level"] == RiskLevel.MEDIUM.value
        ),
        decision=Decision.NOTIFY,
        confidence=0.72,
        requires_review=False,
    ),
    _PolicyRule(
        name="CUSTOMER_SERVICE_AI_HANDLE",
        description=(
            "Legitimate customer service calls (low risk) can be handled "
            "autonomously by the AI agent."
        ),
        predicate=lambda ctx: (
            ctx["intent"] == Intent.CUSTOMER_SERVICE.value
            and ctx["risk_level"] == RiskLevel.LOW.value
        ),
        decision=Decision.AI_HANDLE,
        confidence=0.85,
        requires_review=False,
    ),
    _PolicyRule(
        name="DELIVERY_AI_HANDLE",
        description="Delivery-related calls with no risk indicators are AI-handled.",
        predicate=lambda ctx: (
            ctx["intent"] == Intent.DELIVERY.value
            and ctx["risk_level"] == RiskLevel.LOW.value
        ),
        decision=Decision.AI_HANDLE,
        confidence=0.88,
        requires_review=False,
    ),
    _PolicyRule(
        name="PERSONAL_TRANSFER",
        description=(
            "Calls with a PERSONAL intent (friend, family) should always be "
            "transferred to the human user — the AI should not intercept personal "
            "calls beyond initial greeting."
        ),
        predicate=lambda ctx: ctx["intent"] == Intent.PERSONAL.value,
        decision=Decision.TRANSFER,
        confidence=0.92,
        requires_review=False,
    ),
    _PolicyRule(
        name="DEFAULT_LOW_RISK_HANDLE",
        description=(
            "Fallback: any LOW-risk call with a resolved intent is handled "
            "by the AI.  This covers OTHER, UNKNOWN intents with no red flags."
        ),
        predicate=lambda ctx: ctx["risk_level"] == RiskLevel.LOW.value,
        decision=Decision.AI_HANDLE,
        confidence=0.70,
        requires_review=False,
    ),
    _PolicyRule(
        name="DEFAULT_FALLBACK_FLAG",
        description=(
            "Catch-all: when no specific rule matches (e.g., unusual combination "
            "of signals), flag for human review. Never silently drop ambiguous calls."
        ),
        predicate=lambda ctx: True,  # always matches
        decision=Decision.FLAG_FOR_REVIEW,
        confidence=0.55,
        requires_review=True,
    ),
]


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class DecisionAgent(BaseAgent):
    """Produce the final call-handling decision from all upstream results.

    Attributes:
        agent_name:    Identifier surfaced in logs.
        model_version: Semantic version of the policy rules.
    """

    agent_name: str = "DecisionAgent"
    model_version: str = "v1.0-policy"

    def __init__(self) -> None:
        super().__init__()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process(self, input_data: dict) -> DecisionResult:
        """Evaluate the decision policy and return the handling action.

        Args:
            input_data: Dictionary containing:
                - ``caller_result``     (:class:`CallerClassificationResult`)
                - ``intent_result``     (:class:`IntentClassificationResult`)
                - ``risk_result``       (:class:`RiskAssessmentResult`)
                - ``recruitment_result``(:class:`RecruitmentExtractionResult` | None)
                - ``conversation``      (list of :class:`ConversationTurn`)

        Returns:
            :class:`DecisionResult` with the chosen action and rationale.
        """
        caller_result: CallerClassificationResult = input_data["caller_result"]
        intent_result: IntentClassificationResult = input_data["intent_result"]
        risk_result: RiskAssessmentResult = input_data["risk_result"]

        # Build evaluation context
        ctx = {
            "caller_type": caller_result.caller_type,
            "caller_confidence": caller_result.confidence,
            "intent": intent_result.intent,
            "intent_confidence": intent_result.confidence,
            "secondary_intent": intent_result.secondary_intent,
            "risk_level": risk_result.risk_level,
            "risk_confidence": risk_result.confidence,
        }

        self._log_event(
            "decision_evaluation_started",
            **{k: v for k, v in ctx.items() if isinstance(v, (str, float, int, bool))},
        )

        matched_rule: _PolicyRule | None = None
        for rule in _POLICY:
            if rule.predicate(ctx):
                matched_rule = rule
                break

        # matched_rule is guaranteed (last rule always matches)
        assert matched_rule is not None

        reason = (
            f"Rule '{matched_rule.name}': {matched_rule.description} "
            f"[risk={ctx['risk_level']}, intent={ctx['intent']}, "
            f"caller={ctx['caller_type']}]"
        )

        result = DecisionResult(
            decision=matched_rule.decision.value,
            reason=reason,
            confidence=round(matched_rule.confidence, 4),
            caller_type=caller_result.caller_type,
            intent=intent_result.intent,
            risk_level=risk_result.risk_level,
            requires_human_review=matched_rule.requires_review,
        )

        self._log_event(
            "decision_made",
            decision=result.decision,
            rule=matched_rule.name,
            requires_review=result.requires_human_review,
        )
        return result
