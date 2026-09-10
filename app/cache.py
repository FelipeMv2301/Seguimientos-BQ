import datetime
import logging
from zoneinfo import ZoneInfo

from app import cliente_gestorbq

logger = logging.getLogger("app.cache")

_ZONA_CHILE = ZoneInfo("America/Santiago")

#Cache en memoria, no en disco: no es la fuente de verdad (gestorBQ/Postgres lo es), así que
#perderlo en un reinicio/redeploy no es pérdida de datos — el próximo sync completo lo rearma solo
#(ver Fase 7 del backlog, decisión de Felipe 2026-09-08: sin Volume de Railway, sin DB propia).
_cache = {}


#Reemplaza TODO el cache de una — no mezcla con lo anterior. Lo viejo que ya no venga en la
#respuesta (fuera de la ventana de días) desaparece solo, sin lógica de expiración aparte.
def sincronizar():
    global _cache
    filas = cliente_gestorbq.obtener_masivo()
    _cache = {fila["ot"]: fila for fila in filas}
    logger.info("Sincronización completa: %s OT en cache.", len(_cache))


def _esta_vigente(fila):
    creado_en = datetime.datetime.fromisoformat(fila["creado_en"])
    limite = datetime.datetime.now(creado_en.tzinfo) - datetime.timedelta(days=cliente_gestorbq.DIAS_RETENCION)
    return creado_en >= limite


#Misma forma que devolvía app/db.py::buscar_por_ot antes de este cambio — así main.py y el template
#no se tocan, solo cambia de dónde sale el dato.
def _normalizar(fila):
    if fila is None:
        return None

    direccion = ", ".join(
        parte for parte in (fila.get("direccion_calle"), fila.get("direccion_comuna"), fila.get("direccion_ciudad"))
        if parte
    )
    actualizado_en = fila.get("actualizado_en")
    if actualizado_en:
        actualizado_en = datetime.datetime.fromisoformat(actualizado_en).astimezone(_ZONA_CHILE)

    return {
        "ot": fila["ot"],
        "courier": fila["courier"],
        "estado": fila.get("estado") or "Sin actualizaciones todavía",
        #Código crudo (hoy solo Chibra lo manda) — para armar la barra de progreso por código en vez
        #de parsear el texto largo de "estado" (app/estados.py::progreso_chibra).
        "estado_codigo": fila.get("estado_codigo") or "",
        "actualizado_en": actualizado_en,
        "direccion": direccion,
    }


#Cache primero (validando vigencia por fecha — autolimpieza puntual, sin esperar al próximo sync
#completo); si no está o venció, cae al endpoint individual. None si tampoco existe ahí.
def buscar(ot):
    fila = _cache.get(ot)
    if fila is not None:
        if _esta_vigente(fila):
            return _normalizar(fila)
        _cache.pop(ot, None)

    return _normalizar(cliente_gestorbq.obtener_por_ot(ot))
