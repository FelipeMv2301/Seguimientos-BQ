import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

_RESULTADO_MOVEUP = {
    "ot": "555",
    "courier": "MOVEUP",
    "estado": "Cargado",
    "actualizado_en": datetime.datetime(2026, 9, 1, 10, 30),
    "direccion": "Av. Providencia 123, Providencia, Santiago",
}


def test_formulario_no_muestra_resultado_de_entrada():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "resultado" not in resp.text.lower() or "No encontramos" not in resp.text


def test_buscar_por_query_string_encuentra_y_muestra_progreso_moveup():
    with patch("app.main.db.buscar_por_ot_en_bd", return_value=_RESULTADO_MOVEUP):
        resp = client.get("/seguimiento", params={"ot": "555"})
    assert resp.status_code == 200
    assert "555" in resp.text
    assert "MoveUP" in resp.text
    assert "Cargado" in resp.text
    assert "Av. Providencia 123" in resp.text


def test_ver_seguimiento_por_url_directa_del_correo():
    with patch("app.main.db.buscar_por_ot_en_bd", return_value=_RESULTADO_MOVEUP) as mock_buscar:
        resp = client.get("/seguimiento/555")
    assert resp.status_code == 200
    mock_buscar.assert_called_once_with("555")
    assert "555" in resp.text


def test_ot_no_encontrada_muestra_mensaje():
    with patch("app.main.db.buscar_por_ot_en_bd", return_value=None):
        resp = client.get("/seguimiento/no-existe")
    assert resp.status_code == 200
    assert "No encontramos" in resp.text
    assert "starken.cl" in resp.text


def test_moveup_rechazado_muestra_aviso_y_no_avanza_como_entregado():
    resultado_rechazado = {**_RESULTADO_MOVEUP, "estado": "Rechazado"}
    with patch("app.main.db.buscar_por_ot_en_bd", return_value=resultado_rechazado):
        resp = client.get("/seguimiento/555")
    assert "rechazó este paquete" in resp.text
    assert "Rechazado" in resp.text


def test_chibra_no_muestra_barra_de_progreso():
    resultado_chibra = {**_RESULTADO_MOVEUP, "courier": "CHIBRA", "estado": "En bodega"}
    with patch("app.main.db.buscar_por_ot_en_bd", return_value=resultado_chibra):
        resp = client.get("/seguimiento/555")
    assert "Chibra" in resp.text
    assert "En bodega" in resp.text
    assert "progreso" not in resp.text  # sin estados mapeados todavía, no se arma la barra
