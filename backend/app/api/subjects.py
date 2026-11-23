from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.repositories.subjects import SubjectRepository
from app.schemas.auth import CurrentUserResponse
from app.schemas.common import ApiResponse
from app.schemas.subjects import SubjectResponse
from app.services.subjects import SubjectService

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])


@router.get("", response_model=ApiResponse[list[SubjectResponse]])
def list_subjects(
    current_user: Annotated[CurrentUserResponse, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[list[SubjectResponse]]:
    del current_user
    subjects = SubjectService(SubjectRepository(db)).list_subjects()
    return ApiResponse[list[SubjectResponse]].ok(subjects)
