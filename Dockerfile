FROM python:3.11.9-slim-bookworm AS builder

WORKDIR /build
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11.9-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install/ /usr/local/
COPY . .

RUN groupadd --gid 10001 api \
    && useradd --uid 10001 --gid api --no-create-home --shell /usr/sbin/nologin api \
    && mkdir -p /data \
    && chown -R api:api /app /data

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import json,urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=2); d=json.load(r); assert d['base_datos']=='ok'" || exit 1

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000"]
