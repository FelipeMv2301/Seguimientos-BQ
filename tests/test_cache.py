import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from app import cache


@pytest.fixture(autouse=True)
def _cache_vacio():
    """El cache es un dict a nivel de módulo — sin esto, un test deja datos que ensucia el
    siguiente (mismo problema que tendría cualquier estado global no reseteado entre tests)."""
    cache._cache = {}
    yield
    cache._cache = {}


def _fila_reciente(ot="555", **extra):
    base = {
        "ot": ot,
        "courier": "MOVEUP",
        "estado": "Cargado",
        "actualizado_en": "2026-09-06T14:32:00+00:00",
        "creado_en": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "direccion_calle": "Av. Providencia 123",
        "direccion_comuna": "Providencia",
        "direccion_ciudad": "Santiago",
    }
    base.update(extra)
    return base


def test_sincronizar_reemplaza_el_cache_completo():
    cache._cache = {"OT-VIEJA": _fila_reciente(ot="OT-VIEJA")}
    with patch("app.cache.cliente_gestorbq.obtener_masivo", return_value=[_fila_reciente(ot="OT-NUEVA")]):
        cache.sincronizar()
    assert "OT-VIEJA" not in cache._cache
    assert "OT-NUEVA" in cache._cache


def test_buscar_encuentra_en_cache_sin_llamar_al_individual():
    cache._cache = {"555": _fila_reciente()}
    with patch("app.cache.cliente_gestorbq.obtener_por_ot") as mock_individual:
        resultado = cache.buscar("555")
    assert not mock_individual.called
    assert resultado["ot"] == "555"
    assert resultado["courier"] == "MOVEUP"
    assert resultado["direccion"] == "Av. Providencia 123, Providencia, Santiago"


def test_buscar_normaliza_actualizado_en_a_hora_chile():
    cache._cache = {"555": _fila_reciente(actualizado_en="2026-09-06T14:32:00+00:00")}
    resultado = cache.buscar("555")
    assert resultado["actualizado_en"].tzinfo.key == "America/Santiago"
    # mismo instante que el guardado, la igualdad de datetimes aware compara el instante
    assert resultado["actualizado_en"] == datetime.datetime(2026, 9, 6, 14, 32, tzinfo=datetime.timezone.utc)


def test_buscar_sin_actualizado_en_no_revienta():
    cache._cache = {"555": _fila_reciente(actualizado_en=None)}
    resultado = cache.buscar("555")
    assert resultado["actualizado_en"] is None


def test_buscar_estado_vacio_muestra_mensaje_por_defecto():
    cache._cache = {"555": _fila_reciente(estado="")}
    resultado = cache.buscar("555")
    assert resultado["estado"] == "Sin actualizaciones todavía"


def test_buscar_no_encontrada_en_cache_cae_al_endpoint_individual():
    with patch("app.cache.cliente_gestorbq.obtener_por_ot", return_value=_fila_reciente(ot="999")) as mock_individual:
        resultado = cache.buscar("999")
    mock_individual.assert_called_once_with("999")
    assert resultado["ot"] == "999"


def test_buscar_ni_en_cache_ni_en_gestorbq_devuelve_none():
    with patch("app.cache.cliente_gestorbq.obtener_por_ot", return_value=None):
        resultado = cache.buscar("no-existe")
    assert resultado is None


def test_entrada_vencida_se_autolimpia_y_cae_al_individual():
    """El sync sync repone el cache cada N minutos, pero si por algo falla varias veces seguidas,
    cada entrada igual se revisa por su propia edad (pedido de Felipe 2026-09-08) — no depende
    únicamente de que el próximo sync completo la reemplace."""
    vieja = _fila_reciente(
        ot="555",
        creado_en=(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)).isoformat(),
    )
    cache._cache = {"555": vieja}

    with patch("app.cache.cliente_gestorbq.obtener_por_ot", return_value=_fila_reciente(ot="555")) as mock_individual:
        cache.buscar("555")

    mock_individual.assert_called_once_with("555")
    assert "555" not in cache._cache  # se sacó del cache al detectarse vencida
