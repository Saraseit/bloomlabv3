"""
Uso: python scripts/migrar.py
Aplica las migraciones de esquema pendientes (app/database/migraciones.py).
Es idempotente: las que ya se aplicaron quedan registradas en
schema_migraciones y no se vuelven a ejecutar.
Requiere DATABASE_URL en el entorno (.env).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from app.database.migraciones import aplicar_migraciones

aplicar_migraciones()
print("Esquema al día.")
