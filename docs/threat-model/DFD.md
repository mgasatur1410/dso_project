# Data Flow Diagram — Study Planner

Нотация: потоки помечены **F1…F10** и используются в STRIDE/RISKS.
Границы доверия: **Client / Edge / Core / Data**.

```mermaid
flowchart LR
  %% === Trust Boundaries ===
  subgraph B0["Client boundary"]
    U["Пользователь (Web/Mobile)"]
    C["Клиентское приложение"]
  end

  subgraph B1["Edge boundary"]
    G["API Gateway / Rate Limiter"]
    CDN["CDN / Static"]
  end

  subgraph B2["Core boundary"]
    AUTH["Auth Service (JWT/Refresh)"]
    API["Backend API (Study/Tasks)"]
    WORKER["Async Worker (jobs/notifications)"]
    OBS["Observability (APM/Logs)"]
  end

  subgraph B3["Data boundary"]
    DB[("(Main DB)")]
    OBJ[("(Object Storage)")]
    KMS[("(KMS / Secrets)")]
    MQ[("(Message Queue)")]
  end

  %% External parties
  EXT_OAUTH["Внешний IdP (OAuth/OIDC)"]
  EXT_MAIL["Email/SMS провайдер"]

  %% Flows (нумерация обязательна)
  U -->|"F1: UX/действия"| C
  C -->|"F2: HTTPS REST/JSON"| G
  G -->|"F3: mTLS gRPC/HTTP2"| API
  G -->|"F4: mTLS gRPC/HTTP2"| AUTH
  AUTH -->|"F5: JWT (TTL 3600s) + Refresh 30d"| C
  API -->|"F6: mTLS + SQL/ORM"| DB
  API -->|"F7: mTLS + S3 API"| OBJ
  AUTH -->|"F8: OIDC/OAuth2"| EXT_OAUTH
  WORKER -->|"F9: SMTP/SMS API over TLS"| EXT_MAIL
  API -->|"F10: mTLS + OTLP/Logs"| OBS

  %% Async
  API -->|"enqueue tasks"| MQ
  MQ -->|"dequeue jobs"| WORKER
  WORKER -->|"mTLS + SQL/ORM"| DB
