# Makefile для dev и проверки secdev-контейнера

IMAGE=secdev-app:latest
CONTAINER=secdev-app

.PHONY: build up down ps logs lint scan-health scan-hadolint scan-trivy check-user

build:
	docker build -t $(IMAGE) .

up:
	docker compose up --build -d
	docker compose logs -f

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f

lint:
	hadolint Dockerfile

scan-hadolint:
	hadolint Dockerfile

scan-trivy:
	trivy image --severity CRITICAL,HIGH $(IMAGE)

check-user:
	docker compose exec app id -u

check-health:
	docker compose exec app curl -sf http://localhost:8000/health
