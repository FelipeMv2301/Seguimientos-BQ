import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

from app import cache

logger = logging.getLogger("app.scheduler")

INTERVALO_MINUTOS = int(os.environ.get("SYNC_INTERVALO_MINUTOS", "5"))

_scheduler = None


def _job_sincronizar():
    try:
        cache.sincronizar()
    except Exception:
        logger.exception("Sincronización con gestorBQ falló — se reintenta en el próximo ciclo.")


#Un solo proceso uvicorn (sin workers de gunicorn como gestorBQ), así que no hace falta el lock por
#DB que sí necesita gestorBQ — no hay contención entre procesos que resolver acá.
def iniciar():
    global _scheduler
    if _scheduler is not None:
        return  # ya está corriendo (evita duplicar jobs si algo llama iniciar() dos veces)

    _job_sincronizar()  # sync inicial síncrono: no servir con el cache vacío desde el arranque

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_job_sincronizar, "interval", minutes=INTERVALO_MINUTOS, id="sincronizar_seguimiento")
    _scheduler.start()
    logger.info("Scheduler iniciado: sincroniza cada %s minuto(s).", INTERVALO_MINUTOS)


def detener():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
