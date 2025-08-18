import os
import io
import shutil
import tempfile
import requests  # Usaremos requests para a chamada direta
from fastapi import UploadFile
from app.core.minio_client import minio_client, BUCKET_NAME
from faster_whisper import WhisperModel

# --- Configuração do ElevenLabs ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("Chave de API da ElevenLabs não encontrada no arquivo .env")

# --- Configuração do Whisper (STT Local) ---
STT_MODEL_SIZE = "base"
whisper_model = None


def _get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print(f"Carregando modelo Whisper '{STT_MODEL_SIZE}' pela primeira vez...")
        whisper_model = WhisperModel(STT_MODEL_SIZE, device="cpu", compute_type="int8")
        print("Modelo Whisper carregado com sucesso.")
    return whisper_model


# --- Funções do Serviço ---

def upload_audio_to_storage(file: UploadFile, phone_number: str) -> str:
    # (código existente, sem alterações)
    try:
        file.file.seek(0)
        file_content = file.file.read()
        file_size = len(file_content)
        object_name = f"{phone_number}/{file.filename}"
        file_stream = io.BytesIO(file_content)
        minio_client.put_object(
            BUCKET_NAME, object_name, data=file_stream,
            length=file_size, content_type=file.content_type
        )
        return object_name
    except Exception as e:
        print(f"Erro ao fazer upload para o MinIO: {e}")
        raise


def transcribe_audio_local(audio_file_path: str) -> str:
    # (código existente, sem alterações)
    try:
        model = _get_whisper_model()
        segments, info = model.transcribe(audio_file_path, language="pt", beam_size=5)
        transcribed_text = "".join(segment.text for segment in segments)
        return transcribed_text.strip()
    except Exception as e:
        print(f"Erro ao transcrever áudio localmente: {e}")
        raise


def generate_speech_from_text(text: str) -> bytes:
    """
    Usa a API da ElevenLabs para converter texto em áudio de alta qualidade via chamada HTTP direta.
    """
    # --- TROQUE O ID AQUI ---
    # ID da voz "Bella"
    VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

    # URL do endpoint de Text-to-Speech da ElevenLabs
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        print(f"Gerando áudio (ElevenLabs API) para o texto: '{text}'")

        response = requests.post(tts_url, json=data, headers=headers)

        # Lança um erro se a resposta não for bem-sucedida (como 401 Unauthorized)
        response.raise_for_status()

        # Retorna os bytes brutos do arquivo de áudio (.mp3)
        return response.content

    except Exception as e:
        print(f"ERRO ao gerar áudio com a API da ElevenLabs: {e}")
        raise
