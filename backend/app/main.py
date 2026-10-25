from fastapi import FastAPI
import os
from fastapi.middleware.cors import CORSMiddleware

from app.api.data import router as data_router

app = FastAPI(title="Gridbricks Challenge API")
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
# allow_origins=origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}

