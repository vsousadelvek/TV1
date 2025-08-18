import os
import json
from sqlalchemy.orm import Session
import google.generativeai as genai

from app.models.lead import Lead
from app.models.conversation import ConversationHistory
from app.schemas.lead import LeadUpdate
from app.services import lead_service

# --- Configuração do Google Gemini ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Chave de API do Google não encontrada no arquivo .env")
genai.configure(api_key=GOOGLE_API_KEY)

generation_config = {"temperature": 0.7, "top_p": 1, "top_k": 1, "max_output_tokens": 2048}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                              generation_config=generation_config,
                              safety_settings=safety_settings)


# ------------------------------------

def add_message_to_history(db: Session, lead_id: int, role: str, content: str):
    history_entry = ConversationHistory(lead_id=lead_id, role=role, content=content)
    db.add(history_entry)
    db.commit()


def get_conversation_history(db: Session, lead_id: int) -> str:
    history = db.query(ConversationHistory).filter(ConversationHistory.lead_id == lead_id).order_by(
        ConversationHistory.timestamp.desc()).limit(10).all()
    history.reverse()

    formatted_history = ""
    for entry in history:
        formatted_history += f"{entry.role.capitalize()}: {entry.content}\n"
    return formatted_history.strip()


def process_user_message(db: Session, lead: Lead, user_message: str) -> str:
    add_message_to_history(db, lead.id, 'user', user_message)
    history = get_conversation_history(db, lead.id)

    current_data = {
        "location": lead.location, "property_type": lead.property_type, "bedrooms": lead.bedrooms,
    }
    current_data = {k: v for k, v in current_data.items() if v is not None}

    # --- PROMPT v2 - FOCO EM HUMANIZAÇÃO E FLUIDEZ ---
    prompt = f"""
    Sua única e mais importante regra é: VOCÊ DEVE RESPONDER SEMPRE EM PORTUGUÊS DO BRASIL.

    Você é Prime, um SDR de elite da imobiliária de alto padrão Aurora Prime. Sua personalidade é sofisticada, empática e extremamente consultiva. Você nunca soa como um robô.

    REGRAS DA CONVERSA:
    1. PERSONA: Use uma linguagem fluida e variada. Evite repetir as mesmas frases. Demonstre empatia ("Compreendo perfeitamente...", "Ótima pergunta..."). Se o usuário estiver indeciso, ajude-o a refinar as opções em vez de apenas repetir a pergunta.
    2. UMA PERGUNTA DE CADA VEZ: Mantenha um diálogo natural, nunca faça uma lista de perguntas.
    3. ORDEM LÓGICA: Colete as informações na ordem: 1º location, 2º property_type, 3º bedrooms.
    4. USE A MEMÓRIA: Verifique as "INFORMAÇÕES JÁ COLETADAS". Se uma informação já existe, NÃO pergunte por ela novamente. Confirme-a de forma elegante e passe para a próxima pergunta. Exemplo: "Certo, um terreno em Santa Catarina, excelente! Para esse terreno, estamos pensando em uma construção futura com quantos quartos?"
    5. ENCERRAMENTO: Quando tiver as 3 informações, faça um resumo amigável e se despeça de forma profissional.

    INFORMAÇÕES JÁ COLETADAS:
    {json.dumps(current_data, ensure_ascii=False)}

    HISTÓRICO DA CONVERSA:
    ---
    {history}
    ---

    Baseado em todas as regras, analise a última mensagem do "User" e gere um JSON com duas chaves: "update_data" (com as novas informações) e "response_text" (sua resposta humanizada).
    """

    ai_response_text = "Desculpe, estou com um problema técnico no momento."
    try:
        convo = model.start_chat(history=[])
        response = convo.send_message(prompt)

        response_text = response.text
        start_index = response_text.find('{')
        end_index = response_text.rfind('}') + 1
        json_str = response_text[start_index:end_index]
        response_data = json.loads(json_str)

        update_data = response_data.get("update_data", {})
        ai_response_text = response_data.get("response_text", "Não entendi, pode repetir?")

        if update_data:
            print(f"Atualizando lead {lead.id} com os dados do Gemini: {update_data}")
            lead_update_obj = LeadUpdate(**update_data)
            lead_service.update_lead(db=db, db_lead=lead, lead_update=lead_update_obj)

    except Exception as e:
        print(f"ERRO ao chamar a API do Gemini: {e}")

    add_message_to_history(db, lead.id, 'assistant', ai_response_text)

    return ai_response_text
