# PR: Secure Coding Controls (P06) — Maximum Score ★★2

## Контекст

Реализованы ≥4 измеримых security-контроля для защиты приложения от уязвимостей и злоупотреблений. Каждый контроль проверяем через линтеры, тесты и валидацию, покрывает доменные злоупотребления.

## Что сделано

### 1. Secure File Upload (Path Traversal, Magic Bytes, Size Limits)
- **Уязвимость**: Path Traversal, подмена расширений, вредоносные файлы
- **Решение**:
  - Валидация magic bytes (PNG/JPEG), проверка MIME-типа
  - Лимит размера файла (1 MiB)
  - Защита от Path Traversal: проверка имени файла на `..`, `/`, `\\`, NULL byte, URL-encoded обход
  - Канонизация путей через `os.path.abspath()` для финальной проверки
- **Привязка к рискам**: **F7 (API→OBJ) / R-07** (Подмена/вредонос в Object Storage)
- **Тесты**: `tests/test_fix_file_upload.py` — 7 негативных тестов (path traversal, big file, spoofing, NULL byte injection)

### 2. Secure HTTP Client (Timeouts, Retries, SSRF Protection)
- **Уязвимость**: DoS через медленные внешние запросы, SSRF-атаки
- **Решение**:
  - Явные таймауты (3с по умолчанию)
  - Ретраи (3 попытки с exponential backoff)
  - Защита от SSRF: блокировка `file://`, `gopher://`, `ldap://` протоколов
  - Проверка приватных IP-адресов (localhost, 127.0.0.1, 192.168.x.x, 10.x.x.x, 172.16.x.x)
- **Привязка к рискам**: **F9 (API→EXT_MAIL) / R-09** (Недоступность Email/SMS провайдера)
- **Привязка к NFR**: **NFR-03** (Время отклика API p95 ≤ 300мс), **NFR-05** (Rate limiting)
- **Тесты**: `tests/test_fix_http_client.py` — 6 негативных тестов (SSRF, timeout, file:// протокол)

### 3. Payment Validation (Decimal, UTC, PII Masking)
- **Уязвимость**: Float-погрешности в денежных расчётах, утечка PII в логах, некорректные даты
- **Решение**:
  - Pydantic-модель с `Decimal` (не `float`) для точных денежных расчётов
  - UTC-нормализация дат через `normalize()`
  - Маскирование PII через `mask_pii()`: email → `al***@***com`, sender → `Bo***ob`
  - Валидация границ: `amount > 0`, `max_digits=12`, `decimal_places=2`
- **Привязка к рискам**: **R-02** (Утечка PII из основной БД), **R-06** (Секреты/PII в логах)
- **Привязка к NFR**: **NFR-08** (Логирование без чувствительных данных)
- **Тесты**: `tests/test_fix_payment_validation.py` — 10 негативных тестов (float, negative, zero, long strings, PII masking)

### 4. Input Validation (Domain Fields, Boundary Checks)
- **Уязвимость**: SQL-инъекции, XSS, атаки длинными строками, Path Traversal в именах
- **Решение**:
  - Валидация длины (1..100 chars для `name`)
  - Проверка запрещённых символов (`..`, `/`, `\\`) в именах
  - Граничные значения (пустая строка, максимальная длина)
  - Логирование без PII (маскирование чувствительных данных)
- **Привязка к рискам**: **F2 (Client→Gateway) / R-10** (SQL-инъекции/инъекции в API)
- **Привязка к NFR**: **NFR-08** (Валидация входных данных)
- **Тесты**: `tests/test_fix_input_validation.py` — 6 негативных тестов (long strings, SQLi, XSS, path traversal)

## Метрики и доказательства

### Coverage
- **Текущее покрытие**: 88% (требуется ≥80%) ✅
- Команда: `pytest --cov=app --cov-report=term-missing`
- HTML отчёт: `htmlcov/index.html`

### Тесты
- **Всего тестов**: 40 (все проходят ✅)
- **Негативных тестов**: ≥6 на каждый контроль
- **Доменные злоупотребления**: покрыты (path traversal, SSRF, float-погрешности, длинные строки, PII утечки)

### Quality Gate
- **ruff**: ✅ All checks passed
- **black**: ✅ All done
- **isort**: ✅ Skipped (уже отформатировано)
- **mypy**: ✅ Success: no issues found
- **bandit**: ✅ No issues identified (из CI)

### CI/CD
- **GitHub Actions**: настроен с проверками линтеров, тестов, coverage
- **Coverage gate**: `--cov-fail-under=80` в `pyproject.toml`
- **Артефакты**: coverage.xml, bandit-report.json загружаются в CI

## Привязка к рискам/угрозам (Traceability)

| Контроль | Угроза (F#) | Риск (R#) | NFR | Тесты |
|----------|-------------|-----------|-----|-------|
| File Upload | F7 (API→OBJ) | R-07 | NFR-08 | `test_fix_file_upload.py` |
| HTTP Client | F9 (API→EXT_MAIL) | R-09 | NFR-03, NFR-05 | `test_fix_http_client.py` |
| Payment Validation | - | R-02, R-06 | NFR-08 | `test_fix_payment_validation.py` |
| Input Validation | F2 (Client→Gateway) | R-10 | NFR-08 | `test_fix_input_validation.py` |

## Чек-лист критериев P06 (★★2)

### C1. Исправление уязвимости ★★2
- ✅ **Реальный дефект**: Path Traversal в `/upload`, SSRF в `/external_proxy`, float-погрешности в `/payments`
- ✅ **Diff кода**: все фиксы интегрированы в `app/main.py`
- ✅ **CI-тесты**: все тесты проходят

### C2. Тесты (вкл. негативные) ★★2
- ✅ **≥6 тестов**: 40 тестов всего, ≥6 на каждый контроль
- ✅ **Негативные тесты**: покрыты все злоупотребления (path traversal, SSRF, float, длинные строки)
- ✅ **Доменные сценарии**: "атака длинной строкой", "SSRF в URL", "float-погрешность в amount"

### C3. Валидация/ошибки/логирование ★★2
- ✅ **Валидация доменных полей**: Decimal для amount, длина для sender/email, Path Traversal проверки
- ✅ **PII маскирование**: `mask_pii()` маскирует email, recipient_email, sender
- ✅ **Безопасное логирование**: только диагностическая информация, без чувствительных данных
- ✅ **RFC 7807**: все ошибки возвращаются с `correlation_id`, `type`, `title`, `status`, `detail`

### C4. Линт/формат/quality gate ★★2
- ✅ **ruff, black, isort**: проходят локально и в CI
- ✅ **Дополнительные правила**: mypy (type checking), bandit (security scanning)
- ✅ **Quality gate**: CI блокирует merge при ошибках линтеров/тестов
- ✅ **Coverage ≥80%**: 88% покрытие кода

### C5. Интеграция в модуль проекта ★★2
- ✅ **Рабочий модуль**: все фиксы интегрированы в `app/main.py` (реальный сервис)
- ✅ **Привязка к Issue/истории**: ссылки на NFR-xx, R-xx, F-xx в коде и ADR-004
- ✅ **ADR**: `docs/adr/ADR-004-secure-coding-p06.md` описывает все контроли и их traceability

## Как проверял(а)

- [x] `ruff check .` — All checks passed
- [x] `black --check .` — All done
- [x] `isort --check .` — Skipped (уже отформатировано)
- [x] `mypy app/` — Success: no issues found
- [x] `bandit -r app/` — No issues identified
- [x] `pytest --cov=app --cov-report=term-missing -v` — 40 passed, coverage 88%
- [x] `pre-commit run --all-files` — все хуки проходят

## Ссылки

- **ADR**: `docs/adr/ADR-004-secure-coding-p06.md`
- **NFR**: `docs/security-nfr/NFR.md` (NFR-03, NFR-05, NFR-08)
- **RISKS**: `docs/threat-model/RISKS.md` (R-02, R-06, R-07, R-09, R-10)
- **STRIDE**: `docs/threat-model/STRIDE.md` (F2, F7, F9)
- **Тесты**: `tests/test_fix_*.py` (file_upload, http_client, payment_validation, input_validation)

---

**Готово для ревью!** Все критерии P06 выполнены на максимум ★★2.
