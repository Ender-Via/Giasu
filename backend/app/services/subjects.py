from app.repositories.subjects import SubjectRepository
from app.schemas.subjects import SubjectResponse


class SubjectService:
    def __init__(self, repository: SubjectRepository) -> None:
        self.repository = repository

    def list_subjects(self) -> list[SubjectResponse]:
        return [
            SubjectResponse(id=s.id, name=s.name, code=s.code) for s in self.repository.list_all()
        ]
