# Трассируемость NFR ↔ Stories/Tasks

| NFR ID | Связанные Stories/Tasks | Приоритет | Компонент | Релиз/Окно |
|--------|--------------------------|-----------|-----------|------------|
| NFR-01 | USER-STORY-01 (регистрация, сохранение профиля), DATA-TASK-02 (миграция БД) | High | DB | v1.0 |
| NFR-02 | AUTH-TASK-02 (аутентификация, KDF), SEC-TASK-01 (проверка KDF) | High | Auth | v1.0 |
| NFR-03 | PERF-TASK-05 (кеширование, индексы), API-TASK-09 (пагинация) | Medium | Backend | v1.1 |
| NFR-04 | OPS-TASK-03 (healthcheck, readiness), OPS-TASK-04 (реплики) | High | Infra | v1.0 |
| NFR-05 | API-TASK-07 (rate limiting), SEC-TASK-03 (абьюз-паттерны) | Medium | Gateway | v1.2 |
| NFR-06 | AUTH-TASK-03 (JWT/refresh flow), FE-TASK-06 (автообновление токена) | Medium | Auth | v1.0 |
| NFR-07 | DEVOPS-TASK-01 (секрет-менеджер), DEVOPS-TASK-05 (KMS ключи) | Low | DevOps | v1.1 |
| NFR-08 | LOGS-TASK-04 (структурные логи), ALERT-TASK-02 (SLO/алёрты) | High | Backend | v1.0 |
