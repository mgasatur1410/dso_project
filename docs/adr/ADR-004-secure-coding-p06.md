# ADR-004 — Secure Coding Controls (P06)

## Context
Необходимо реализовать ≥3 измеримых security-контроля для защиты приложения от уязвимостей и злоупотреблений. Каждый контроль должен быть проверяемым через линтеры, тесты и валидацию.

## Decision
Реализованы следующие security-контроли:

### 1. Secure File Upload (Path Traversal, Magic Bytes, Size Limits)
- **Проблема**: Риск загрузки вредоносных файлов, Path Traversal, подмена расширений
- **Решение**: Валидация magic bytes, проверка MIME-типа, лимит размера, защита от Path Traversal через канонизацию путей
- **Привязка к рискам**: F7 (API→OBJ) / R-07: Подмена/вредонос в Object Storage
- **Тесты**: `tests/test_fix_file_upload.py` — негативные тесты на path traversal, big file, spoofing

### 2. Secure HTTP Client (Timeouts, Retries, Error Handling)
- **Проблема**: Риск DoS через медленные внешние запросы, отсутствие таймаутов
- **Решение**: Явные таймауты (3с), ретраи (3 попытки), обработка ошибок
- **Привязка к рискам**: F9 (API→EXT_MAIL) / R-09: Недоступность Email/SMS провайдера; NFR-03: Время отклика API (p95 ≤ 300мс)
- **Тесты**: `tests/test_fix_http_client.py` — негативные тесты на таймауты, SSRF, file:// протокол

### 3. Payment Validation (Decimal, UTC, PII Masking)
- **Проблема**: Float-погрешности в денежных расчётах, утечка PII в логах, некорректные даты
- **Решение**: Pydantic-модель с Decimal (не float), UTC-нормализация дат, маскирование PII через `mask_pii()`
- **Привязка к рискам**: R-02: Утечка PII из основной БД; R-06: Секреты/PII в логах; NFR-08: Логирование без чувствительных данных
- **Тесты**: `tests/test_fix_payment_validation.py` — негативные тесты на float, длинные строки, PII маскирование

### 4. Input Validation (Domain Fields, Boundary Checks)
- **Проблема**: SQL-инъекции, XSS, атаки длинными строками
- **Решение**: Валидация длины, формата, граничных значений для всех входных данных
- **Привязка к рискам**: F2 (Client→Gateway) / R-10: SQL-инъекции/инъекции в API; NFR-08: Валидация входных данных
- **Тесты**: `tests/test_fix_input_validation.py` — негативные тесты на длинные строки, SQLi-подобные атаки

## Alternatives
1. Без валидации: проще, но критично небезопасно (уязвимости)
2. Простая валидация без доменных правил: работает, но не защищает от специфических атак

## Security Impact
- Снижены риски Path Traversal, DoS, утечки PII, float-погрешностей
- Все контроли покрыты негативными тестами (≥6 тестов на контроль)
- Coverage ≥80% через pytest-cov

## Rollout Plan
- Эндпоинты `/upload`, `/external_proxy`, `/payments` реализованы с валидацией
- Все контроли покрыты негативными тестами
- Coverage настроен в CI (≥80%)
- Линтеры (ruff, black, isort, mypy, bandit) проходят

## Links
- **NFR**: NFR-03, NFR-08
- **Risks**: R-02, R-06, R-07, R-09, R-10
- **Threats**: F2, F7, F9
- **Тесты**: `tests/test_fix_*.py` (file_upload, http_client, payment_validation, input_validation)
