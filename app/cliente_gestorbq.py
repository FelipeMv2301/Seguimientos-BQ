import os

import httpx

#Base pública de gestorBQ (nunca por la red interna del servidor — así funciona igual si este
#servicio corre en el mismo servidor o en Railway, ver Fase 7 del backlog).
BASE_URL = os.environ.get("GESTORBQ_API_URL", "").rstrip("/")
API_KEY = os.environ.get("SEGUIMIENTO_API_KEY", "")
#Mismos días para pedir el masivo y para la autolimpieza local (app/cache.py) — una sola fuente de
#verdad del tamaño de la ventana, acordado con Felipe 2026-09-08.
DIAS_RETENCION = int(os.environ.get("DIAS_RETENCION", "25"))

_TIMEOUT_MASIVO = 30.0
_TIMEOUT_INDIVIDUAL = 10.0


def _cabeceras():
    return {"X-API-KEY": API_KEY}


#Trae todo lo sincronizable de una vez (últimos DIAS_RETENCION días) — lo que el scheduler llama
#cada N minutos para rearmar el cache en memoria completo. Deja que un error de red/HTTP suba tal
#cual (app/scheduler.py lo captura y loguea, sin tumbar el proceso).
def obtener_masivo():
    respuesta = httpx.get(
        f"{BASE_URL}/envios/api/seguimiento/masivo/",
        params={"dias": DIAS_RETENCION},
        headers=_cabeceras(),
        timeout=_TIMEOUT_MASIVO,
    )
    respuesta.raise_for_status()
    return respuesta.json()["resultados"]


#Fallback cuando la OT no está en el cache local (más vieja que la ventana, o llegó entre dos
#sincronizaciones). None si gestorBQ no la tiene — nunca una excepción por "no encontrado".
def obtener_por_ot(ot):
    respuesta = httpx.get(
        f"{BASE_URL}/envios/api/seguimiento/{ot}/",
        headers=_cabeceras(),
        timeout=_TIMEOUT_INDIVIDUAL,
    )
    if respuesta.status_code == 404:
        return None
    respuesta.raise_for_status()
    return respuesta.json()
