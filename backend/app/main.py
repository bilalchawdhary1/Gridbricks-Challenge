
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Gridbricks Wind Forecast API",
    description="API for reviewing wind forecasts and forecast accuracy.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Gridbricks API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
