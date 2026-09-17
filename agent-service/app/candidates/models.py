import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime,  ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.base import Base

class CandidateCV(Base):
    __tablename__ = 'candidate_cv'
    __table_args__ = {'schema': 'documents'}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')
    )
    candidate_name: Mapped[str | None] = mapped_column(String)
    content: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey('auth.users.id')
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
