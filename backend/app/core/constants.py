from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    HSE_MANAGER = "HSE_MANAGER"
    HSE_ANALYST = "HSE_ANALYST"
    REVIEWER = "REVIEWER"
    VIEWER = "VIEWER"


class ReportType(StrEnum):
    UNSAFE_ACT = "UNSAFE_ACT"
    UNSAFE_CONDITION = "UNSAFE_CONDITION"
    NEAR_MISS = "NEAR_MISS"
    INCIDENT = "INCIDENT"


class SourceType(StrEnum):
    PUBLIC = "PUBLIC"
    SYNTHETIC = "SYNTHETIC"
    USER_SUBMITTED = "USER_SUBMITTED"
    IMPORTED = "IMPORTED"


class ReportStatus(StrEnum):
    NEW = "NEW"
    ANALYZED = "ANALYZED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REVIEWED = "REVIEWED"
    CLOSED = "CLOSED"


class SIFLevel(StrEnum):
    NON_SIF = "NON_SIF"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    REVIEW = "REVIEW"


class BarrierStatus(StrEnum):
    EFFECTIVE = "EFFECTIVE"
    FAILED = "FAILED"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


class ReviewDecision(StrEnum):
    PENDING = "PENDING"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    MODIFY = "MODIFY"
