from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_requirement import JobRequirement

class JobRequirementRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[JobRequirement]:
        return list(self._db.scalars(
            select(JobRequirement).order_by(JobRequirement.created_at.desc())
        ))

    def get_by_id(self, job_requirement: int) -> JobRequirement | None:
        return self._db.scalar(select(JobRequirement).where(JobRequirement.id == job_requirement))

    def create(self, title: str, content: str, embedding: list[float]) -> JobRequirement:
        job_requirement = JobRequirement(title=title, content=content, embedding=embedding)
        self._db.add(job_requirement)
        self._db.flush()
        return job_requirement

    def update(
        self,
        job_requirement: JobRequirement,
        title: str | None,
        content: str | None,
        embedding: list[float] | None,
    ) -> JobRequirement:
        if title is not None:
            job_requirement.title = title
        if content is not None:
            job_requirement.content = content
        if embedding is not None:
            job_requirement.embedding = embedding
        self._db.flush()
        return job_requirement

    def delete(self, job_requirement: JobRequirement) -> None:
        self._db.delete(job_requirement)