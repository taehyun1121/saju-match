from fastapi import FastAPI

app = FastAPI(title="SajuMatch API")

@app.get("/")
def root():
    return {"service": "SajuMatch API", "status": "OK"}

@app.get("/health")
def health():
    return {"status": "ok"}
