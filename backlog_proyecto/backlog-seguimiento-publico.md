# Backlog — Seguimientos-BQ (servicio público de seguimiento)

> Estado: **Fases 1-3 hechas y subidas a `desarrollo`** (2026-09-01) — esqueleto, acceso a datos,
> endpoints/pantallas con barra de progreso y logo real de Bioquímica. Faltan Fase 4 (pulir estilo,
> ya adelantada en gran parte), 5 (integración con el correo de gestorBQ) y 6 (deploy). Acordado con
> Felipe 2026-09-01: la idea nació
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
| SPK-SG1 | ~~¿Repo propio o dentro de gestorBQ?~~ **Resuelto 2026-09-01**: repo propio, `github.com/FelipeMv2301/Seguimientos-BQ`, ramas `desarrollo`/`produccion`, runner self-hosted propio (`~/actions-runner-seguimientos-bq` en el servidor, mismo patrón que los otros 3 repos). | Fase 6 (deploy) |
| SPK-SG2 | Usuario Postgres de **solo lectura**, acotado a `envios_enviocourier` y `pedidos_pedido` — falta crearlo en el server. Puedo darte el SQL exacto cuando lleguemos ahí, pero lo tienes que correr tú (acceso admin a la DB de producción). | Fase 2 (conexión real) — se puede desarrollar Fase 1-2 en local contra una Postgres de prueba mientras tanto |
| SPK-SG3 | Dominio `seguimiento.bioquimica.cl` — falta el registro DNS y el bloque nuevo en el Caddyfile del servidor. | Fase 6 (deploy) |
| SPK-SG4 | Acoplamiento de esquema: este servicio lee tablas de Django **directo**, por nombre (`envios_enviocourier`, `pedidos_pedido`) — si gestorBQ migra esas tablas (renombra columnas, etc.), este servicio se puede romper en silencio, sin que nada en gestorBQ avise. No bloquea nada ahora, pero hay que tenerlo presente a futuro (ej. anotarlo en el `CLAUDE.md` de gestorBQ como advertencia). | Ninguna fase puntual — riesgo permanente a vigilar |
| SPK-SG5 | ~~Mensaje si buscan una OT de Starken~~ **Resuelto 2026-09-01**: mensaje de "no encontrado" que sugiere `starken.cl/seguimiento`. | Fase 3 |

## 3.1 Estados reales de courier (para la barra de progreso)

**MoveUP** — mapeado 2026-09-01 con dos sondeos de solo lectura contra producción: primero lo ya
guardado en `EnvioCourier` (~120 envíos, solo mostró `Cargado`/`Entregado`), después la API de MoveUP
directo con rango amplio (ene-sep 2026, 465 paquetes) — reveló un tercer estado real: **`Rechazado`**
(el destinatario rechaza el paquete al momento de la entrega). No hay documentación de MoveUP con el
enum completo; estos 3 son los únicos vistos en datos reales:

| Estado | Significado | Trato en la barra |
|---|---|---|
| *(vacío)* | Sin estado reportado todavía | Paso 0 — "Pedido recibido" |
| `Cargado` | En tránsito | Paso 1 |
| `Entregado` | Entrega exitosa (terminal) | Paso 2 (último) |
| `Rechazado` | Destinatario rechazó el paquete (terminal, negativo) | Se congela en el paso 1 + aviso aparte — **no** es "avanzar" a un paso 3 |

Si aparece un estado nuevo no visto (ej. algo cayó fuera de la muestra ene-sep), la barra no se rompe —
por defecto queda en el paso 0 (ver `app/estados.py::progreso_moveup`). Mismo método de sondeo (API con
rango de fechas amplio, no solo lo ya guardado) sirve para cuando se mapee **Chibra** — sin datos ni
documentación todavía, sin barra de progreso por ahora, solo el texto crudo de `estado_courier`.

## 4. Fases (chicas, una a la vez, cada una con sus tests)

1. ✅ **Fase 1 — Esqueleto del proyecto.** Estructura FastAPI (`app/main.py`), `requirements.txt`,
   config vía variables de entorno (`.env`/`.env.example`), `pytest` configurado con un test mínimo
   pasando (ej. un healthcheck `GET /salud`). Sin lógica de negocio todavía.
2. ✅ **Fase 2 — Acceso a datos.** `app/db.py::buscar_por_ot_en_bd`/`buscar_por_ot` (join
   `envios_enviocourier` + `pedidos_pedido`, filtrado a Chibra/MoveUP), cursor inyectado para poder
   testear sin Postgres real. 4 tests.
3. ✅ **Fase 3 — Endpoints y pantallas.** `GET /` (formulario), `GET /seguimiento?ot=` (búsqueda
   manual, vía query string — un `<form method="get">` no puede armar una ruta con path param solo),
   `GET /seguimiento/{ot}` (URL limpia, la que linkea el correo). Barra de progreso para MoveUP
   (ver 3.1) + encabezado con el logo real de Bioquímica (`logo_blanco.png`, copiado de gestorBQ) y
   la misma paleta azul/teal que ya usan los correos de notificación. 12 tests nuevos.
4. **Fase 4 — Estilo.** Gran parte ya quedó resuelta en la Fase 3 (encabezado, logo, paleta, barra de
   progreso). Pendiente solo un repaso mobile más fino si hace falta.
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
