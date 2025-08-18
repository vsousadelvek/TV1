from pydantic import BaseModel
from typing import Optional

class BrokerBase(BaseModel):
    name: str
    email: str
    specialty_region: Optional[str] = None

class Broker(BrokerBase):
    id: int

    class Config:
        from_attributes = True