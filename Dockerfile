# Build stage - установка зависимостей для копирования в runtime
FROM python:3.11-slim AS build
WORKDIR /app

# Копируем requirements.txt отдельно для эффективного кэширования слоя
COPY requirements.txt .

# Устанавливаем Python-зависимости (без кэша для уменьшения размера)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения (для тестов)
COPY . .

# Test stage - запуск тестов (опционально, можно отключить в продакшене)
FROM build AS test
RUN pip install --no-cache-dir -r requirements-dev.txt && pytest -q

# Production runtime stage - минимальный образ
FROM python:3.11-slim AS runtime

# Устанавливаем curl только для healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Создаём non-root пользователя
RUN groupadd -r app && \
    useradd --no-log-init -r -g app -u 1000 -m app && \
    mkdir -p /app /app/uploads && \
    chown -R app:app /app

# Копируем установленные зависимости из build-слоя (оптимизация: только site-packages)
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Копируем код приложения
COPY --chown=app:app . .

# Устанавливаем корректные права (owner: read+write+execute, group: read+execute, others: read)
RUN chmod -R 755 /app && \
    chmod -R o-w /app

EXPOSE 8000

# Healthcheck для мониторинга состояния контейнера
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Переключаемся на non-root пользователя
USER app

# Явно объявляем ENTRYPOINT и CMD
ENTRYPOINT ["uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000"]
