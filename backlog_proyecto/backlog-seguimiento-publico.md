# Backlog — Seguimientos-BQ (servicio público de seguimiento)

> Estado: **Recién arrancando, sin código todavía.** Acordado con Felipe 2026-09-01: la idea nació
> dentro de `gestorBQ` (ver `backlog_proyecto/backlog-servicio-seguimiento-publico.md` en ese repo,
> 2026-08-25) pero se decidió que **no vive ahí** — gestorBQ hoy es 100% autenticado (Google OAuth
> `@bioquimica.cl`), y este es un servicio público sin login. Se gradúa a proyecto propio, en esta
> carpeta (`C:\Users\920562\Documents\proyectos\Seguimientos-BQ`), stack **FastAPI + frontend server-
> rendered (Jinja2)**, dominio pensado: `seguimiento.bioquimica.cl`.

## 1. Objetivo

Un cliente que recibió un despacho por **Chibra** o **MoveUP** (ninguno de los dos tiene tracking
público propio — a diferencia de Starken, que sí) puede buscar el estado de su envío escribiendo
**solo el N° de OT** — sin segundo factor, decisión ya tomada. El correo de notificación de gestorBQ
va a linkear directo a `seguimiento.bioquimica.cl/seguimiento/<OT>` (paso de integración al final,
toca el otro repo — ver Fase 5).

**Datos a mostrar** (leídos de la misma Postgres que usa gestorBQ, en modo **solo lectura**):
OT, dirección de despacho, courier, estado, y hora de la última actualización de estado.

## 2. Decisiones ya tomadas (no reabrir sin motivo nuevo)

- **Servicio aparte, no dentro de gestorBQ** — para no meter una puerta pública sin login en el
  mismo proceso/codebase que maneja datos sensibles (SAP, credenciales de courier, etc.).
- **Stack**: FastAPI (no Django completo — este servicio no necesita ORM propio, admin, ni auth).
  Frontend server-rendered con Jinja2, sin build de JS/CSS (es una sola pantalla).
- **Buscar solo por OT**, sin segundo factor (RUT, email, etc.) — ya evaluado el riesgo (alguien que
  adivine/enumere OTs ve dirección+estado ajenos) y aceptado, mismo criterio que ya se había hablado
  en la idea original.
- **Solo Chibra y MoveUP** — Starken ya tiene su propio tracking público
  (`https://www.starken.cl/seguimiento?codigo=...`), no se duplica acá.
- **Acceso a datos: conexión directa de solo lectura a la Postgres de gestorBQ** (no un endpoint HTTP
  expuesto por gestorBQ) — decisión tomada para no agregar superficie nueva al repo principal. Implica
  un usuario Postgres propio, acotado, sin permisos de escritura (ver spike SPK-SG2).

## 3. Spikes abiertos (resolver antes de la fase que bloquean)

| ID | Pregunta | Bloquea |
|---|---|---|
| SPK-SG1 | ¿Repo de GitHub propio (con su propio pipeline de Actions), o vive en el mismo repo de gestorBQ como carpeta aparte? Repo propio es más limpio (deploy independiente) pero es infraestructura nueva. | Fase 6 (deploy) |
| SPK-SG2 | Usuario Postgres de **solo lectura**, acotado a `envios_enviocourier` y `pedidos_pedido` — falta crearlo en el server. Puedo darte el SQL exacto cuando lleguemos ahí, pero lo tienes que correr tú (acceso admin a la DB de producción). | Fase 2 (conexión real) — se puede desarrollar Fase 1-2 en local contra una Postgres de prueba mientras tanto |
| SPK-SG3 | Dominio `seguimiento.bioquimica.cl` — falta el registro DNS y el bloque nuevo en el Caddyfile del servidor. | Fase 6 (deploy) |
| SPK-SG4 | Acoplamiento de esquema: este servicio lee tablas de Django **directo**, por nombre (`envios_enviocourier`, `pedidos_pedido`) — si gestorBQ migra esas tablas (renombra columnas, etc.), este servicio se puede romper en silencio, sin que nada en gestorBQ avise. No bloquea nada ahora, pero hay que tenerlo presente a futuro (ej. anotarlo en el `CLAUDE.md` de gestorBQ como advertencia). | Ninguna fase puntual — riesgo permanente a vigilar |
| SPK-SG5 | Si alguien busca una OT que es de **Starken** (no la tenemos acá), ¿mensaje genérico de "no encontrado", o uno que sugiera "prueba en starken.cl/seguimiento"? | Fase 3 (pantalla de resultado) |

## 4. Fases (chicas, una a la vez, cada una con sus tests)

1. **Fase 1 — Esqueleto del proyecto.** Estructura FastAPI (`app/main.py`), `requirements.txt`,
   config vía variables de entorno (`.env`/`.env.example`), `pytest` configurado con un test mínimo
   pasando (ej. un healthcheck `GET /salud`). Sin lógica de negocio todavía.
2. **Fase 2 — Acceso a datos.** Función `buscar_por_ot(ot)` que consulta Postgres (join
   `envios_enviocourier` + `pedidos_pedido`, filtrado a Chibra/MoveUP) y devuelve el resultado o
   `None`. Tests contra una base de prueba (no la real) — con datos de ejemplo insertados a mano en
   el test.
3. **Fase 3 — Endpoints y pantallas.** `GET /` (formulario vacío), `GET /seguimiento/{ot}` (busca y
   muestra resultado, o "no encontrado"). Tests con `TestClient` de FastAPI, mockeando la función de
   Fase 2.
4. **Fase 4 — Estilo.** CSS mínimo, mobile-first (se abre desde el celular, viene de un correo).
5. **Fase 5 — Integración con gestorBQ.** Cambio chico en el OTRO repo
   (`integraciones/email_client.py::_generar_track_url` o el llamado que arma el link de seguimiento
   en el correo) para que Chibra/MoveUP linkeen a `seguimiento.bioquimica.cl/seguimiento/<OT>` en vez
   de no tener link. Se hace en gestorBQ, no acá.
6. **Fase 6 — Despliegue.** Resolver SPK-SG1/SPK-SG2/SPK-SG3, Dockerfile, y (si repo propio) su
   pipeline de CI/CD.

## 5. Fuera de alcance

- Seguimiento de Starken (ya tiene el suyo).
- Cualquier acción de escritura (anular, notificar, etc.) — esto es 100% lectura.
- Autenticación de ningún tipo — es intencionalmente público.
