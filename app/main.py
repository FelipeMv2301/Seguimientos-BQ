from fastapi import FastAPI

app = FastAPI(title="Seguimientos-BQ")


@app.get("/salud")
def salud():
    return {"status": "ok"}
