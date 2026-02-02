from fastapi import FastAPI

app = FastAPI(title="Mizigo TZ API")

@app.get("/health")
def health():
    return {"status": "ok"}
