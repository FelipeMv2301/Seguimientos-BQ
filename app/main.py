from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import cache, estados, scheduler

BASE_DIR = Path(__file__).parent


#Arranca el scheduler (sync inicial + cada N min) al levantar la app, lo apaga al bajarla — así el
#cache nunca queda corriendo huérfano si uvicorn recarga o el proceso termina.
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.iniciar()
    yield
    scheduler.detener()


app = FastAPI(title="Seguimientos-BQ", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/salud")
def salud():
    return {"status": "ok"}


#Arma el contexto de plantilla a partir del resultado crudo de la DB — agrega nombre legible del
#courier y, si es MoveUP (único con estados mapeados hoy), los pasos de la barra de progreso.
def _armar_contexto(ot, resultado):
    contexto = {"buscado": ot, "resultado": resultado, "pasos": None, "paso_actual": None, "mensaje_negativo": None}
    if resultado is None:
        return contexto

    resultado["courier_legible"] = estados.NOMBRE_COURIER.get(resultado["courier"], resultado["courier"])
    if resultado["courier"] in estados.COURIERS_CON_PROGRESO:
        contexto["mensaje_negativo"] = estados.mensaje_negativo_moveup(resultado["estado"])
        #Un desenlace negativo no es "avanzar" en la barra — se congela en el último paso positivo
        #alcanzado (PASO_ANTES_DE_NEGATIVO) y se avisa aparte, con el mensaje específico del caso.
        contexto["pasos"] = estados.PASOS_MOVEUP
        contexto["paso_actual"] = (
            estados.PASO_ANTES_DE_NEGATIVO if contexto["mensaje_negativo"] else estados.progreso_moveup(resultado["estado"])
        )
    return contexto


@app.get("/", response_class=HTMLResponse)
def formulario(request: Request):
    return templates.TemplateResponse(request, "index.html", _armar_contexto(None, None))


@app.get("/seguimiento", response_class=HTMLResponse)
def buscar(request: Request, ot: str):
    resultado = cache.buscar(ot)
    return templates.TemplateResponse(request, "index.html", _armar_contexto(ot, resultado))


#Lo que linkea el correo de gestorBQ: URL limpia con la OT en la ruta. Reusa el mismo render que
#la búsqueda manual, sin ida y vuelta (nada de redirect) — misma pantalla, mismo resultado.
@app.get("/seguimiento/{ot}", response_class=HTMLResponse)
def ver_seguimiento(request: Request, ot: str):
    resultado = cache.buscar(ot)
    return templates.TemplateResponse(request, "index.html", _armar_contexto(ot, resultado))
