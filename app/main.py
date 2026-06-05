from fastapi import FastAPI
from app.routers.insumos import router as insumos_router

app = FastAPI(
    title="BloomLab API",
    version="1.0.0"
)

app.include_router(insumos_router)

@app.get("/")
def root():
    return {
        "mensaje": "BloomLab API funcionando"
    }