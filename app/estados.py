#Mapeo de estado de courier -> paso de la barra de progreso. Presentación pura, no toca la DB.
#
#MoveUP: actualizado 2026-09-08 con el enum REAL de su API (PackageStatus), que Felipe consiguió
#directo — ya no es un sondeo de datos en producción como la primera versión de este mapeo (ver
#backlog-seguimiento-publico.md sección 3.1 para el historial de cómo se armó antes de tener esto).
#Valores reales: Cargado, Programado, En Camino, Entregado, Devolución, No Entregado, Rechazado,
#Retirado, Recepcionado en bodega, Entregado a Blue Express.
#
#Decisiones (acordadas con Felipe 2026-09-08):
#- "Entregado a Blue Express" es una entrega EXITOSA (MoveUP subcontrató el último tramo) — mismo
#  paso final y mismo trato que "Entregado", no un estado aparte ni "ignorado" (ignorarlo lo dejaría
#  en el paso 0, que es lo opuesto a la realidad: el paquete YA se entregó).
#- "Rechazado", "No Entregado" y "Devolución" son desenlaces NEGATIVOS y terminales — no son "avanzar"
#  en la barra. Se congela en el último paso positivo alcanzado (PASO_ANTES_DE_NEGATIVO) y se avisa
#  aparte, con un mensaje específico por caso (no todos significan lo mismo).
#- Solo se tiene el estado ACTUAL (no el historial de eventos), así que no se puede saber con certeza
#  en qué paso positivo iba el paquete antes de un desenlace negativo — se asume que fue "En Camino"
#  (el desenlace ocurre al momento de la entrega, ya en reparto), mismo criterio para los 3 casos.
#
#Chibra: TODO — sin estados mapeados todavía, no hay evidencia real ni documentación. Chibra no
#muestra barra de progreso por ahora, solo el texto crudo de estado_courier.
PASOS_MOVEUP = [
    "Pedido recibido", "Programado", "Retirado", "Recepcionado en bodega", "Cargado", "En Camino", "Entregado",
]

_ORDEN_MOVEUP = {
    "Programado": 1,
    "Retirado": 2,
    "Recepcionado en bodega": 3,
    "Cargado": 4,
    "En Camino": 5,
    "Entregado": 6,
    "Entregado a Blue Express": 6,  # entrega exitosa igual, solo cambia quién hizo el último tramo
}

#Mensaje específico por desenlace negativo — no todos significan lo mismo, aunque los tres congelen
#la barra en el mismo lugar.
_MENSAJE_NEGATIVO_MOVEUP = {
    "Rechazado": "El destinatario rechazó este paquete al momento de la entrega.",
    "No Entregado": "No fue posible entregar este paquete.",
    "Devolución": "Este paquete está en proceso de devolución.",
}

#Último paso positivo alcanzado antes de un desenlace negativo — "En Camino" (índice de PASOS_MOVEUP).
PASO_ANTES_DE_NEGATIVO = 5


def progreso_moveup(estado_courier):
    return _ORDEN_MOVEUP.get(estado_courier, 0)


#None si el estado no es un desenlace negativo — el mensaje específico si sí lo es. Reemplaza a la
#vieja es_rechazo_moveup (booleana, solo cubría "Rechazado") ahora que hay 3 casos con mensajes propios.
def mensaje_negativo_moveup(estado_courier):
    return _MENSAJE_NEGATIVO_MOVEUP.get(estado_courier)


#Couriers con barra de progreso mapeada. Se usa desde main.py para decidir si armar la barra.
COURIERS_CON_PROGRESO = {"MOVEUP"}

NOMBRE_COURIER = {"MOVEUP": "MoveUP", "CHIBRA": "Chibra"}
