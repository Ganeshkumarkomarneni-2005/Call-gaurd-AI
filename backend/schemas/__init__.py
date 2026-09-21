"""Schemas package — exposes all Pydantic models from one namespace."""

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
from backend.schemas.call import (
    CallAnalysisResponse,
    CallDetailResponse,
    CallListResponse,
    CallResponse,
    IncomingCallRequest,
    RecruitmentDetailsResponse,
    TranscriptResponse,
    TranscriptSegmentResponse,
    TransferRequest,
)
from backend.schemas.dashboard import (
    DashboardStats,
    NotificationListResponse,
    NotificationResponse,
)
from backend.schemas.user import (
    Token,
    TokenData,
    UserCreate,
    UserLogin,
    UserResponse,
)

__all__ = [
    # user
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenData",
    # call
    "IncomingCallRequest",
    "CallResponse",
    "CallListResponse",
    "TranscriptSegmentResponse",
    "TranscriptResponse",
    "CallAnalysisResponse",
    "RecruitmentDetailsResponse",
    "CallDetailResponse",
    "TransferRequest",
    # dashboard
    "DashboardStats",
    "NotificationResponse",
    "NotificationListResponse",
    # analysis
    "ConversationTurn",
    "ClassificationInput",
    "CallerClassificationResult",
    "IntentClassificationResult",
    "RiskIndicator",
    "RiskAssessmentResult",
    "RecruitmentExtractionResult",
    "DecisionResult",
    "HandoffSummary",
]
