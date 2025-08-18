import datetime

from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base



class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # Campos de Qualificação
    location: Mapped[str] = mapped_column(String, nullable=True)
    property_type: Mapped[str] = mapped_column(String, nullable=True)
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=True)
    parking_spots: Mapped[int] = mapped_column(Integer, nullable=True)
    min_area_sqm: Mapped[int] = mapped_column(Integer, nullable=True)
    investment_range: Mapped[str] = mapped_column(String, nullable=True)
    move_in_deadline: Mapped[str] = mapped_column(String, nullable=True)
    payment_method: Mapped[str] = mapped_column(String, nullable=True)

    # Campos de Controle
    status: Mapped[str] = mapped_column(String, default="new")
    intent_level: Mapped[str] = mapped_column(String, nullable=True)
    broker_id: Mapped[int] = mapped_column(ForeignKey("brokers.id"), nullable=True)
    handoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    broker = relationship("Broker")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    #Adotei a sintaxe mais moderna do SQLAlchemy com Mapped e mapped_column, que é mais clara e compatível com ferramentas de análise de tipo