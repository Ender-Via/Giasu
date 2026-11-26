from typing import Final, Literal

TutorRequestStatusName = Literal["PendingReview", "Rejected", "Recruiting", "Hired", "Closed"]


class TutorRequestStatus:
    PENDING_REVIEW: Final = "PendingReview"
    REJECTED: Final = "Rejected"
    RECRUITING: Final = "Recruiting"
    HIRED: Final = "Hired"
    CLOSED: Final = "Closed"

    ALL: Final = (PENDING_REVIEW, REJECTED, RECRUITING, HIRED, CLOSED)
    EDITABLE: Final = (PENDING_REVIEW, REJECTED, RECRUITING)


class TutorApplicationStatus:
    PENDING: Final = "Pending"
    VIEWED: Final = "Viewed"
    TRIAL_INVITED: Final = "TrialInvited"
    REJECTED: Final = "Rejected"
    NOT_HIRED: Final = "NotHired"

    CLOSE_TRANSITIONS: Final = {PENDING: REJECTED, VIEWED: REJECTED, TRIAL_INVITED: NOT_HIRED}
    OPEN: Final = tuple(CLOSE_TRANSITIONS)
