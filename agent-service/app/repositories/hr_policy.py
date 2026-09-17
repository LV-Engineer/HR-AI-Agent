from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hr_policy import HrPolicy

class HrPolicyRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[HrPolicy]:
        return list(self._db.scalars(
            select(HrPolicy).order_by(HrPolicy.created_at.desc())
        ))

    def get_by_id(self, policy_id: int) -> HrPolicy | None:
        return self._db.scalar(select(HrPolicy).where(HrPolicy.id == policy_id))

    def create(self, title: str, content: str, file_path: str, embedding: list[float]) -> HrPolicy:
        policy = HrPolicy(title=title, content=content, file_path=file_path, embedding=embedding)
        self._db.add(policy)
        self._db.flush()
        return policy

    def delete(self, policy: HrPolicy) -> None:
        self._db.delete(policy)