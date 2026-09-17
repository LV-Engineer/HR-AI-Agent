import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.embeddings import get_embedding
from app.core.text_extraction import extract_text
from app.policies.repositories import HrPolicyRepository
from app.policies.schemas import HrPolicyResponse

POLICY_DIR = Path(settings.policy_storage_dir)
POLICY_DIR.mkdir(parents=True, exist_ok=True)

class UnsupportedFileTypeError(Exception):
    pass

class HrPolicyNotFoundError(Exception):
    pass

class PolicyService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._policies = HrPolicyRepository(db)

    def upload_policy(self, title: str, filename: str, file_bytes: bytes) -> HrPolicyResponse:
        if not filename.lower().endswith('.pdf'):
            raise UnsupportedFileTypeError()

        content = extract_text(file_bytes)
        embedding = get_embedding(content)

        stored_path = POLICY_DIR / f'{uuid.uuid4()}.pdf'
        stored_path.write_bytes(file_bytes)

        policy = self._policies.create(
            title=title, content=content, file_path=str(stored_path), embedding=embedding,
        )
        self._db.commit()
        return HrPolicyResponse.model_validate(policy)

    def list_policies(self) -> list[HrPolicyResponse]:
        policies = self._policies.list_all()
        return [HrPolicyResponse.model_validate(p) for p in policies]

    def get_policy_file(self, policy_id: int) -> tuple[Path, str]:
        policy = self._policies.get_by_id(policy_id)
        if policy is None or policy.file_path is None:
            raise HrPolicyNotFoundError()
        return Path(policy.file_path), policy.title

    def delete_policy(self, policy_id: int) -> None:
        policy = self._policies.get_by_id(policy_id)
        if policy is None:
            raise HrPolicyNotFoundError()
        file_path = Path(policy.file_path) if policy.file_path else None
        self._policies.delete(policy)
        self._db.commit()
        if file_path is not None:
            file_path.unlink(missing_ok=True)
