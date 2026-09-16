import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_cv import CandidateCV

class CandidateCVRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[CandidateCV]:
        return list(self._db.scalars(
            select(CandidateCV).order_by(CandidateCV.uploaded_at.desc())
        ))

    def get_by_id(self, cv_id: uuid.UUID) -> CandidateCV | None:
        return self._db.scalar(select(CandidateCV).where(CandidateCV.id == cv_id))

    def create(
        self,
        candidate_name: str,
        content: str,
        file_path: str,
        uploaded_by: uuid.UUID,
        embedding: list[float],
    ) -> CandidateCV:
        cv = CandidateCV(
            candidate_name=candidate_name,
            content=content,
            file_path=file_path,
            uploaded_by=uploaded_by,
            embedding=embedding,
        )
        self._db.add(cv)
        self._db.flush()
        return cv
    
    def delete(self, cv: CandidateCV) -> None:
        self._db.delete(cv)