from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.lead import Lead
from app.models.broker import Broker
from app.models.followup import FollowUp

def perform_handoff(db: Session, lead: Lead):
    """
    Realiza o handoff de um lead: encontra o corretor, formata o resumo,
    cancela follow-ups futuros e atualiza o status do lead.
    """
    # 1. Regra de roteamento: encontrar corretor pela região do lead
    broker = db.query(Broker).filter(Broker.specialty_region == lead.location).first()
    if not broker:
        # Roteamento padrão se não encontrar especialista
        broker = db.query(Broker).first()

    # 2. Formatar o resumo
    summary = f"""
    --- NOVO LEAD QUALIFICADO PARA HANDOFF ---
    Corretor Designado: {broker.name} ({broker.email})

    [Dados do Lead]
    - Telefone: {lead.phone_number}
    - Status: Qualificado para Handoff

    [Preferências]
    - Região de Interesse: {lead.location}
    - Tipo de Imóvel: {lead.property_type}
    - Quartos: {lead.bedrooms}
    - Vagas: {lead.parking_spots}
    - Faixa de Investimento: {lead.investment_range}
    - Prazo para Mudança: {lead.move_in_deadline}

    Atribuído em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}
    --- FIM DO RESUMO ---
    """
    print(summary) # Simula o envio do resumo para o CRM/Corretor

    # 3. Atualizar o lead
    lead.broker_id = broker.id
    lead.status = "handoff_completed"
    lead.handoff_at = datetime.now(timezone.utc)
    db.add(lead)

    # 4. Cancelar todos os follow-ups pendentes para este lead
    db.query(FollowUp).filter(
        FollowUp.lead_id == lead.id,
        FollowUp.status == "pending"
    ).update({"status": "cancelled"})

    db.commit()
    db.refresh(lead)
    return lead