from app.database.connection import get_connection

conn = get_connection()

print("✅ BloomLab conectado")

conn.close()