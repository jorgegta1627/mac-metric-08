import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

print("Buscando .env en:", ENV_PATH)
print("¿Existe?", ENV_PATH.exists())

load_dotenv(dotenv_path=ENV_PATH)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print("DB_HOST =", DB_HOST)
print("DB_PORT =", DB_PORT)
print("DB_NAME =", DB_NAME)
print("DB_USER =", DB_USER)
print("DB_PASSWORD =", DB_PASSWORD)

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()

    print("✅ Conexión exitosa a PostgreSQL")
    print(version[0])

    cursor.close()
    conn.close()

except Exception as e:
    print("❌ Error al conectar con PostgreSQL:")
    print(e)