import uuid

from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    conversation_id: uuid.UUID | None = None