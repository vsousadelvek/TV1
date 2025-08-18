from pydantic import BaseModel
from datetime import datetime

class FollowUpBase(BaseModel):
    scheduled_for: datetime
    message_template: str

class FollowUpCreate(FollowUpBase):
    pass

class FollowUp(FollowUpBase):
    id: int
    lead_id: int
    status: str

    class Config:
        from_attributes = True