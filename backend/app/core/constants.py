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
