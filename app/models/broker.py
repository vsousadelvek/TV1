from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Broker(Base):
    __tablename__ = "brokers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    specialty_region: Mapped[str] = mapped_column(nullable=True) # Ex: "Balneário Camboriú", "Florianópolis"