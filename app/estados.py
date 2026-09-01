#Mapeo de estado de courier -> paso de la barra de progreso. Presentación pura, no toca la DB.
#
#MoveUP: mapeado con datos reales de producción (2026-09-01), en varias rondas de sondeo de solo
#lectura (Felipe además lo confirmó viendo paquetes en vivo en el panel de MoveUP/gestor-despachos-
#retiros, no de una lista de documentación — MoveUP no publica el enum completo de estados):
#  1. Lo ya guardado en EnvioCourier (~120 envíos): solo "Cargado"/"Entregado".
#  2. API de MoveUP, rango ene-sep 2026 (465 paquetes): + "Rechazado" (1 caso) — el destinatario
#     rechaza el paquete; NO es "avanzar" en la barra, es una salida negativa, se muestra aparte.
#  3. Filtro status="Retirado" (exacto, case-sensitive — "retirado"/"RETIRADO" no matchean): 1 paquete
#     real, ya había cambiado de estado al reintentar segundos después — paso breve de "retirado del
#     origen", anterior a "Cargado".
#  4. Paquetes recién creados (últimos 3 días, sin filtro de estado): + "En Camino" (11 de 33) —
#     viene después de "Cargado" (se carga al vehículo, después queda en camino/reparto).
#Si aparece un estado nuevo no mapeado, el paso por defecto es 0 (no se rompe, solo no avanza la
#barra) — puede seguir habiendo estados sin descubrir todavía, esto no pretende ser el enum completo.
#
#Chibra: TODO — sin estados mapeados todavía, no hay evidencia real ni documentación. Chibra no
#muestra barra de progreso por ahora, solo el texto crudo de estado_courier.
PASOS_MOVEUP = ["Pedido recibido", "Retirado", "Cargado", "En Camino", "Entregado"]

_ORDEN_MOVEUP = {"Retirado": 1, "Cargado": 2, "En Camino": 3, "Entregado": 4}

ESTADO_RECHAZADO_MOVEUP = "Rechazado"

#Último paso alcanzado antes de un rechazo — "En Camino" (índice de PASOS_MOVEUP), ya que el rechazo
#ocurre al momento de la entrega, después de que el paquete sale en reparto.
PASO_ANTES_DE_RECHAZO = 3


def progreso_moveup(estado_courier):
    return _ORDEN_MOVEUP.get(estado_courier, 0)


def es_rechazo_moveup(estado_courier):
    return estado_courier == ESTADO_RECHAZADO_MOVEUP


#Couriers con barra de progreso mapeada. Se usa desde main.py para decidir si armar la barra.
COURIERS_CON_PROGRESO = {"MOVEUP"}

NOMBRE_COURIER = {"MOVEUP": "MoveUP", "CHIBRA": "Chibra"}
