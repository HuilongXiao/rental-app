from fastapi import FastAPI

app = FastAPI(title="Rental App API", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "rental-app-api"}
