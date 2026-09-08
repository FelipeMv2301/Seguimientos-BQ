from unittest.mock import patch, MagicMock

from app import cliente_gestorbq


def _respuesta_falsa(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    if status_code >= 400 and status_code != 404:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    else:
        resp.raise_for_status.return_value = None
    return resp


def test_obtener_masivo_manda_api_key_y_dias_de_retencion():
    with patch("app.cliente_gestorbq.httpx.get", return_value=_respuesta_falsa(json_data={"resultados": []})) as mock_get:
        cliente_gestorbq.obtener_masivo()

    args, kwargs = mock_get.call_args
    assert kwargs["params"] == {"dias": cliente_gestorbq.DIAS_RETENCION}
    assert kwargs["headers"]["X-API-KEY"] == cliente_gestorbq.API_KEY
    assert "/envios/api/seguimiento/masivo/" in args[0]


def test_obtener_masivo_devuelve_la_lista_de_resultados():
    filas = [{"ot": "1"}, {"ot": "2"}]
    with patch("app.cliente_gestorbq.httpx.get", return_value=_respuesta_falsa(json_data={"resultados": filas})):
        resultado = cliente_gestorbq.obtener_masivo()
    assert resultado == filas


def test_obtener_por_ot_encontrada():
    fila = {"ot": "123", "courier": "CHIBRA"}
    with patch("app.cliente_gestorbq.httpx.get", return_value=_respuesta_falsa(json_data=fila)) as mock_get:
        resultado = cliente_gestorbq.obtener_por_ot("123")
    assert resultado == fila
    assert "/envios/api/seguimiento/123/" in mock_get.call_args[0][0]


def test_obtener_por_ot_no_encontrada_devuelve_none():
    with patch("app.cliente_gestorbq.httpx.get", return_value=_respuesta_falsa(status_code=404)):
        resultado = cliente_gestorbq.obtener_por_ot("no-existe")
    assert resultado is None


def test_obtener_por_ot_error_http_distinto_de_404_propaga():
    with patch("app.cliente_gestorbq.httpx.get", return_value=_respuesta_falsa(status_code=500)):
        try:
            cliente_gestorbq.obtener_por_ot("123")
            assert False, "debería haber lanzado"
        except Exception:
            pass
