import datetime
from app.db import buscar_por_ot


class CursorFalso:
    """Simula un cursor de RealDictCursor: execute() guarda los params, fetchone() devuelve
    lo que el test configure. Así se prueba la lógica de buscar_por_ot sin una Postgres real."""

    def __init__(self, fila=None):
        self._fila = fila
        self.ultima_consulta = None
        self.ultimos_params = None

    def execute(self, consulta, params):
        self.ultima_consulta = consulta
        self.ultimos_params = params

    def fetchone(self):
        return self._fila


def test_encuentra_ot_y_arma_direccion_completa():
    cursor = CursorFalso({
        "orden_transporte": "12345",
        "courier": "CHIBRA",
        "estado_courier": "En tránsito",
        "estado_courier_actualizado": datetime.datetime(2026, 9, 1, 10, 30),
        "direccion_calle": "Av. Providencia 123",
        "direccion_comuna": "Providencia",
        "direccion_ciudad": "Santiago",
    })

    resultado = buscar_por_ot(cursor, "12345")

    assert resultado == {
        "ot": "12345",
        "courier": "CHIBRA",
        "estado": "En tránsito",
        "actualizado_en": datetime.datetime(2026, 9, 1, 10, 30),
        "direccion": "Av. Providencia 123, Providencia, Santiago",
    }
    assert cursor.ultimos_params == ("12345",)


def test_ot_inexistente_devuelve_none():
    cursor = CursorFalso(fila=None)
    assert buscar_por_ot(cursor, "no-existe") is None


def test_estado_courier_vacio_muestra_mensaje_por_defecto():
    cursor = CursorFalso({
        "orden_transporte": "999",
        "courier": "MOVEUP",
        "estado_courier": "",
        "estado_courier_actualizado": None,
        "direccion_calle": "Calle 1",
        "direccion_comuna": "",
        "direccion_ciudad": "Santiago",
    })

    resultado = buscar_por_ot(cursor, "999")

    assert resultado["estado"] == "Sin actualizaciones todavía"
    assert resultado["direccion"] == "Calle 1, Santiago"  # la comuna vacía no deja una coma colgando


def test_consulta_filtra_solo_chibra_y_moveup():
    cursor = CursorFalso(fila=None)
    buscar_por_ot(cursor, "1")
    assert "CHIBRA" in cursor.ultima_consulta
    assert "MOVEUP" in cursor.ultima_consulta
