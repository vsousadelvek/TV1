from .broker import Broker as BrokerSchema
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Schema base com todos os campos que podem ser fornecidos
class LeadBase(BaseModel):
    phone_number: str
    location: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    parking_spots: Optional[int] = None
    min_area_sqm: Optional[int] = None
    investment_range: Optional[str] = None
    move_in_deadline: Optional[str] = None
    payment_method: Optional[str] = None
    broker: Optional[BrokerSchema] = None
    handoff_at: Optional[datetime] = None
    created_at: datetime

# Schema para criação
class LeadCreate(BaseModel):
    phone_number: str

# Schema para atualização
class LeadUpdate(BaseModel):
    location: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    parking_spots: Optional[int] = None
    min_area_sqm: Optional[int] = None
    investment_range: Optional[str] = None
    move_in_deadline: Optional[str] = None
    payment_method: Optional[str] = None
    status: Optional[str] = None
    intent_level: Optional[str] = None

# Schema para leitura (o que a API retorna)
class Lead(LeadBase):
    id: int
    status: str
    intent_level: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True