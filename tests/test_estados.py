from app.estados import progreso_moveup, mensaje_negativo_moveup, PASOS_MOVEUP, PASO_ANTES_DE_NEGATIVO


def test_sin_estado_todavia_queda_en_el_primer_paso():
    assert progreso_moveup("") == 0
    assert progreso_moveup(None) == 0


def test_programado_es_el_segundo_paso():
    assert progreso_moveup("Programado") == 1


def test_retirado_es_el_tercer_paso():
    assert progreso_moveup("Retirado") == 2


def test_recepcionado_en_bodega_es_el_cuarto_paso():
    assert progreso_moveup("Recepcionado en bodega") == 3


def test_cargado_es_el_quinto_paso():
    assert progreso_moveup("Cargado") == 4


def test_en_camino_es_el_sexto_paso():
    assert progreso_moveup("En Camino") == 5


def test_entregado_es_el_ultimo_paso():
    assert progreso_moveup("Entregado") == len(PASOS_MOVEUP) - 1


def test_entregado_a_blue_express_es_el_mismo_ultimo_paso_que_entregado():
    """Entrega exitosa igual — MoveUP solo subcontrató el último tramo. No es un paso aparte ni se
    ignora (ignorarlo lo dejaría en el paso 0, que es lo opuesto a la realidad)."""
    assert progreso_moveup("Entregado a Blue Express") == progreso_moveup("Entregado")


def test_estado_desconocido_no_rompe_y_queda_en_el_primer_paso():
    """Si MoveUP manda un estado que nunca vimos, no debe reventar — solo no avanza la barra.
    Puede seguir habiendo estados sin descubrir (esto no es el enum completo de MoveUP)."""
    assert progreso_moveup("Un estado nuevo que no existía") == 0


def test_rechazado_no_entregado_y_devolucion_son_desenlaces_negativos():
    assert mensaje_negativo_moveup("Rechazado") is not None
    assert mensaje_negativo_moveup("No Entregado") is not None
    assert mensaje_negativo_moveup("Devolución") is not None


def test_cada_desenlace_negativo_tiene_su_propio_mensaje():
    """No todos significan lo mismo, aunque los tres congelen la barra en el mismo lugar."""
    mensajes = {
        mensaje_negativo_moveup("Rechazado"),
        mensaje_negativo_moveup("No Entregado"),
        mensaje_negativo_moveup("Devolución"),
    }
    assert len(mensajes) == 3  # los 3 textos son distintos entre sí


def test_estados_positivos_no_son_desenlace_negativo():
    assert mensaje_negativo_moveup("Entregado") is None
    assert mensaje_negativo_moveup("Entregado a Blue Express") is None
    assert mensaje_negativo_moveup("Cargado") is None
    assert mensaje_negativo_moveup("") is None


def test_paso_antes_de_negativo_es_en_camino():
    assert PASOS_MOVEUP[PASO_ANTES_DE_NEGATIVO] == "En Camino"
