import ollama
import json
from app.schemas.lead import LeadUpdate

# O endereço do Ollama rodando no computador host.
# Usamos 'host.docker.internal' para o contêiner Docker acessar o localhost
OLLAMA_HOST = "host.docker.internal"
OLLAMA_PORT = 11434

client = ollama.Client(host=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}")

def extract_lead_info_from_text(text: str) -> LeadUpdate:
    """
    Usa o Mistral via Ollama para extrair informações de um texto
    e retorná-las no formato do nosso schema LeadUpdate.
    """
    prompt = f"""
    Analise o texto a seguir e extraia as informações sobre as preferências de um cliente imobiliário.
    O texto é: "{text}"

    Retorne um JSON contendo apenas as chaves que você conseguir identificar no texto. As chaves possíveis são:
    - location (string)
    - property_type (string, ex: 'casa', 'apartamento', 'cobertura')
    - bedrooms (integer)
    - parking_spots (integer)
    - investment_range (string)

    Se você não encontrar uma informação, não inclua a chave no JSON.
    Exemplo de retorno: {{"location": "Balneário Camboriú", "bedrooms": 4}}
    """

    try:
        response = client.chat(
            model='mistral',
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )

        response_json_str = response['message']['content']
        data = json.loads(response_json_str)

        lead_update_data = LeadUpdate(**data)
        return lead_update_data

    except Exception as e:
        print(f"Erro ao analisar texto com Ollama: {e}")
        return LeadUpdate()