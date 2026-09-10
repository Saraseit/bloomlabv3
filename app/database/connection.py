from dotenv import load_dotenv
import atexit
import os

from psycopg.pq import TransactionStatus
from psycopg_pool import ConnectionPool

load_dotenv()

# ──────────────────────────────────────────────
# Pool de conexiones
#
# Neon en tier gratuito limita las conexiones concurrentes (~5-10). Abrir
# una conexión nueva por request agotaba ese límite con dos o tres
# usuarios simultáneos, así que las conexiones se reciclan desde un pool.
# ──────────────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no está definida. El pool de conexiones no puede "
        "arrancar: define DATABASE_URL en el entorno (archivo .env en "
        "local, variable de entorno en Render) antes de iniciar la API."
    )

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    kwargs={"sslmode": "require"},
    min_size=1,
    max_size=5,
    max_waiting=10,
    timeout=10.0,
    open=False,
)

# wait=False: si Neon tarda en responder al arrancar, el pool reintenta
# en segundo plano en lugar de tumbar el arranque de FastAPI.
pool.open()

# Cierra el pool ordenadamente al terminar el proceso.
atexit.register(pool.close)


class PooledConnection:
    """Conexión prestada del pool con la interfaz de psycopg.

    Los services usan el patrón conn = get_connection() / conn.commit() /
    conn.close(). Se conserva tal cual: la única diferencia es que close()
    devuelve la conexión al pool con putconn() en vez de cerrarla.

    Igual que close() en psycopg, putconn() hace rollback de cualquier
    transacción abierta antes de reciclar la conexión, así que el
    comportamiento de commit/rollback es idéntico al anterior.
    """

    def __init__(self, conn):
        self._conn = conn
        self._devuelta = False

    def close(self):
        """Devuelve la conexión al pool. Es idempotente."""
        if self._devuelta:
            return
        self._devuelta = True

        # Se descarta el trabajo sin confirmar antes de reciclar, igual que
        # hacía close() en psycopg. Se hace aquí y no en putconn() porque
        # psycopg abre transacción incluso con un SELECT: sin este rollback
        # el pool registraría un WARNING por cada request de solo lectura.
        try:
            if self._conn.info.transaction_status != TransactionStatus.IDLE:
                self._conn.rollback()
        except Exception:
            pass

        pool.putconn(self._conn)

    def __getattr__(self, nombre):
        # cursor(), commit(), rollback(), info, etc. van a la conexión real
        return getattr(self._conn, nombre)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # Sin excepción se confirma el trabajo; con excepción se revierte,
        # igual que el bloque with de psycopg.
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self.close()
        return False

    def __del__(self):
        # Red de seguridad: si un service se sale por una excepción sin
        # llamar a close(), la conexión regresa al pool en vez de perderse.
        try:
            self.close()
        except Exception:
            pass


def get_connection():
    """Presta una conexión del pool.

    Sirve con el patrón de siempre:

        conn = get_connection()
        ...
        conn.commit()
        conn.close()

    y también como context manager:

        with get_connection() as conn:
            ...
    """
    return PooledConnection(pool.getconn())
