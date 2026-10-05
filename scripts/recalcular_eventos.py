"""
Uso: python scripts/recalcular_eventos.py
Recalcula y guarda los totales de todos los eventos (activos e inactivos)
con la fórmula vigente. Sirve después de un cambio de fórmula o de
parámetros. Imprime el antes y el después de cada evento activo.
Requiere DATABASE_URL en el entorno (.env).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from app.database.connection import get_connection
from app.services.eventos_service import actualizar_totales_evento

conn = get_connection()
cur = conn.cursor()
cur.execute("""
    SELECT id, nombre, activo, costo_final, precio_minimo, precio_sugerido, precio_venta
    FROM eventos
    ORDER BY id
""")
antes = cur.fetchall()
conn.close()


def dinero(v):
    return f"{float(v):>12,.2f}" if v is not None else f"{'N/D':>12}"


print(f"{'evento':<38}{'costo antes':>13}{'costo ahora':>13}"
      f"{'mínimo ahora':>13}{'sugerido ahora':>15}{'acordado':>13}{'margen':>8}")
for evento_id, nombre, activo, costo_ant, _, _, precio_venta in antes:
    t = actualizar_totales_evento(evento_id)
    if not activo:
        continue
    margen = f"{t['margen'] * 100:6.1f}%" if t["tipo_precio"] == "acordado" else "      -"
    print(f"{(str(evento_id) + ' ' + nombre)[:37]:<38}{dinero(costo_ant)} {dinero(t['costo_final'])}"
          f" {dinero(t['precio_minimo'])}   {dinero(t['precio_sugerido'])} {dinero(precio_venta)}{margen}")

print(f"\nEventos recalculados: {len(antes)}")
