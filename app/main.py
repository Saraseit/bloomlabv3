from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers.auth import router as auth_router
from app.routers.usuarios import router as usuarios_router
from app.routers.insumos import router as insumos_router
from app.routers.arreglos import router as arreglos_router
from app.routers.arreglo_detalle import router as arreglo_detalle_router
from app.routers.clientes import router as clientes_router
from app.routers.eventos import router as eventos_router
from app.routers.evento_arreglo import router as evento_arreglo_router
from app.routers.evento_gastos import router as evento_gastos_router
from app.routers.evento_pagos import router as evento_pagos_router
from app.routers.evento_gastos_reales import (
    router as evento_gastos_reales_router
)
from app.routers.evento_compras import router as evento_compras_router
from app.routers.configuracion import router as configuracion_router
from app.routers.reportes import router as reportes_router
from app.routers.reportes_financieros import (
    router as reportes_fin_router
)

app = FastAPI(
    title="BloomLab API",
    version="3.0.0"
)

# -------------------------
# CORS (IMPORTANTE si usas frontend)
# -------------------------
#
# allow_origins=["*"] junto con allow_credentials=True es inválido según
# la spec de CORS: el navegador rechaza la respuesta cuando la petición
# lleva cookies. Hoy no se usan cookies y por eso no se notaba, pero la
# combinación estaba rota de antemano.
#
# Si más adelante se implementa login con JWT en cookies, hay que cambiar
# allow_origins por el dominio exacto del frontend en Render
# (por ejemplo ["https://bloomlabv3.onrender.com"]) y recién entonces
# poner allow_credentials=True. El comodín deja de ser válido.
#
# JWT viaja en Authorization: Bearer <token>, no en cookies.
# allow_credentials=False + allow_origins=["*"] es válido
# para este esquema. Si se migra a cookies, ver instrucciones
# en el bloque de CORS original.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# ROUTERS
# -------------------------
app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(insumos_router)
app.include_router(arreglos_router)
app.include_router(arreglo_detalle_router)
app.include_router(clientes_router)
app.include_router(eventos_router)
app.include_router(evento_arreglo_router)
app.include_router(evento_gastos_router)
app.include_router(evento_pagos_router)
app.include_router(evento_gastos_reales_router)
app.include_router(evento_compras_router)
app.include_router(configuracion_router)
app.include_router(reportes_router)
app.include_router(reportes_fin_router)


# -------------------------
# FRONTEND STATIC
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

class FrontendSinCache(StaticFiles):
    """Archivos del frontend que el navegador revalida en cada carga.

    Sin Cache-Control el navegador aplica caché heurística y, tras un
    despliegue, puede mezclar un HTML nuevo con un JS viejo. no-cache no
    impide guardar el archivo: obliga a preguntar con el ETag, y si no
    cambió el servidor responde 304 sin volver a mandarlo.
    """

    async def get_response(self, path, scope):
        respuesta = await super().get_response(path, scope)
        respuesta.headers["Cache-Control"] = "no-cache"
        return respuesta


if os.path.exists(FRONTEND_DIR):
    app.mount(
        "/frontend",
        FrontendSinCache(directory=FRONTEND_DIR, html=True),
        name="frontend"
    )

# -------------------------
# ROOT
# -------------------------
@app.get("/")
def root():
    return {
        "mensaje": "BloomLab API funcionando 🚀"
    }

# -------------------------
# SALUD (diagnóstico)
# -------------------------
# async a propósito: corre en el bucle principal sin pedir un hilo. Si
# los hilos se agotan, esta ruta sigue respondiendo y muestra cuántos
# están ocupados, así se distingue un servidor atorado de uno caído.
# No toca la base ni expone datos de negocio.
import threading
import time
from datetime import datetime, timezone

import anyio.to_thread

from app.database.connection import pool

_INICIO_PROCESO = time.time()


@app.get("/salud")
async def salud():
    limitador = anyio.to_thread.current_default_thread_limiter()
    stats = pool.get_stats()
    return {
        "ok": True,
        "proceso_desde": datetime.fromtimestamp(
            _INICIO_PROCESO, timezone.utc
        ).isoformat(timespec="seconds"),
        "minutos_activo": round((time.time() - _INICIO_PROCESO) / 60, 1),
        "hilos_sistema": threading.active_count(),
        "hilos_peticiones": {
            "ocupados": limitador.borrowed_tokens,
            "maximo": limitador.total_tokens,
        },
        "pool_bd": {
            "conexiones": stats.get("pool_size"),
            "libres": stats.get("pool_available"),
            "peticiones_esperando": stats.get("requests_waiting", 0),
            "errores_al_pedir": stats.get("requests_errors", 0),
            "conexiones_perdidas": stats.get("connections_lost", 0),
            "errores_al_conectar": stats.get("connections_errors", 0),
        },
    }
