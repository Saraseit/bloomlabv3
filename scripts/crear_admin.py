"""
Uso: python scripts/crear_admin.py
Crea el primer usuario admin de BloomLab si no existe.
Requiere DATABASE_URL en el entorno (.env).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()
from app.database.connection import get_connection
from app.core.security import hash_password

NOMBRE = "Administrador"
EMAIL = "admin@minimal.com"
PASSWORD = "bloomlab2024"   # el usuario debe cambiarlo al primer login
ROL = "admin"

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT id FROM usuarios WHERE email = %s", (EMAIL,))
if cur.fetchone():
    print(f"El usuario {EMAIL} ya existe.")
else:
    cur.execute("""
        SELECT id FROM empresas WHERE nombre = 'Minimal' LIMIT 1
    """)
    empresa = cur.fetchone()
    if not empresa:
        print("Error: la empresa 'Minimal' no existe en la tabla empresas.")
        sys.exit(1)
    cur.execute("""
        INSERT INTO usuarios (empresa_id, nombre, email,
                              password_hash, rol, activo)
        VALUES (%s,%s,%s,%s,%s,TRUE) RETURNING id
    """, (empresa[0], NOMBRE, EMAIL, hash_password(PASSWORD), ROL))
    nuevo_id = cur.fetchone()[0]
    conn.commit()
    print(f"Admin creado. ID: {nuevo_id}, email: {EMAIL}, pass: {PASSWORD}")
cur.close()
conn.close()
