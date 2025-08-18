import os
from minio import Minio
from dotenv import load_dotenv

load_dotenv()

MINIO_HOST = os.getenv("MINIO_HOST")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
BUCKET_NAME = "lead-media"

minio_client = Minio(
    MINIO_HOST,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False # Em desenvolvimento, usamos HTTP
)

# Cria o bucket se ele não existir
try:
    found = minio_client.bucket_exists(BUCKET_NAME)
    if not found:
        minio_client.make_bucket(BUCKET_NAME)
        print(f"Bucket '{BUCKET_NAME}' criado com sucesso.")
    else:
        print(f"Bucket '{BUCKET_NAME}' já existe.")
except Exception as e:
    print(f"Erro ao conectar com o MinIO ou criar bucket: {e}")
    # Em um app real, poderíamos decidir parar a inicialização aqui
    pass