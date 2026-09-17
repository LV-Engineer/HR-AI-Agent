import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.embeddings import get_embedding
from app.core.text_extraction import extract_text
from app.candidates.repositories import CandidateCVRepository
from app.candidates.schemas import CandidateCVResponse

CV_DIR = Path(settings.cv_storage_dir)
CV_DIR.mkdir(parents=True, exist_ok=True)

class UnsupportedFileTypeError(Exception):
    pass

class CandidateCVNotFoundError(Exception):
    pass

class CandidateService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._cvs = CandidateCVRepository(db)

    def list_cvs(self) -> list[CandidateCVResponse]:
        cvs = self._cvs.list_all()
        return [CandidateCVResponse.model_validate(cv) for cv in cvs]

    def get_cv_file(self, cv_id: uuid.UUID) -> tuple[Path, str]:
        cv = self._cvs.get_by_id(cv_id)
        if cv is None:
            raise CandidateCVNotFoundError()
        return Path(cv.file_path), cv.candidate_name or 'cv'

    def upload_cv(
        self,
        candidate_name: str,
        filename: str,
        file_bytes: bytes,
        uploaded_by: uuid.UUID,
    ) -> CandidateCVResponse:
        if not filename.lower().endswith('.pdf'):
            raise UnsupportedFileTypeError()

        content = extract_text(file_bytes)
        embedding = get_embedding(content)

        stored_path = CV_DIR / f'{uuid.uuid4()}.pdf'
        stored_path.write_bytes(file_bytes)

        cv = self._cvs.create(
            candidate_name=candidate_name,
            content=content,
            file_path=str(stored_path),
            uploaded_by=uploaded_by,
            embedding=embedding,
        )
        self._db.commit()
        return CandidateCVResponse.model_validate(cv)

    def delete_cv(self, cv_id: uuid.UUID) -> None:
        cv = self._cvs.get_by_id(cv_id)
        if cv is None:
            raise CandidateCVNotFoundError()
        file_path = Path(cv.file_path)
        self._cvs.delete(cv)
        self._db.commit()
        file_path.unlink(missing_ok=True)
