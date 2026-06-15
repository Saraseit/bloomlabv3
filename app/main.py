from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.insumos import router as insumos_router
from app.routers.arreglos import router as arreglos_router
from app.routers.arreglo_detalle import (
    router as arreglo_detalle_router
)
from app.routers.clientes import (
    router as clientes_router
)
from app.routers.eventos import (
    router as eventos_router
)
from app.routers.evento_arreglo import (
    router as evento_arreglo_router
)



app = FastAPI(
    title="BloomLab API",
    version="1.0.0"
)

app.include_router(insumos_router)
app.include_router(arreglos_router)
app.include_router(arreglo_detalle_router)
app.include_router(clientes_router)
app.include_router(eventos_router)
app.include_router(
    evento_arreglo_router
)

# Frontend
app.mount(
    "/frontend",
    StaticFiles(directory="app/frontend"),
    name="frontend"
)

@app.get("/")
def root():
    return {
        "mensaje": "BloomLab API funcionando"
    }

