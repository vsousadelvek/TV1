from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.models.lead import Lead
from app.models.followup import FollowUp

# Cadência de follow-up em dias e as mensagens
FOLLOW_UP_CADENCE = {
    1: "Olá! Só para confirmar se recebeu minha primeira mensagem e se há algo que eu possa ajudar.",
    3: "Olá! Pensando em nossa conversa, encontrei algumas oportunidades que podem lhe interessar. Gostaria de ver os detalhes?",
    7: "Olá! Que tal agendarmos uma breve chamada para eu entender melhor suas necessidades e apresentar as melhores opções?",
    14: "Olá! Não quero incomodar. Continuo à sua disposição para quando quiser retomar a busca pelo seu imóvel ideal. Um abraço!",
}

def schedule_initial_followups(db: Session, lead: Lead):
    """Agenda a sequência inicial de follow-ups para um novo lead."""
    now = datetime.now(timezone.utc)
    for days, message in FOLLOW_UP_CADENCE.items():
        scheduled_time = now + timedelta(days=days)
        follow_up_task = FollowUp(
            lead_id=lead.id,
            scheduled_for=scheduled_time,
            status="pending",
            message_template=message
        )
        db.add(follow_up_task)
    db.commit()

def process_pending_followups(db: Session):
    """Busca e 'envia' os follow-ups pendentes."""
    now = datetime.now(timezone.utc)
    pending_tasks = db.query(FollowUp).filter(
        FollowUp.status == "pending",
        FollowUp.scheduled_for <= now
    ).all()

    for task in pending_tasks:
        print(f"--- ENVIANDO FOLLOW-UP ---")
        print(f"Para: {task.lead.phone_number}")
        print(f"Mensagem: {task.message_template}")
        print(f"--------------------------")
        task.status = "sent"
        db.add(task)

    db.commit()

def get_followups_by_lead_id(db: Session, lead_id: int):
    """Busca todos os follow-ups agendados para um lead específico."""
    return db.query(FollowUp).filter(FollowUp.lead_id == lead_id).all()