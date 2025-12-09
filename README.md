# SecDev Course Template

Стартовый шаблон для студенческого репозитория (Study Planner).

Study Planner — это умное приложение, которое помогает планировать учёбу, отслеживать темы, дедлайны и прогресс выполнения заданий.

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
uvicorn app.main:app --reload
```

## Ритуал перед PR
```bash
ruff check --fix .
black .
isort .
pytest -q
pre-commit run --all-files
```

## Тесты
```bash
pytest -q
# С coverage (требуется ≥80%)
pytest --cov=app --cov-report=term-missing
# HTML отчёт
pytest --cov=app --cov-report=html
# Затем открыть htmlcov/index.html
```

## CI
В репозитории настроены workflows **CI** (GitHub Actions) — required check для `main`.
Badge добавится автоматически после загрузки шаблона в GitHub.

### Workflows
- **CI/CD** (`.github/workflows/ci.yml`) — линтинг, тесты, сборка контейнера, сканирование безопасности
- **Security - SBOM & SCA** (`.github/workflows/ci-sbom-sca.yml`) — генерация SBOM и анализ уязвимостей зависимостей

### EVIDENCE структура
Директория `EVIDENCE/` содержит артефакты практик курса:
- **`EVIDENCE/P09/`** — артефакты P09 (SBOM & SCA):
  - `sbom.json` — Software Bill of Materials (Syft v1.38.0, формат syft-json)
  - `sca_report.json` — отчёт об уязвимостях зависимостей (Grype v0.97.0)
  - `waivers.snapshot.yml` — снэпшот политики waivers на момент прогона

Артефакты генерируются автоматически в CI и доступны через GitHub Actions Artifacts.
Имена артефактов содержат SHA коммита для трассировки: `p09-sbom-sca-<sha>`.
Используются для DS-раздела итогового отчёта и управления уязвимостями.

## Контейнеры
```bash
docker build -t secdev-app .
docker run --rm -p 8000:8000 secdev-app
# или
docker compose up --build
```

## Эндпойнты
- `GET /health` → `{"status": "ok"}`
- `POST /items?name=...` — демо-сущность
- `GET /items/{id}`

## Формат ошибок
Все ошибки — JSON-обёртка:
```json
{
  "error": {"code": "not_found", "message": "item not found"}
}
```

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
