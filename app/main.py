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


#Un registro por courier con progreso — cada uno arma su barra a partir de la clave que le
#corresponda (MoveUP: el estado tal cual, ya viene legible; Chibra: el código corto, más confiable
#que parsear el texto largo). Sumar un courier con progreso = agregar su entrada acá, sin tocar
#_armar_contexto.
_BARRA_PROGRESO_COURIER = {
    "MOVEUP": lambda resultado: (
        estados.PASOS_MOVEUP,
        estados.mensaje_negativo_moveup(resultado["estado"]),
        estados.progreso_moveup(resultado["estado"]),
        estados.PASO_ANTES_DE_NEGATIVO_MOVEUP,
    ),
    "CHIBRA": lambda resultado: (
        estados.PASOS_CHIBRA,
        estados.mensaje_negativo_chibra(resultado.get("estado_codigo")),
        estados.progreso_chibra(resultado.get("estado_codigo")),
        estados.PASO_ANTES_DE_NEGATIVO_CHIBRA,
    ),
}


#Arma el contexto de plantilla a partir del resultado crudo de la API de gestorBQ — agrega nombre
#legible del courier y, si tiene progreso mapeado, los pasos de la barra.
def _armar_contexto(ot, resultado):
    contexto = {"buscado": ot, "resultado": resultado, "pasos": None, "paso_actual": None, "mensaje_negativo": None}
    if resultado is None:
        return contexto

    resultado["courier_legible"] = estados.NOMBRE_COURIER.get(resultado["courier"], resultado["courier"])
    armar_barra = _BARRA_PROGRESO_COURIER.get(resultado["courier"])
    if armar_barra:
        pasos, mensaje_negativo, paso_actual, paso_antes_de_negativo = armar_barra(resultado)
        contexto["pasos"] = pasos
        contexto["mensaje_negativo"] = mensaje_negativo
        #Un desenlace negativo no es "avanzar" en la barra — se congela en el último paso positivo
        #alcanzado y se avisa aparte, con el mensaje específico del caso.
        contexto["paso_actual"] = paso_antes_de_negativo if mensaje_negativo else paso_actual
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
