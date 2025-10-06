# BDD-приёмка NFR — Study Planner

## NFR-01 — Шифрование данных пользователей
Scenario: Encrypt user data at rest
  Given пользователь сохраняет личные учебные данные
  When запись попадает в базу данных
  Then данные должны быть зашифрованы алгоритмом AES-256 at rest

## NFR-02 — Хэширование паролей
Scenario: Passwords hashed with Argon2id
  Given пользователь регистрируется и задаёт пароль
  When система сохраняет пароль
  Then пароль должен быть захэширован Argon2id с параметрами t=3, m=64MB, p=2

## NFR-03 — Быстрый отклик API
Scenario: p95 API response time under normal load
  Given 100 одновременных активных пользователей
  When они запрашивают свои планы и прогресс
  Then 95% ответов должны приходить быстрее 300 мс

## (Негативный) NFR-04 — Отказоустойчивость при падении backend
Scenario: Graceful degradation with retries
  Given основной backend временно недоступен
  When пользователь отправляет запрос к API
  Then система возвращает "Service temporarily unavailable", выполняет до 3 ретраев с экспоненциальной задержкой и логирует инцидент

## (Негативный) NFR-05 — Истёкший JWT
Scenario: Access denied for expired token
  Given access JWT старше 3600 секунд
  When пользователь обращается к защищённому эндпоинту
  Then система должна вернуть 401 Unauthorized и предложить обновить токен через refresh
