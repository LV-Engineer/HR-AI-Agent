import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

class CandidateCVResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_name: str
    uploaded_at: datetime
