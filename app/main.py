from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.database import engine, Base, SessionLocal
from app.models import lead, followup, broker, conversation
from app.api import lead_routes, webhook_routes
from app.services.followup_service import process_pending_followups
from app.models.broker import Broker as BrokerModel
from fastapi.middleware.cors import CORSMiddleware

# --- Lógica de Inicialização ---

def create_initial_data():
    """Cria dados iniciais (ex: corretores) se o banco estiver vazio."""
    db = SessionLocal()
    try:
        # Verifica se já existem corretores para não duplicar
        if db.query(BrokerModel).count() == 0:
            print("Criando dados iniciais de corretores...")
            brokers = [
                BrokerModel(name="Carlos Mendes", email="carlos.mendes@auroraprime.com",
                            specialty_region="Balneário Camboriú"),
                BrokerModel(name="Juliana Paiva", email="juliana.paiva@auroraprime.com",
                            specialty_region="Florianópolis"),
                BrokerModel(name="Marcos Andrade", email="marcos.andrade@auroraprime.com", specialty_region="Itapema")
            ]
            db.add_all(brokers)
            db.commit()
            print("Dados iniciais criados.")
    finally:
        db.close()


def check_followups_job():
    """Função que o agendador executará para processar os follow-ups."""
    db = SessionLocal()
    try:
        print("Scheduler rodando: Verificando follow-ups pendentes...")
        process_pending_followups(db)
    finally:
        db.close()


# Cria o agendador
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação (iniciar e parar)."""
    # Cria as tabelas do banco de dados na inicialização
    print("Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)

    # Adiciona dados iniciais se necessário
    create_initial_data()

    # Adiciona a tarefa ao scheduler para rodar a cada minuto
    scheduler.add_job(
        check_followups_job,
        trigger=IntervalTrigger(minutes=1),
        id="check_followups_job",
        replace_existing=True,
    )
    scheduler.start()

    print("Aplicação iniciada com sucesso.")
    yield

    # Desliga o scheduler ao encerrar a aplicação
    scheduler.shutdown()
    print("Aplicação encerrada.")


# --- Criação da Aplicação FastAPI ---

app = FastAPI(
    title="Aurora Prime SDR Virtual",
    description="API para o assistente de qualificação de leads da Aurora Prime Imóveis.",
    version="1.0.0",
    lifespan=lifespan
)
# Bloco para configurar o CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens (para o teste)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

# Inclui os roteadores da nossa API
app.include_router(lead_routes.router)
app.include_router(webhook_routes.router)


@app.get("/", tags=["Root"])
def read_root():
    """Endpoint raiz para verificar se a API está no ar."""
    return {"status": "ok", "message": "Bem-vindo à API do SDR Virtual da Aurora Prime!"}