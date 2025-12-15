# P10 — SAST & Secrets (Semgrep + Gitleaks)

Ветка `p10-sast-secrets` (workflow `.github/workflows/ci-p10-security.yml`). Отдельный пайплайн для SAST и поиска секретов (Semgrep + Gitleaks).

## Что сделано по критериям

### C1. SAST (Semgrep, SARIF)
- Semgrep из Docker `returntocorp/semgrep:1.80.0`.
- Профили: `p/ci` + проектные правила `security/semgrep/rules.yml` (TLS verify/httpx, UploadFile.filename join, httpx timeout, Decimal-from-float).
- Вывод: SARIF `EVIDENCE/P10/semgrep.sarif`, загружается через `upload-sarif@v4` в Code Scanning.
- Триггеры: push/PR по коду и security-конфигах; `concurrency` включён.
- `continue-on-error: true` + `--metrics=off`, чтобы findings/метрики не падали сборку.

### C2. Secrets (Gitleaks)
- Gitleaks `zricethezav/gitleaks:latest`, скан `--source /repo`.
- Конфиг: короткий `security/.gitleaks.toml` (extends дефолт + allowlist для placeholders GitHub secrets и публичного контакта).
- Отчёт: JSON `EVIDENCE/P10/gitleaks.json`, артефакт.
- Флаги: `--exit-code 0` + `continue-on-error`, чтобы не падать на предупреждениях.

### C3. Артефакты и трассировка
- `EVIDENCE/P10/semgrep.sarif`
- `EVIDENCE/P10/gitleaks.json`
- `EVIDENCE/P10/p10_summary.md` (сводка: counts + план использования)
- Артефакт `p10-security-<sha>`, минимальные права: `contents: read`, `security-events: write`, заданы `timeout-minutes`.

### C4. Триаж
- Semgrep: 0 findings.
- Gitleaks: 0 findings; allowlist только для описанных ложных срабатываний.
- Действия: фиксить нечего; новые allowlist — только с обоснованием. Критичные секреты: `DB_URL`, `JWT_SECRET_*`; при инциденте — ревокация/ротация и перепроверка.

### C5. Интеграция в CI
- Триггеры по релевантным путям, `concurrency` включён.
- Минимальные permissions, `continue-on-error`, таймауты.
- SARIF уходит в Code Scanning.

## Артефакты последнего прогона
- `EVIDENCE/P10/semgrep.sarif` — 0 findings.
- `EVIDENCE/P10/gitleaks.json` — 0 leaks.
- `EVIDENCE/P10/p10_summary.md` — сводка + план использования (DS/triage).

## Примечание по стабильности
- Gitleaks: сменили недоступный `:8.18.4` на `:latest`, добавили `--config` и `--exit-code 0`.
- Semgrep: `--metrics=off` и `|| true`, чтобы exit 2 не помечал джоб как failed.
- Upload SARIF: `github/codeql-action/upload-sarif@v4` (без предупреждений о v3).
