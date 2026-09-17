from datetime import datetime

from pydantic import BaseModel, ConfigDict

class JobRequirementCreateRequest(BaseModel):
    title: str
    content: str

class JobRequirementSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime

class JobRequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime

class JobRequirementUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None