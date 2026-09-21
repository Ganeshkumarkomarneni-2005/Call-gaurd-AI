"""Call Analysis Pipeline.

Orchestrates all nine CallGuard AI agents for end-to-end call analysis.
Uses ``asyncio.gather`` to run independent agents in parallel where possible.

Pipeline stages:
    Stage 1 (parallel): Caller classification + Intent detection
    Stage 2 (conditional): Recruitment extraction (if intent includes RECRUITMENT)
    Stage 3 (parallel): Fraud detection  [no dependency on Stage 2]
    Stage 4 (sequential): Risk assessment (needs all Stage 1-3 outputs)
    Stage 5 (sequential): Decision (needs risk result)
    Stage 6 (parallel): Call summary + Notification determination + Handoff prep
"""

from __future__ import annotations

import asyncio
import time
from typing import Any
from uuid import UUID

from backend.agents.call_summary_agent import CallSummaryAgent
from backend.agents.caller_classification_agent import CallerClassificationAgent
from backend.agents.decision_agent import DecisionAgent
from backend.agents.fraud_detection_agent import FraudDetectionAgent
from backend.agents.human_handoff_agent import HumanHandoffAgent
from backend.agents.intent_detection_agent import IntentDetectionAgent
from backend.agents.notification_agent import NotificationAgent
from backend.agents.recruitment_agent import RecruitmentAgent
from backend.agents.risk_assessment_agent import RiskAssessmentAgent
from backend.schemas.analysis import (
    CallerClassificationResult,
    ClassificationInput,
    ConversationTurn,
    DecisionResult,
    HandoffSummary,
    IntentClassificationResult,
    RecruitmentExtractionResult,
    RiskAssessmentResult,
    RiskIndicator,
)

import structlog

logger = structlog.get_logger(component="CallAnalysisPipeline")


class CallAnalysisPipeline:
    """Orchestrate all agents for a complete call analysis.

    Instantiates all nine agents and runs them in dependency order,
    parallelising where there are no data dependencies.

    Example usage::

        pipeline = CallAnalysisPipeline()
        result = await pipeline.analyze_call(
            conversation=[...],
            call_id="550e8400-e29b-41d4-a716-446655440000",
        )

    Attributes:
        caller_classifier: :class:`CallerClassificationAgent` instance.
        intent_detector:   :class:`IntentDetectionAgent` instance.
        recruitment_agent: :class:`RecruitmentAgent` instance.
        fraud_detector:    :class:`FraudDetectionAgent` instance.
        risk_assessor:     :class:`RiskAssessmentAgent` instance.
        decision_agent:    :class:`DecisionAgent` instance.
        summary_agent:     :class:`CallSummaryAgent` instance.
        notification_agent::class:`NotificationAgent` instance.
        handoff_agent:     :class:`HumanHandoffAgent` instance.
    """

    def __init__(self) -> None:
        self.caller_classifier = CallerClassificationAgent()
        self.intent_detector = IntentDetectionAgent()
        self.recruitment_agent = RecruitmentAgent()
        self.fraud_detector = FraudDetectionAgent()
        self.risk_assessor = RiskAssessmentAgent()
        self.decision_agent = DecisionAgent()
        self.summary_agent = CallSummaryAgent()
        self.notification_agent = NotificationAgent()
        self.handoff_agent = HumanHandoffAgent()

    # ------------------------------------------------------------------
    # Main pipeline entry point
    # ------------------------------------------------------------------

    async def analyze_call(
        self,
        conversation: list[ConversationTurn],
        call_id: str,
        caller_number: str = "Unknown",
        audio_features: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run the full analysis pipeline and return all results.

        Args:
            conversation:   Ordered list of :class:`ConversationTurn` objects.
            call_id:        UUID string for the call.
            caller_number:  E.164 caller phone number (for handoff context).
            audio_features: Optional dict of raw audio features (spectral,
                            energy, etc.) from the telephony layer.

        Returns:
            Dictionary with keys:
                - ``call_id``              (str)
                - ``caller_result``        (:class:`CallerClassificationResult`)
                - ``intent_result``        (:class:`IntentClassificationResult`)
                - ``fraud_indicators``     (list[:class:`RiskIndicator`])
                - ``recruitment_result``   (:class:`RecruitmentExtractionResult` | None)
                - ``risk_result``          (:class:`RiskAssessmentResult`)
                - ``decision``             (:class:`DecisionResult`)
                - ``summary``              (str)
                - ``notification``         (dict | None)
                - ``handoff_summary``      (:class:`HandoffSummary` | None)
                - ``pipeline_latency_ms``  (int)
        """
        pipeline_start = time.monotonic()
        log = logger.bind(call_id=call_id)
        log.info("pipeline_started", turn_count=len(conversation))

        # -------------------------------------------------------------------
        # Build shared ClassificationInput
        # -------------------------------------------------------------------
        classification_input = ClassificationInput(
            call_id=UUID(call_id),
            conversation=conversation,
            audio_features=audio_features,
        )

        # -------------------------------------------------------------------
        # Stage 1 (parallel): Caller classification + Intent detection
        # -------------------------------------------------------------------
        log.info("stage_1_started", agents=["CallerClassification", "IntentDetection"])
        caller_result, intent_result = await asyncio.gather(
            self.caller_classifier.process(classification_input),
            self.intent_detector.process(classification_input),
        )
        log.info(
            "stage_1_complete",
            caller_type=caller_result.caller_type,
            intent=intent_result.intent,
        )

        # -------------------------------------------------------------------
        # Stage 2 (conditional): Recruitment extraction
        # -------------------------------------------------------------------
        recruitment_result: RecruitmentExtractionResult | None = None
        is_recruitment = intent_result.intent.lower() == "recruitment" or (
            intent_result.secondary_intent is not None
            and intent_result.secondary_intent.lower() == "recruitment"
        )
        if is_recruitment:
            log.info("stage_2_started", agent="RecruitmentAgent")
            recruitment_result = await self.recruitment_agent.process(
                classification_input
            )
            log.info(
                "stage_2_complete",
                company=recruitment_result.company,
                is_legitimate=recruitment_result.is_legitimate,
            )

        # -------------------------------------------------------------------
        # Stage 3: Fraud detection (parallel-safe with Stage 2 but needs
        #          Stage 1 classification_input — already available)
        # -------------------------------------------------------------------
        log.info("stage_3_started", agent="FraudDetection")
        fraud_indicators: list[RiskIndicator] = await self.fraud_detector.process(
            classification_input
        )
        log.info("stage_3_complete", indicator_count=len(fraud_indicators))

        # -------------------------------------------------------------------
        # Stage 4: Risk assessment
        # -------------------------------------------------------------------
        log.info("stage_4_started", agent="RiskAssessment")
        risk_result: RiskAssessmentResult = await self.risk_assessor.process(
            {
                "caller_result": caller_result,
                "intent_result": intent_result,
                "fraud_indicators": fraud_indicators,
                "recruitment_result": recruitment_result,
            }
        )
        log.info(
            "stage_4_complete",
            risk_level=risk_result.risk_level,
            confidence=risk_result.confidence,
        )

        # -------------------------------------------------------------------
        # Stage 5: Decision
        # -------------------------------------------------------------------
        log.info("stage_5_started", agent="Decision")
        decision: DecisionResult = await self.decision_agent.process(
            {
                "caller_result": caller_result,
                "intent_result": intent_result,
                "risk_result": risk_result,
                "recruitment_result": recruitment_result,
                "conversation": conversation,
            }
        )
        log.info("stage_5_complete", decision=decision.decision)

        # -------------------------------------------------------------------
        # Stage 6 (parallel): Summary + Notification + Handoff preparation
        # -------------------------------------------------------------------
        log.info(
            "stage_6_started",
            agents=["CallSummary", "Notification", "HumanHandoff"],
        )

        shared_ctx = {
            "call_id": call_id,
            "caller_number": caller_number,
            "conversation": conversation,
            "caller_result": caller_result,
            "intent_result": intent_result,
            "risk_result": risk_result,
            "recruitment_result": recruitment_result,
            "decision": decision,
        }

        summary, notification, handoff_summary = await asyncio.gather(
            self.summary_agent.process(shared_ctx),
            self.notification_agent.process(shared_ctx),
            self.handoff_agent.process(shared_ctx),
        )
        log.info(
            "stage_6_complete",
            notification_type=notification["type"] if notification else "none",
        )

        # -------------------------------------------------------------------
        # Compute total pipeline latency
        # -------------------------------------------------------------------
        pipeline_latency_ms = int((time.monotonic() - pipeline_start) * 1000)
        log.info(
            "pipeline_complete",
            pipeline_latency_ms=pipeline_latency_ms,
            decision=decision.decision,
            risk_level=risk_result.risk_level,
        )

        return {
            "call_id": call_id,
            "caller_result": caller_result,
            "intent_result": intent_result,
            "fraud_indicators": fraud_indicators,
            "recruitment_result": recruitment_result,
            "risk_result": risk_result,
            "decision": decision,
            "summary": summary,
            "notification": notification,
            "handoff_summary": handoff_summary,
            "pipeline_latency_ms": pipeline_latency_ms,
        }
