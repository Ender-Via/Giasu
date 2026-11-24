from typing import Literal
from uuid import UUID

from pydantic import BaseModel

RoleName = Literal["Admin", "Tutor", "Parent"]


class CurrentUserResponse(BaseModel):
    userId: UUID
    fullName: str
    role: RoleName
