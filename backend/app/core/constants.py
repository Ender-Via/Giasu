from typing import Final


class TutorProfileStatus:
    DRAFT: Final = "Draft"
    PENDING_REVIEW: Final = "PendingReview"
    APPROVED: Final = "Approved"
    REJECTED: Final = "Rejected"

    ALL: Final = (DRAFT, PENDING_REVIEW, APPROVED, REJECTED)
    EDITABLE_EVIDENCE: Final = (DRAFT, REJECTED)


class Availability:
    ACCEPTING: Final = "Accepting"
    FULL: Final = "Full"
    PAUSED: Final = "Paused"

    ALL: Final = (ACCEPTING, FULL, PAUSED)


class VerificationStatus:
    UNVERIFIED: Final = "Unverified"
    PENDING: Final = "Pending"
    VERIFIED: Final = "Verified"
    REJECTED: Final = "Rejected"

    ALL: Final = (UNVERIFIED, PENDING, VERIFIED, REJECTED)


class TeachingMode:
    OFFLINE: Final = "Offline"
    ONLINE: Final = "Online"
    BOTH: Final = "Both"

    ALL: Final = (OFFLINE, ONLINE, BOTH)


EDUCATION_LEVELS: Final = ("Primary", "LowerSecondary", "UpperSecondary", "Other")

ROLE_TUTOR: Final = "Tutor"
ROLE_PARENT: Final = "Parent"
ROLE_ADMIN: Final = "Admin"


class NotificationType:
    MODERATION_RESULT: Final = "ModerationResult"
    NEW_APPLICATION: Final = "NewApplication"
    APPLICATION_STATUS: Final = "ApplicationStatus"
    ROADMAP: Final = "Roadmap"
    SESSION: Final = "Session"
    REQUEST_EXPIRY: Final = "RequestExpiry"
    TUITION: Final = "Tuition"
    PROGRESS: Final = "Progress"
    VIOLATION: Final = "Violation"
    MODERATION_QUEUE: Final = "ModerationQueue"

    ALL: Final = (
        MODERATION_RESULT,
        NEW_APPLICATION,
        APPLICATION_STATUS,
        ROADMAP,
        SESSION,
        REQUEST_EXPIRY,
        TUITION,
        PROGRESS,
        VIOLATION,
        MODERATION_QUEUE,
    )

    BY_ROLE: Final[dict[str, tuple[str, ...]]] = {
        ROLE_TUTOR: (
            MODERATION_RESULT,
            APPLICATION_STATUS,
            ROADMAP,
            SESSION,
            TUITION,
            PROGRESS,
            VIOLATION,
        ),
        ROLE_PARENT: (
            MODERATION_RESULT,
            NEW_APPLICATION,
            ROADMAP,
            SESSION,
            REQUEST_EXPIRY,
            TUITION,
            PROGRESS,
            VIOLATION,
        ),
        ROLE_ADMIN: (
            VIOLATION,
            MODERATION_QUEUE,
        ),
    }
