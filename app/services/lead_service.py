from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.schemas.lead import LeadCreate
from app.schemas.lead import LeadUpdate

def get_lead_by_phone(db: Session, phone_number: str):
    """Busca um lead pelo número de telefone."""
    return db.query(Lead).filter(Lead.phone_number == phone_number).first()

def create_lead(db: Session, lead: LeadCreate):
    """Cria um novo lead no banco de dados."""
    db_lead = Lead(phone_number=lead.phone_number)
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

def update_lead(db: Session, db_lead: Lead, lead_update: LeadUpdate):
    """Atualiza um lead com novos dados de qualificação."""
    update_data = lead_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_lead, key, value)

    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead