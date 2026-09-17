from datetime import datetime

from pydantic import BaseModel, ConfigDict

class ReportSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filename: str
    created_at: datetime
