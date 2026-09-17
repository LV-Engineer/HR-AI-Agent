from sqlalchemy.orm import Session

from app.core.embeddings import get_embedding
from app.repositories.job_requirement import JobRequirementRepository
from app.schemas.job_requirement import JobRequirementResponse, JobRequirementSummary

class JobRequirementNotFoundError(Exception):
    pass

class JobRequirementService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._job_requirements = JobRequirementRepository(db)

    def create_job_requirement(self, title: str, content: str) -> JobRequirementResponse:
        embedding = get_embedding(content)
        job_requirement = self._job_requirements.create(title=title, content=content, embedding=embedding)
        self._db.commit()
        return JobRequirementResponse.model_validate(job_requirement)

    def list_job_requirements(self) -> list[JobRequirementSummary]:
        job_requirements = self._job_requirements.list_all()
        return [JobRequirementSummary.model_validate(jr) for jr in job_requirements]

    def get_job_requirement(self, job_requirement_id: int) -> JobRequirementResponse:
        job_requirement = self._job_requirements.get_by_id(job_requirement_id)
        if job_requirement is None:
            raise JobRequirementNotFoundError()
        return JobRequirementResponse.model_validate(job_requirement)

    def update_job_requirement(
        self, job_requirement_id: int, title: str | None, content: str | None
    ) -> JobRequirementResponse:
        job_requirement = self._job_requirements.get_by_id(job_requirement_id)
        if job_requirement is None:
            raise JobRequirementNotFoundError()
        embedding = get_embedding(content) if content is not None else None
        updated = self._job_requirements.update(job_requirement, title=title, content=content, embedding=embedding)
        self._db.commit()
        return JobRequirementResponse.model_validate(updated)

    def delete_job_requirement(self, job_requirement_id: int) -> None:
        job_requirement = self._job_requirements.get_by_id(job_requirement_id)
        if job_requirement is None:
            raise JobRequirementNotFoundError()
        self._job_requirements.delete(job_requirement)
        self._db.commit()