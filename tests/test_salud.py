from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_salud_responde_ok():
    resp = client.get("/salud")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
