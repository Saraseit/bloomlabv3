from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers.insumos import router as insumos_router
from app.routers.arreglos import router as arreglos_router
from app.routers.arreglo_detalle import router as arreglo_detalle_router
from app.routers.clientes import router as clientes_router
from app.routers.eventos import router as eventos_router
from app.routers.evento_arreglo import router as evento_arreglo_router
from app.routers.evento_gastos import router as evento_gastos_router
from app.routers.reportes import router as reportes_router

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
app.include_router(insumos_router)
app.include_router(arreglos_router)
app.include_router(arreglo_detalle_router)
app.include_router(clientes_router)
app.include_router(eventos_router)
app.include_router(evento_arreglo_router)
app.include_router(evento_gastos_router)
app.include_router(reportes_router)


# -------------------------
# FRONTEND STATIC
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount(
        "/frontend",
        StaticFiles(directory=FRONTEND_DIR, html=True),
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