#Mapeo de estado de courier -> paso de la barra de progreso. Presentación pura, no toca la DB.
#
#MoveUP: mapeado con datos reales de producción (2026-09-01). Primer sondeo sobre lo ya guardado en
#EnvioCourier (~120 envíos) solo mostró "Cargado"/"Entregado". Un segundo sondeo directo a la API de
#MoveUP (rango ene-sep 2026, 465 paquetes) encontró un tercer estado real: "Rechazado" (1 caso) — el
#destinatario rechaza el paquete. No es "avanzar" en la barra, es una salida negativa — se muestra
#aparte, no como el último paso. No hay documentación de MoveUP con más estados que estos tres; si
#aparece uno nuevo no mapeado, el paso por defecto es 0 (no se rompe, solo no avanza la barra).
#
#Chibra: TODO — sin estados mapeados todavía, no hay evidencia real ni documentación. Chibra no
#muestra barra de progreso por ahora, solo el texto crudo de estado_courier.
PASOS_MOVEUP = ["Pedido recibido", "Cargado", "Entregado"]

_ORDEN_MOVEUP = {"Cargado": 1, "Entregado": 2}

ESTADO_RECHAZADO_MOVEUP = "Rechazado"


def progreso_moveup(estado_courier):
    return _ORDEN_MOVEUP.get(estado_courier, 0)


def es_rechazo_moveup(estado_courier):
    return estado_courier == ESTADO_RECHAZADO_MOVEUP


#Couriers con barra de progreso mapeada. Se usa desde main.py para decidir si armar la barra.
COURIERS_CON_PROGRESO = {"MOVEUP"}

NOMBRE_COURIER = {"MOVEUP": "MoveUP", "CHIBRA": "Chibra"}
