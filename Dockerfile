FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

ENV PYTHONPATH=/app/src

COPY alembic ./alembic
COPY alembic.ini .
COPY --from=ghcr.io/ufoscout/docker-compose-wait:latest /wait /wait
COPY entrypoint.sh .

RUN chmod +x ./entrypoint.sh
CMD /wait && ./entrypoint.sh
