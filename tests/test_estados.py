from app.estados import progreso_moveup, es_rechazo_moveup, PASOS_MOVEUP


def test_sin_estado_todavia_queda_en_el_primer_paso():
    assert progreso_moveup("") == 0
    assert progreso_moveup(None) == 0


def test_cargado_es_el_segundo_paso():
    assert progreso_moveup("Cargado") == 1


def test_entregado_es_el_ultimo_paso():
    assert progreso_moveup("Entregado") == len(PASOS_MOVEUP) - 1


def test_estado_desconocido_no_rompe_y_queda_en_el_primer_paso():
    """Si MoveUP manda un estado que nunca vimos, no debe reventar — solo no avanza la barra."""
    assert progreso_moveup("Un estado nuevo que no existía") == 0


def test_rechazado_se_detecta_como_rechazo_no_como_progreso():
    assert es_rechazo_moveup("Rechazado") is True
    assert es_rechazo_moveup("Entregado") is False
    assert es_rechazo_moveup("Cargado") is False
