# SDR Virtual para Imobiliária de Alto Padrão

## 1. Descrição do Projeto

Esta é uma implementação de um SDR (Sales Development Representative) virtual para WhatsApp, conforme especificado no briefing do projeto. O objetivo é criar um assistente de IA capaz de qualificar leads de forma humanizada, entender mensagens de texto e áudio, executar um fluxo de follow-up estruturado e realizar o handoff para um corretor humano.

## 2. Arquitetura e Stack Tecnológica

A solução foi construída utilizando uma arquitetura de microsserviços orquestrada com Docker Compose, focando em tecnologias modernas, escaláveis e, sempre que possível, de código aberto e auto-hospedadas para garantir privacidade e controle.

- **Linguagem:** Python 3.11
- **Framework Web:** FastAPI
- **Servidor ASGI:** Uvicorn
- **Banco de Dados:** PostgreSQL
- **Armazenamento de Mídia (S3-compatível):** MinIO
- **Speech-to-Text (STT):** `faster-whisper` (Modelo "base" rodando localmente)
- **Natural Language Understanding (NLU):** `Ollama` com o modelo `Mistral:7b` (rodando localmente)
- **Text-to-Speech (TTS):** `Coqui-TTS` (Modelo "tts_models/pt/cv/vits" rodando localmente)
- **Orquestração:** Docker & Docker Compose

## 3. Como Executar o Projeto

#### Pré-requisitos
1.  Docker e Docker Compose instalados.
2.  Ollama instalado na máquina host (disponível em [ollama.com](https://ollama.com/)).

#### Passos para Execução
1.  **Clone o repositório:**
    ```sh
    git clone <url-do-repositorio>
    cd <pasta-do-projeto>
    ```

2.  **Instale e execute o modelo de linguagem (Ollama):**
    Em um terminal separado, execute o seguinte comando e mantenha-o rodando. O download (aprox. 4GB) ocorrerá apenas na primeira vez.
    ```sh
    ollama run mistral
    ```

3.  **Configure as Variáveis de Ambiente:**
    Crie um arquivo `.env` na raiz do projeto, baseado no arquivo `.env.example` (se houver) ou com o seguinte conteúdo:
    ```env
    # PostgreSQL Config
    DB_USER=aurora
    DB_PASSWORD=supersecretpassword
    DB_NAME=aurora_db

    # MinIO Config
    MINIO_USER=minioadmin
    MINIO_PASSWORD=supersecretpassword
    MINIO_HOST=minio:9000
    MINIO_ACCESS_KEY=${MINIO_USER}
    MINIO_SECRET_KEY=${MINIO_PASSWORD}
    ```

4.  **Inicie os Serviços com Docker Compose:**
    No terminal principal, na raiz do projeto, execute:
    ```sh
    docker-compose up --build
    ```
    *Aguarde o download e carregamento dos modelos de IA na primeira inicialização.*

5.  **Acesse a API:**
    A documentação interativa estará disponível em **`http://localhost:8000/docs`**.

## 4. Plano de Integração (Passos Futuros)

Conforme a estratégia do projeto teste, as integrações com serviços externos foram simuladas. A seguir, o plano para a implementação final.

#### 4.1. Integração com WhatsApp (Evolution API)
A conexão com o WhatsApp seria realizada através de um único endpoint de webhook: `POST /webhook/whatsapp`.

**Lógica do Webhook:**
1.  Receber o payload JSON da Evolution API.
2.  Extrair o telefone do remetente (`sender`) e o conteúdo da mensagem.
3.  Verificar se o lead já existe no banco com `lead_service.get_lead_by_phone`. Se não, criar com `lead_service.create_lead`.
4.  Identificar o tipo de mensagem (texto, áudio, etc.).
5.  **Se for áudio:**
    -   Baixar o arquivo de áudio a partir da URL fornecida pela Evolution API.
    -   Chamar o `media_service.transcribe_audio_local` para obter o texto.
6.  **Processar o Texto (original ou transcrito):**
    -   Chamar o `nlu_service.extract_lead_info_from_text` para extrair dados estruturados.
    -   Chamar o `lead_service.update_lead` para salvar as novas informações no perfil do lead.
7.  Formular uma resposta em texto e usar a API da Evolution para enviá-la de volta ao usuário.

#### 4.2. Integração com CRM
O handoff para o corretor, atualmente simulado com um `print()`, seria finalizado no `handoff_service.py`.

**Lógica de Handoff:**
1.  A função `perform_handoff` permaneceria a mesma até a geração do resumo.
2.  A linha `print(summary)` seria substituída por uma chamada de API para o CRM, usando a biblioteca `requests`:

    ```python
    import requests

    crm_api_url = "[https://api.crm-exemplo.com/v1/leads](https://api.crm-exemplo.com/v1/leads)"
    headers = {"Authorization": "Bearer <TOKEN_DO_CRM>"}
    
    lead_payload = {
        "name": f"Lead - {lead.phone_number}",
        "phone": lead.phone_number,
        "owner_email": broker.email,
        "notes": summary, # O resumo completo entraria nas notas
        "custom_fields": {
            "regiao_interesse": lead.location,
            "tipo_imovel": lead.property_type
        }
    }
    
    response = requests.post(crm_api_url, json=lead_payload, headers=headers)
    if response.status_code == 201:
        print("Lead enviado ao CRM com sucesso.")
    ```

## 5. Análise de Riscos (Evolution API)

-   **Risco Principal:** Por ser uma API não oficial, a Evolution API está sujeita a instabilidade e, em casos extremos, ao banimento do número de WhatsApp pela Meta.
-   **Plano de Contingência (Plano B):** Para um ambiente de produção, a migração para a **API Oficial do WhatsApp Business (via Meta Cloud API)** seria o caminho recomendado. Embora tenha custos por conversação e seja mais restritiva, ela oferece estabilidade, suporte oficial e conformidade com os termos de serviço da Meta.
