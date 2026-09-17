import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    content: str
    created_at: datetime

class QueryRequest(BaseModel):
    question: str
    conversation_id: uuid.UUID | None = None
