"""Agents package — exposes all agent classes and the pipeline."""

from backend.agents.base import BaseAgent
from backend.agents.call_summary_agent import CallSummaryAgent
from backend.agents.caller_classification_agent import CallerClassificationAgent
from backend.agents.decision_agent import DecisionAgent
from backend.agents.fraud_detection_agent import FraudDetectionAgent
from backend.agents.human_handoff_agent import HumanHandoffAgent
from backend.agents.intent_detection_agent import IntentDetectionAgent
from backend.agents.notification_agent import NotificationAgent
from backend.agents.pipeline import CallAnalysisPipeline
from backend.agents.recruitment_agent import RecruitmentAgent
from backend.agents.risk_assessment_agent import RiskAssessmentAgent

__all__ = [
    "BaseAgent",
    "CallerClassificationAgent",
    "IntentDetectionAgent",
    "RecruitmentAgent",
    "FraudDetectionAgent",
    "RiskAssessmentAgent",
    "DecisionAgent",
    "CallSummaryAgent",
    "NotificationAgent",
    "HumanHandoffAgent",
    "CallAnalysisPipeline",
]
