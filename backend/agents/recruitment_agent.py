"""Recruitment Agent.

Extracts structured recruitment details from a conversation and assesses
whether the recruitment call appears legitimate or fraudulent.

Key responsibility — distinguish:
    * Legitimate AI recruitment calls (normal, notify user only)
    * Recruitment fraud (payment requests, data harvesting, deception)

IMPORTANT: A call is NOT fraudulent merely because the caller is an AI.
           Fraud classification is based on *content*, not caller type.

In mock/rule-based mode the agent uses regex patterns and keyword matching.
A trained NER model can be plugged in via :meth:`_ml_extract`.
"""

from __future__ import annotations

import re
from typing import Any

from backend.agents.base import BaseAgent
from backend.schemas.analysis import ClassificationInput, RecruitmentExtractionResult

# ---------------------------------------------------------------------------
# Extraction patterns
# ---------------------------------------------------------------------------

# Company name — looks for "from <Company>", "calling from <Company>", etc.
_COMPANY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:from|at|with|representing)\s+([A-Z][A-Za-z0-9\s&\-\.]{1,48}?)(?:\.|,|\s+(?:and|for|to|about|regarding|here)\b)", re.M),
    re.compile(r"\bI(?:'m| am)\s+(?:calling|reaching out)\s+(?:from|on behalf of)\s+([A-Z][A-Za-z0-9\s&\-\.]{1,48}?)(?:\.|,|\s)", re.M),
    re.compile(r"\bour company(?:\s+name)?\s+is\s+([A-Z][A-Za-z0-9\s&\-\.]{1,48}?)(?:\.|,|\s)", re.I),
]

# Recruiter / person name
_RECRUITER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bmy name(?:\s+is)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", re.M),
    re.compile(r"\bI(?:'m| am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:calling|from|reaching)\b", re.M),
    re.compile(r"\bspeaking with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", re.M),
]

# Position / role
_POSITION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:for|regarding|about)\s+(?:the\s+)?(?:position|role|opening|vacancy|post)\s+of\s+([A-Za-z\s\-\.]{2,50}?)(?:\.|,|at|\b)", re.I),
    re.compile(r"\b([A-Za-z\s\-\.]{2,40}?)\s+(?:position|role|opening|vacancy|post)\b", re.I),
    re.compile(r"\b(?:hire|hiring|recruit|looking)\s+(?:a|an|for)?\s+([A-Za-z\s\-\.]{2,40}?)\b", re.I),
]

# Interview date
_DATE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b((?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
        r"|(?:\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})"
        r"|(?:\d{1,2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
        r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+\d{4})?)"
        r")\b",
        re.I,
    )
]

# Interview time
_TIME_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)|noon|midnight)\b", re.I),
]

# Interview stage keywords
_STAGE_MAP: dict[str, str] = {
    "initial": "initial",
    "first round": "initial",
    "technical": "technical",
    "coding": "technical",
    "hr": "hr",
    "human resource": "hr",
    "final": "final",
    "management": "final",
    "director": "final",
}

# Red-flag patterns — indicate potential fraud
_FRAUD_FLAGS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(registration|joining|training|processing|onboarding)\s+fee\b", re.I), "Registration or training fee requested"),
    (re.compile(r"\bpay\s+(?:for|before|to\s+start|to\s+proceed)\b", re.I), "Payment required to proceed"),
    (re.compile(r"\bsend\s+(?:money|funds|cash|payment)\b", re.I), "Money transfer requested"),
    (re.compile(r"\bdeposit\s+(?:amount|money|fee)\b", re.I), "Deposit requested"),
    (re.compile(r"\badvance\s+(?:fee|payment|amount)\b", re.I), "Advance fee requested"),
    (re.compile(r"\b(?:urgent|immediately|right now|within\s+\d+\s+hours?|today only)\b", re.I), "Excessive urgency detected"),
    (re.compile(r"\b(?:aadhar|pan card|passport number|national id|ssn)\b", re.I), "Sensitive PII requested"),
    (re.compile(r"\b(?:click this link|download|whatsapp|telegram)\b", re.I), "Redirect to external platform"),
]

# Positive legitimacy signals
_LEGIT_SIGNALS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:no\s+charge|free\s+of\s+cost|no\s+fee|no\s+payment\s+required)\b", re.I),
    re.compile(r"\bofficial\s+(?:email|portal|website)\b", re.I),
    re.compile(r"\bverify\s+(?:on\s+our\s+website|through\s+linkedin|on\s+our\s+portal)\b", re.I),
]


class RecruitmentAgent(BaseAgent):
    """Extract recruitment details and assess call legitimacy.

    Uses regex and keyword matching in mock/rule-based mode.  Designed to
    be replaced by an NER + classification model via :meth:`_ml_extract`.

    Attributes:
        agent_name:    Identifier surfaced in logs.
        model_version: Semantic version of the extraction rules.
    """

    agent_name: str = "RecruitmentAgent"
    model_version: str = "v1.0-regex"

    def __init__(self) -> None:
        super().__init__()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process(
        self, input_data: ClassificationInput
    ) -> RecruitmentExtractionResult:
        """Extract recruitment details from the conversation.

        Args:
            input_data: :class:`ClassificationInput` with call UUID and turns.

        Returns:
            :class:`RecruitmentExtractionResult` with extracted fields and
            legitimacy assessment.
        """
        self._log_event(
            "recruitment_extraction_started",
            call_id=str(input_data.call_id),
        )

        # Try ML hook first
        ml_result = self._ml_extract(input_data)
        if ml_result is not None:
            return ml_result

        full_text = self._build_full_text(input_data.conversation)
        caller_text = self._build_caller_text(input_data.conversation)

        company = self._extract_company(full_text)
        recruiter_name = self._extract_recruiter_name(full_text)
        position = self._extract_position(full_text)
        interview_stage = self._extract_interview_stage(caller_text)
        interview_date = self._extract_date(full_text)
        interview_time = self._extract_time(full_text)
        next_step = self._infer_next_step(caller_text, position, interview_date)

        is_legitimate, legitimacy_reason = self._assess_legitimacy(caller_text, company)

        # Confidence in extraction correlates with how many fields we found
        populated = sum(
            1
            for v in [company, recruiter_name, position, interview_stage]
            if v is not None
        )
        extraction_confidence = round(0.30 + populated * 0.15, 4)

        result = RecruitmentExtractionResult(
            company=company,
            recruiter_name=recruiter_name,
            position=position,
            interview_stage=interview_stage,
            interview_date=interview_date,
            interview_time=interview_time,
            next_step=next_step,
            is_legitimate=is_legitimate,
            legitimacy_reason=legitimacy_reason,
            confidence=min(extraction_confidence, 1.0),
        )

        self._log_event(
            "recruitment_extraction_complete",
            call_id=str(input_data.call_id),
            company=company,
            position=position,
            is_legitimate=is_legitimate,
        )
        return result

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------

    def _build_full_text(self, conversation: list[Any]) -> str:
        """Combine all speaker turns (agent + caller) for context extraction."""
        return " ".join(t.text.strip() for t in conversation)

    def _build_caller_text(self, conversation: list[Any]) -> str:
        """Combine caller-only turns for fraud-signal analysis."""
        return " ".join(
            t.text.strip()
            for t in conversation
            if t.speaker.lower() == "caller"
        )

    # ------------------------------------------------------------------
    # Field extractors
    # ------------------------------------------------------------------

    def _extract_company(self, text: str) -> str | None:
        for pattern in _COMPANY_PATTERNS:
            m = pattern.search(text)
            if m:
                name = m.group(1).strip().rstrip(".,")
                if 2 <= len(name) <= 60:
                    return name
        return None

    def _extract_recruiter_name(self, text: str) -> str | None:
        for pattern in _RECRUITER_PATTERNS:
            m = pattern.search(text)
            if m:
                name = m.group(1).strip()
                # Reject common false positives
                if name.lower() not in {"an", "the", "a", "calling", "reaching"}:
                    return name
        return None

    def _extract_position(self, text: str) -> str | None:
        for pattern in _POSITION_PATTERNS:
            m = pattern.search(text)
            if m:
                pos = m.group(1).strip().rstrip(".,").strip()
                if 2 <= len(pos) <= 60:
                    return pos
        return None

    def _extract_interview_stage(self, text: str) -> str | None:
        lower = text.lower()
        for keyword, stage in _STAGE_MAP.items():
            if keyword in lower:
                return stage
        return None

    def _extract_date(self, text: str) -> str | None:
        for pattern in _DATE_PATTERNS:
            m = pattern.search(text)
            if m:
                return m.group(1).strip()
        return None

    def _extract_time(self, text: str) -> str | None:
        for pattern in _TIME_PATTERNS:
            m = pattern.search(text)
            if m:
                return m.group(1).strip()
        return None

    def _infer_next_step(
        self,
        caller_text: str,
        position: str | None,
        interview_date: str | None,
    ) -> str | None:
        """Infer the next recruitment step from context."""
        lower = caller_text.lower()
        if "send your cv" in lower or "email your resume" in lower:
            return "Candidate asked to submit CV/resume"
        if interview_date:
            pos_str = f" for the {position} role" if position else ""
            return f"Interview scheduled{pos_str} on {interview_date}"
        if "we will call" in lower or "we'll call you" in lower:
            return "Recruiter will follow up with another call"
        if "send us your details" in lower:
            return "Candidate asked to share details"
        return None

    # ------------------------------------------------------------------
    # Legitimacy assessment
    # ------------------------------------------------------------------

    def _assess_legitimacy(
        self, caller_text: str, company: str | None
    ) -> tuple[bool, str]:
        """Assess whether the recruitment call appears legitimate.

        IMPORTANT: An AI-sourced call is NOT fraudulent by nature.  Fraud
        determination is based exclusively on *content* red flags.

        Args:
            caller_text: Caller-only text for red-flag scanning.
            company:     Extracted company name (None if not found).

        Returns:
            Tuple of (is_legitimate: bool, reason: str).
        """
        flags: list[str] = []
        for pattern, description in _FRAUD_FLAGS:
            if pattern.search(caller_text):
                flags.append(description)

        legit_signals: list[str] = []
        for pattern in _LEGIT_SIGNALS:
            if pattern.search(caller_text):
                legit_signals.append("Positive legitimacy signal detected")

        if flags:
            reason = (
                "Potential fraud indicators detected: "
                + "; ".join(flags)
                + ". Legitimate recruiters do not charge candidates."
            )
            return False, reason

        if company:
            return True, f"Clear company identity ({company!r}) with no suspicious payment requests"
        return True, "No fraud indicators detected; standard recruitment flow"

    # ------------------------------------------------------------------
    # ML extension point
    # ------------------------------------------------------------------

    def _ml_extract(
        self, input_data: ClassificationInput
    ) -> RecruitmentExtractionResult | None:
        """Hook for plugging in a trained NER / classification model.

        Leverages `recruitment_detector_v1.0.0.joblib` and `recruitment_legitimacy_v1.0.0.joblib`
        when available to classify recruitment relevance and legitimacy.
        """
        try:
            import joblib
            from pathlib import Path

            s1_path = Path("ml/models/recruitment_detector_v1.0.0.joblib")
            s2_path = Path("ml/models/recruitment_legitimacy_v1.0.0.joblib")

            if not s1_path.exists() or not s2_path.exists():
                return None

            s1_bundle = joblib.load(s1_path)
            s2_bundle = joblib.load(s2_path)

            v1, m1 = s1_bundle.get("vectorizer"), s1_bundle.get("model")
            v2, m2 = s2_bundle.get("vectorizer"), s2_bundle.get("model")

            if not v1 or not m1 or not v2 or not m2:
                return None

            caller_text = self._build_caller_text(input_data.conversation)
            full_text = self._build_full_text(input_data.conversation)
            eval_text = caller_text if caller_text.strip() else full_text
            if not eval_text.strip():
                return None

            # Stage 1: Recruitment vs Non-recruitment
            X1 = v1.transform([eval_text])
            is_recruitment = bool(m1.predict(X1)[0])

            if not is_recruitment:
                return None

            # Stage 2: Legitimate vs Fraudulent Recruitment
            X2 = v2.transform([eval_text])
            is_legit = bool(m2.predict(X2)[0])

            # Extract entities using rule-based/regex helpers
            company = self._extract_company(full_text)
            recruiter_name = self._extract_recruiter(full_text)
            position = self._extract_position(full_text)
            interview_date = self._extract_date(full_text)
            interview_time = self._extract_time(full_text)
            interview_stage = self._extract_stage(full_text)
            next_step = self._infer_next_step(caller_text, position, interview_date)

            if is_legit:
                reason = "ML Verified: Authentic recruitment communication pattern detected"
            else:
                reason = "ML Alert: Fraudulent recruitment markers or advance fee pattern detected"

            return RecruitmentExtractionResult(
                company=company,
                recruiter_name=recruiter_name,
                position=position,
                interview_stage=interview_stage,
                interview_date=interview_date,
                interview_time=interview_time,
                next_step=next_step,
                is_legitimate=is_legit,
                legitimacy_reason=reason,
                confidence=0.98,
                model_version="v1.0.0-hierarchical_lr",
            )
        except Exception:
            return None

