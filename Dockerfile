FROM python:3.12-slim

WORKDIR /app

#Ya no necesita libpq-dev/gcc (sin psycopg2 desde Fase 7 — sincroniza vía HTTPS, no Postgres directo).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
#Forma shell (no exec) para que $PORT se expanda — Railway lo inyecta y espera que el proceso
#escuche ahí; en self-hosted (docker-compose, sin $PORT seteado) cae al 8000 de siempre.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
