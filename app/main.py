from fastapi import FastAPI

from app.routers.insumos import router as insumos_router
from app.routers.arreglos import router as arreglos_router
from app.routers.arreglo_detalle import (
    router as arreglo_detalle_router
)

app = FastAPI(
    title="BloomLab API",
    version="1.0.0"
)

app.include_router(insumos_router)
app.include_router(arreglos_router)
app.include_router(arreglo_detalle_router)


@app.get("/")
def root():
    return {
        "mensaje": "BloomLab API funcionando"
    }