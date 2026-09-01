import os
from zoneinfo import ZoneInfo

import psycopg2
import psycopg2.extras

_ZONA_CHILE = ZoneInfo("America/Santiago")

#Solo lectura: este servicio nunca escribe en la base de gestorBQ (ver SPK-SG2 del backlog —
#el usuario Postgres real debe crearse sin permisos de INSERT/UPDATE/DELETE).
_CONSULTA_POR_OT = """
    SELECT e.orden_transporte, e.courier, e.estado_courier, e.estado_courier_actualizado,
           p.direccion_calle, p.direccion_comuna, p.direccion_ciudad
    FROM envios_enviocourier e
    JOIN pedidos_pedido p ON p.envio_id = e.id
    WHERE e.orden_transporte = %s AND e.courier IN ('CHIBRA', 'MOVEUP')
    LIMIT 1
"""


def obtener_conexion():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


#Recibe un cursor ya abierto (RealDictCursor) en vez de abrir la conexión acá adentro — así los
#tests pueden inyectar un cursor falso sin necesitar una Postgres real.
def buscar_por_ot(cursor, ot):
    cursor.execute(_CONSULTA_POR_OT, (ot,))
    fila = cursor.fetchone()
    if fila is None:
        return None

    direccion = ", ".join(
        parte for parte in (fila["direccion_calle"], fila["direccion_comuna"], fila["direccion_ciudad"])
        if parte
    )
    #Postgres guarda el instante (timestamptz); psycopg2 lo devuelve con tzinfo del offset de sesión,
    #no necesariamente Chile. Se normaliza acá para mostrar siempre la hora de Chile al cliente.
    actualizado_en = fila["estado_courier_actualizado"]
    if actualizado_en is not None and actualizado_en.tzinfo is not None:
        actualizado_en = actualizado_en.astimezone(_ZONA_CHILE)
    return {
        "ot": fila["orden_transporte"],
        "courier": fila["courier"],
        "estado": fila["estado_courier"] or "Sin actualizaciones todavía",
        "actualizado_en": actualizado_en,
        "direccion": direccion,
    }


def abrir_cursor(conexion):
    return conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


#Abre conexión, busca y cierra — todo junto, para que las rutas de FastAPI llamen una sola función.
#En los tests de endpoints se mockea esta función completa (no hace falta Postgres para probar rutas).
def buscar_por_ot_en_bd(ot):
    conexion = obtener_conexion()
    try:
        cursor = abrir_cursor(conexion)
        return buscar_por_ot(cursor, ot)
    finally:
        conexion.close()
