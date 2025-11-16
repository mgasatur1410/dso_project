# Build stage
FROM python:3.11-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

FROM build AS test
RUN pip install --no-cache-dir -r requirements-dev.txt && pytest -q

FROM python:3.11-slim AS runtime
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN groupadd -r app && useradd --no-log-init -r -g app app && mkdir -p /app && chown app:app /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod -R o-w /app

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s CMD curl -fsS http://localhost:8000/health || exit 1
USER app
ENTRYPOINT ["uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000"]
