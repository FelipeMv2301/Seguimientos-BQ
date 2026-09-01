from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db, estados

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Seguimientos-BQ")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/salud")
def salud():
    return {"status": "ok"}


#Arma el contexto de plantilla a partir del resultado crudo de la DB — agrega nombre legible del
#courier y, si es MoveUP (único con estados mapeados hoy), los pasos de la barra de progreso.
def _armar_contexto(ot, resultado):
    contexto = {"buscado": ot, "resultado": resultado, "pasos": None, "paso_actual": None, "rechazado": False}
    if resultado is None:
        return contexto

    resultado["courier_legible"] = estados.NOMBRE_COURIER.get(resultado["courier"], resultado["courier"])
    if resultado["courier"] in estados.COURIERS_CON_PROGRESO:
        contexto["rechazado"] = estados.es_rechazo_moveup(resultado["estado"])
        #Rechazado no es "avanzar" en la barra — se congela en el último paso alcanzado antes del
        #rechazo (hoy siempre "Cargado", es el único paso previo posible) y se avisa aparte.
        contexto["pasos"] = estados.PASOS_MOVEUP
        contexto["paso_actual"] = 1 if contexto["rechazado"] else estados.progreso_moveup(resultado["estado"])
    return contexto


@app.get("/", response_class=HTMLResponse)
def formulario(request: Request):
    return templates.TemplateResponse(request, "index.html", _armar_contexto(None, None))


@app.get("/seguimiento", response_class=HTMLResponse)
def buscar(request: Request, ot: str):
    resultado = db.buscar_por_ot_en_bd(ot)
    return templates.TemplateResponse(request, "index.html", _armar_contexto(ot, resultado))


#Lo que linkea el correo de gestorBQ: URL limpia con la OT en la ruta. Reusa el mismo render que
#la búsqueda manual, sin ida y vuelta (nada de redirect) — misma pantalla, mismo resultado.
@app.get("/seguimiento/{ot}", response_class=HTMLResponse)
def ver_seguimiento(request: Request, ot: str):
    resultado = db.buscar_por_ot_en_bd(ot)
    return templates.TemplateResponse(request, "index.html", _armar_contexto(ot, resultado))
