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


app = FastAPI(
    title="BloomLab API",
    version="3.0.0"
)

# -------------------------
# CORS (IMPORTANTE si usas frontend)
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # luego puedes restringirlo
    allow_credentials=True,
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