from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi import Response
# Imports dos nossos módulos de serviço e schemas
from app.services import lead_service, conversation_service, media_service
from app.schemas.lead import LeadCreate
from app.core.database import SessionLocal

router = APIRouter()


# --- Schemas (Modelos de Dados) para esta rota ---

class WebhookPayload(BaseModel):
    phone_number: str
    message: str


class TextToSpeechPayload(BaseModel):
    text: str


# --- Funções Auxiliares ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Endpoints da API ---

@router.post("/conversation/webhook", tags=["Conversational Demo"], operation_id="handle_conversation")
def handle_conversation_message(payload: WebhookPayload, db: Session = Depends(get_db)):
    """
    Este endpoint simula o recebimento de uma mensagem do WhatsApp.
    Ele gerencia a conversa e atualiza o lead em tempo real.
    """
    # Garante que o lead exista, criando um novo se necessário
    lead = lead_service.get_lead_by_phone(db, phone_number=payload.phone_number)
    if not lead:
        lead = lead_service.create_lead(db, lead=LeadCreate(phone_number=payload.phone_number))

    # Processa a mensagem e obtém a resposta da IA
    ai_response = conversation_service.process_user_message(db, lead, payload.message)

    return {"response": ai_response}


@router.post("/tts/generate", tags=["Conversational Demo"], operation_id="generate_speech")
def generate_speech(payload: TextToSpeechPayload):
    """Recebe um texto e retorna o áudio correspondente usando gTTS."""
    try:
        # A função que você já tem no seu media_service
        audio_bytes = media_service.generate_speech_from_text(payload.text)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# No topo do arquivo webhook_routes.py


# Adicione esta classe Pydantic
class TextToSpeechPayload(BaseModel):
    text: str

# Adicione este novo endpoint no final do arquivo
@router.post("/tts/generate", tags=["Conversational Demo"], operation_id="generate_speech")
def generate_speech(payload: TextToSpeechPayload):
    """Recebe um texto e retorna o áudio correspondente usando ElevenLabs."""
    try:
        audio_bytes = media_service.generate_speech_from_text(payload.text)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))