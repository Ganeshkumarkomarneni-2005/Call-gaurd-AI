"""Simulation service for CallGuard AI.

Creates realistic multi-turn call scenarios (AI recruitment, human recruitment,
recruitment fraud, OTP banking scam, promotional robocall) and executes the full
9-agent AI analysis pipeline to populate transcripts, call analysis,
recruitment intelligence, and notifications.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.pipeline import CallAnalysisPipeline
from backend.db.models import Call, CallAnalysis, Notification, RecruitmentDetails, Transcript, TranscriptSegment
from backend.schemas.analysis import ConversationTurn
from backend.utils.time_utils import now_utc

logger = structlog.get_logger(component="SimulationService")

# ─── Demo Scenarios ────────────────────────────────────────────────────────────

SCENARIOS: dict[str, dict[str, Any]] = {
    "ai_recruiter": {
        "title": "AI Recruitment Assistant (ABC Technologies)",
        "caller_number": "+919876543210",
        "virtual_number": "+918001234567",
        "turns": [
            ("CALLER", "Hello! I am Arya, an automated recruitment assistant calling from ABC Technologies.", 0, 3500),
            ("AGENT", "Hello. Could you please confirm which role and candidate you are calling about?", 3800, 7000),
            ("CALLER", "We reviewed your application for the Senior Data Analyst position and were very impressed with your background.", 7500, 13000),
            ("AGENT", "Great! What are the next steps in the interview process?", 13500, 16500),
            ("CALLER", "We would like to schedule a 45-minute technical discussion with our Engineering Director for this Thursday at 3:00 PM. No fees or payments are ever requested. Would this time work for you?", 17000, 26000),
            ("AGENT", "Yes, Thursday at 3:00 PM works. Please send the meeting invite to my registered email.", 26500, 30500),
            ("CALLER", "Wonderful! I have scheduled the interview and sent the confirmation link. Thank you and have a great day!", 31000, 36000),
        ],
    },
    "human_recruiter": {
        "title": "Human HR Recruiter (Acme Global)",
        "caller_number": "+919812345678",
        "virtual_number": "+918001234567",
        "turns": [
            ("CALLER", "Hi, good morning! This is Priya from Acme Global HR team. Am I speaking with the candidate for the Cloud Engineer opening?", 0, 5000),
            ("AGENT", "Hi Priya, yes, please go ahead.", 5500, 7500),
            ("CALLER", "Awesome! We loved your profile and experience with distributed backend systems. We'd love to invite you for an initial round on Friday at 11:00 AM.", 8000, 16000),
            ("AGENT", "Sounds good, Friday at 11:00 AM is noted. Who will be conducting the interview?", 16500, 20500),
            ("CALLER", "Our Lead DevOps Architect, Rahul, will be on the call. I will share the calendar invite shortly. Thank you!", 21000, 27000),
        ],
    },
    "recruitment_fraud": {
        "title": "Job Offer Scam Demanding ₹5,000 Fee",
        "caller_number": "+919100012345",
        "virtual_number": "+918001234567",
        "turns": [
            ("CALLER", "Congratulations! You have been directly selected for the Executive Assistant position at Global Apex Tech Corp with a package of 12 LPA.", 0, 7000),
            ("AGENT", "I don't recall interviewing for this position. Could you clarify the process?", 7500, 12000),
            ("CALLER", "Your resume was shortlisted from the job portal. To issue your formal appointment letter and security ID badge, you must pay a mandatory registration fee of ₹5,000 immediately via UPI.", 12500, 23000),
            ("AGENT", "Why is a payment required before joining?", 23500, 26000),
            ("CALLER", "This is a strictly refundable security deposit. You must transfer the ₹5,000 to our UPI ID within the next 30 minutes, or your selection will be immediately canceled and assigned to another candidate!", 26500, 38000),
        ],
    },
    "otp_fraud": {
        "title": "Banking Impersonation & OTP Fraud",
        "caller_number": "+919000099999",
        "virtual_number": "+918001234567",
        "turns": [
            ("CALLER", "Emergency security alert from your Bank Fraud Prevention Department. We have detected an unauthorized debit attempt of ₹45,000 on your account.", 0, 7500),
            ("AGENT", "Which account is this regarding?", 8000, 10000),
            ("CALLER", "Your primary savings account. We have temporarily placed a hold. To cancel this fraudulent transaction and unfreeze your funds, please immediately read out the 6-digit OTP just sent to your phone.", 10500, 21000),
            ("AGENT", "The SMS explicitly says not to share OTP with anyone, including bank officials.", 21500, 26500),
            ("CALLER", "Sir, I am the senior security manager. If you do not provide the OTP within 60 seconds, your account will be permanently blocked and penalty charges will apply!", 27000, 36000),
        ],
    },
    "promotional": {
        "title": "Promotional Loan Robocall",
        "caller_number": "+919777788888",
        "virtual_number": "+918001234567",
        "turns": [
            ("CALLER", "Congratulations! You have been pre-approved for an instant personal loan of up to ₹15 Lakhs at a special promotional rate of 8.5% with zero processing fee.", 0, 9000),
            ("CALLER", "This is a limited period offer valid only for today. Press 1 to speak with our loan executive, or press 9 to opt out.", 9500, 17000),
        ],
    },
}


class SimulationService:
    """Service to generate and run realistic simulated calls."""

    def __init__(self) -> None:
        self.pipeline = CallAnalysisPipeline()

    async def simulate_call(
        self,
        db: AsyncSession,
        scenario_key: str = "ai_recruiter",
        user_id: Optional[UUID] = None,
        custom_caller: Optional[str] = None,
    ) -> Call:
        """Run an end-to-end simulated call and persist all artifacts.

        Args:
            db: Async database session.
            scenario_key: One of the predefined scenario keys.
            user_id: The owning user UUID.
            custom_caller: Optional custom caller phone number.

        Returns:
            The fully populated :class:`Call` ORM model.
        """
        scenario = SCENARIOS.get(scenario_key, SCENARIOS["ai_recruiter"])
        caller_number = custom_caller or scenario["caller_number"]
        virtual_number = scenario["virtual_number"]
        turns_data = scenario["turns"]

        # 1. Create Call Record
        call = Call(
            user_id=user_id,
            status="ended",
            caller_number=caller_number,
            caller_name=scenario["title"],
            virtual_number=virtual_number,
            telephony_call_id=f"sim-{uuid4().hex[:12]}",
            telephony_provider="mock",
            started_at=now_utc(),
            ended_at=now_utc(),
            duration_seconds=turns_data[-1][3] // 1000 if turns_data else 30,
        )
        db.add(call)
        await db.flush()

        # 2. Build Conversation Turns for AI Pipeline & Transcript
        conversation_turns: list[ConversationTurn] = []
        transcript_text_parts: list[str] = []

        transcript = Transcript(
            call_id=call.id,
            full_text="",
            summary="",
            word_count=0,
        )
        db.add(transcript)
        await db.flush()

        for idx, (speaker, text, start_ms, end_ms) in enumerate(turns_data):
            turn = ConversationTurn(
                speaker=speaker.lower(),
                text=text,
                timestamp_ms=start_ms,
            )
            conversation_turns.append(turn)
            transcript_text_parts.append(f"{speaker}: {text}")

            segment = TranscriptSegment(
                transcript_id=transcript.id,
                speaker=speaker,
                text=text,
                start_ms=start_ms,
                end_ms=end_ms,
                confidence=0.98,
            )
            db.add(segment)

        full_text = "\n".join(transcript_text_parts)
        transcript.full_text = full_text
        transcript.word_count = len(full_text.split())

        # 3. Run full 9-Agent AI Analysis Pipeline
        analysis_result = await self.pipeline.analyze_call(
            conversation=conversation_turns,
            call_id=str(call.id),
            caller_number=caller_number,
        )

        transcript.summary = analysis_result.get("summary") or "Call handled by CallGuard AI."

        # 4. Persist CallAnalysis
        caller_res = analysis_result["caller_result"]
        intent_res = analysis_result["intent_result"]
        risk_res = analysis_result["risk_result"]
        decision_res = analysis_result["decision"]
        fraud_indicators = analysis_result["fraud_indicators"]

        risk_indicator_texts = [
            f"{ind.category}: {ind.evidence}" if hasattr(ind, "category") else str(ind)
            for ind in fraud_indicators
        ]

        analysis = CallAnalysis(
            call_id=call.id,
            caller_type=caller_res.caller_type.lower() if hasattr(caller_res, "caller_type") else "unknown",
            caller_type_confidence=getattr(caller_res, "confidence", 0.9),
            intent=intent_res.intent if hasattr(intent_res, "intent") else "UNKNOWN",
            secondary_intent=getattr(intent_res, "secondary_intent", None),
            intent_confidence=getattr(intent_res, "confidence", 0.9),
            risk_level=risk_res.risk_level.lower() if hasattr(risk_res, "risk_level") else "low",
            risk_confidence=getattr(risk_res, "confidence", 0.95),
            risk_indicators=json.dumps(risk_indicator_texts),
            decision=decision_res.decision.lower() if hasattr(decision_res, "decision") else "ai_handle",
            decision_reason=getattr(decision_res, "reason", "Policy matched."),
            decision_confidence=getattr(decision_res, "confidence", 0.9),
            analysis_latency_ms=analysis_result.get("pipeline_latency_ms", 120),
        )
        db.add(analysis)

        # 5. Persist Recruitment Details if present
        rec_res = analysis_result.get("recruitment_result")
        if rec_res and (getattr(rec_res, "company", None) or getattr(rec_res, "position", None)):
            rec_details = RecruitmentDetails(
                call_id=call.id,
                company=getattr(rec_res, "company", None),
                recruiter_name=getattr(rec_res, "recruiter_name", None),
                position=getattr(rec_res, "position", None),
                interview_stage=getattr(rec_res, "interview_stage", None),
                interview_date=getattr(rec_res, "interview_date", None),
                interview_time=getattr(rec_res, "interview_time", None),
                next_step=getattr(rec_res, "next_step", None),
                is_legitimate=getattr(rec_res, "is_legitimate", True),
                legitimacy_reason=getattr(rec_res, "legitimacy_reason", None),
            )
            db.add(rec_details)

        # 6. Persist Notification if generated
        notif_dict = analysis_result.get("notification")
        if notif_dict and user_id is not None:
            notification = Notification(
                user_id=user_id,
                call_id=call.id,
                notification_type=notif_dict.get("type", "CALL_ANALYZED"),
                title=notif_dict.get("title", f"Call from {caller_number}"),
                body=notif_dict.get("body", transcript.summary),
                read=False,
            )
            db.add(notification)
        elif user_id is not None:
            # Create a default informational notification
            notification = Notification(
                user_id=user_id,
                call_id=call.id,
                notification_type="CALL_COMPLETED",
                title=f"Call from {caller_number}",
                body=transcript.summary or "Call completed and analyzed.",
                read=False,
            )
            db.add(notification)

        await db.commit()
        await db.refresh(call)

        logger.info(
            "simulated_call_completed",
            call_id=str(call.id),
            scenario=scenario_key,
            decision=analysis.decision,
            risk=analysis.risk_level,
        )
        return call


simulation_service = SimulationService()
