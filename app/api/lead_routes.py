from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import List
import tempfile
import shutil
import os
from slugify import slugify

from app.services import lead_service, followup_service, handoff_service, media_service, nlu_service
from app.schemas.lead import Lead, LeadCreate, LeadUpdate
from app.schemas.followup import FollowUp
from app.models.followup import FollowUp as FollowUpModel
from app.core.database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Endpoints de Leads (sem alterações) ---
@router.post("/leads/", response_model=Lead, tags=["Leads"], operation_id="create_lead")
def create_new_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    # ... (código existente)
    db_lead = lead_service.get_lead_by_phone(db, phone_number=lead.phone_number)
    if db_lead:
        return db_lead
    new_lead = lead_service.create_lead(db=db, lead=lead)
    followup_service.schedule_initial_followups(db=db, lead=new_lead)
    return new_lead


@router.get("/leads/{phone_number}", response_model=Lead, tags=["Leads"], operation_id="get_lead_by_phone")
def read_lead(phone_number: str, db: Session = Depends(get_db)):
    # ... (código existente)
    db_lead = lead_service.get_lead_by_phone(db, phone_number=phone_number)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return db_lead


@router.patch("/leads/{phone_number}", response_model=Lead, tags=["Leads"], operation_id="update_lead")
def update_lead_data(phone_number: str, lead_update: LeadUpdate, db: Session = Depends(get_db)):
    # ... (código existente)
    db_lead = lead_service.get_lead_by_phone(db, phone_number=phone_number)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return lead_service.update_lead(db=db, db_lead=db_lead, lead_update=lead_update)


# --- Endpoints de Follow-ups ---
@router.get("/leads/{phone_number}/followups", response_model=List[FollowUp], tags=["Follow-ups"],
            operation_id="get_lead_followups")
def read_lead_followups(phone_number: str, db: Session = Depends(get_db)):
    # ... (código existente)
    db_lead = lead_service.get_lead_by_phone(db, phone_number=phone_number)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return followup_service.get_followups_by_lead_id(db, lead_id=db_lead.id)


# --- MUDANÇA PRINCIPAL AQUI ---
@router.get("/followups/{followup_id}/audio", tags=["Follow-ups"], operation_id="get_followup_audio")
def get_followup_as_audio(followup_id: int, db: Session = Depends(get_db)):
    """
    Gera e retorna a mensagem de um follow-up em áudio de alta qualidade via servidor GPU.
    """
    followup_task = db.query(FollowUpModel).filter(FollowUpModel.id == followup_id).first()
    if not followup_task:
        raise HTTPException(status_code=404, detail="Tarefa de follow-up não encontrada")

    try:
        # Chama o serviço que agora busca o áudio da GPU
        audio_bytes = media_service.generate_speech_from_text(followup_task.message_template)

        # Retorna os bytes de áudio diretamente
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar áudio: {e}")


# --- Endpoints de Mídia e Handoff (sem alterações) ---
@router.post("/leads/{phone_number}/audio", tags=["Mídia"], operation_id="upload_audio_message")
def handle_audio_message(
        phone_number: str, audio_file: UploadFile = File(...), db: Session = Depends(get_db)
):
    # ... (código existente)
    db_lead = lead_service.get_lead_by_phone(db, phone_number=phone_number)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    audio_file.file.seek(0)
    original_filename = audio_file.filename
    file_extension = os.path.splitext(original_filename)[1]
    safe_filename_base = slugify(os.path.splitext(original_filename)[0])
    safe_filename = f"{safe_filename_base}{file_extension}"
    audio_file.filename = safe_filename
    object_name = media_service.upload_audio_to_storage(audio_file, phone_number)
    audio_file.file.seek(0)
    temp_audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=safe_filename) as temp_audio:
            shutil.copyfileobj(audio_file.file, temp_audio)
            temp_audio_path = temp_audio.name
        transcribed_text = media_service.transcribe_audio_local(temp_audio_path)
        print(f"Texto transcrito para análise: '{transcribed_text}'")
        current_data = {"location": db_lead.location, "property_type": db_lead.property_type,
                        "bedrooms": db_lead.bedrooms}
        current_data = {k: v for k, v in current_data.items() if v is not None}
        extracted_data = nlu_service.extract_lead_info_from_text(transcribed_text, current_data)
        print(f"Dados extraídos pelo LLM: {extracted_data.model_dump(exclude_unset=True)}")
        if extracted_data.model_dump(exclude_unset=True):
            lead_service.update_lead(db=db, db_lead=db_lead, lead_update=extracted_data)
    finally:
        audio_file.file.close()
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
    return {
        "message": "Áudio processado e lead atualizado.",
        "storage_path": object_name,
        "transcribed_text": transcribed_text,
        "updated_fields": extracted_data.model_dump(exclude_unset=True)
    }


@router.post("/leads/{phone_number}/handoff", response_model=Lead, tags=["Handoff"],
             operation_id="perform_lead_handoff")
def trigger_handoff(phone_number: str, db: Session = Depends(get_db)):
    # ... (código existente)
    db_lead = lead_service.get_lead_by_phone(db, phone_number=phone_number)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return handoff_service.perform_handoff(db, lead=db_lead)
