import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configurações do Banco de Dados
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@db/{os.getenv('DB_NAME')}")