from fastapi import FastAPI

app = FastAPI(title="Gridbricks Challenge")

@app.get("/")
def root():
    return {"message": "Gridbricks Challenge is running!"}


