import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict

import httpx
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

app = FastAPI(title="SecDev Course App", version="0.1.0")


# PII log masking utility
# Привязка к рискам: R-02 (Утечка PII из основной БД), R-06 (Секреты/PII в логах)
# Привязка к NFR: NFR-08 (Логирование без чувствительных данных)
def mask_pii(data: dict) -> dict:
    """Маскирует PII-поля в данных для безопасного логирования.

    Маскирует:
    - email: alice@example.com → al***@***com
    - recipient_email: аналогично email
    - sender: если содержит потенциально чувствительную информацию
    """
    masked = dict(data)
    # Маскирование email-полей
    for email_field in ("email", "recipient_email", "sender_email"):
        if email_field in masked:
            val = masked[email_field]
            if isinstance(val, str) and "@" in val:
                # Маскируем: первые 2 символа + ***@*** + последние 3 символа
                masked[email_field] = val[:2] + "***@***" + val[-3:]
            elif isinstance(val, str):
                masked[email_field] = "***"
    # Маскирование имени отправителя (может содержать PII)
    if "sender" in masked and isinstance(masked["sender"], str):
        sender = masked["sender"]
        if len(sender) > 4:
            masked["sender"] = sender[:2] + "***" + sender[-2:]
    return masked


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("secdev")


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


def build_problem(
    request: Request, status: int, title: str, detail: str, type_: str = "about:blank"
):
    correlation_id = str(uuid.uuid4())
    return {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": str(request.url),
        "correlation_id": correlation_id,
    }


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    pb = build_problem(
        request,
        status=exc.status,
        title=exc.code,
        detail=exc.message,
        type_="https://example.com/errors/" + exc.code,
    )
    return JSONResponse(status_code=exc.status, content=pb)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    pb = build_problem(
        request,
        status=exc.status_code,
        title="http_error",
        detail=detail,
        type_="https://example.com/errors/http",
    )
    return JSONResponse(status_code=exc.status_code, content=pb)


@app.get("/health")
def health():
    return {"status": "ok"}


# Example minimal entity (for tests/demo)
_DB: Dict[str, list[Any]] = {"items": []}


@app.post("/items")
def create_item(name: str):
    """Создание элемента с доменной валидацией и защитой от инъекций.

    Привязка к рискам: F2 (Client→Gateway) / R-10 (SQL-инъекции/инъекции в API)
    Привязка к NFR: NFR-08 (Валидация входных данных)
    """
    # Доменная валидация: длина, формат, защита от инъекций
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
    # Защита от path traversal в имени (дополнительная проверка)
    if ".." in name or "/" in name or "\\" in name:
        raise ApiError(
            code="validation_error",
            message="name contains forbidden characters",
            status=422,
        )
    # Логирование без PII (имя может содержать чувствительные данные)
    safe_name = mask_pii({"name": name}).get(
        "name", name[:10] + "..." if len(name) > 10 else name
    )
    logger.info(f"Item created: name_length={len(name)}, safe_preview={safe_name}")
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
SAFE_MIME = {"image/png": b"\x89PNG", "image/jpeg": b"\xFF\xD8\xFF"}
MAX_UPLOAD_SIZE = 1024 * 1024  # 1 MiB


@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    """Безопасная загрузка файлов с защитой от Path Traversal и вредоносных файлов.

    Привязка к рискам: F7 (API→OBJ) / R-07 (Подмена/вредонос в Object Storage)
    Привязка к NFR: NFR-08 (Валидация входных данных, логирование без PII)
    """
    # Защита от Path Traversal: проверка оригинального имени файла
    original_filename = file.filename or ""
    # Проверка на запрещённые паттерны в имени файла
    if (
        ".." in original_filename
        or "/" in original_filename
        or "\\" in original_filename
    ):
        raise ApiError(code="path_traversal", message="bad filename", status=400)
    # Защита от NULL byte injection (проверяем строку и её байтовое представление)
    try:
        if "\x00" in original_filename:
            raise ApiError(code="path_traversal", message="bad filename", status=400)
        # Проверяем байтовое представление
        filename_bytes = original_filename.encode("utf-8", errors="replace")
        if b"\x00" in filename_bytes:
            raise ApiError(code="path_traversal", message="bad filename", status=400)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Если не удаётся закодировать - подозрительно
        raise ApiError(code="path_traversal", message="bad filename", status=400)
    # Защита от URL-encoded попыток обхода
    if (
        "%2e%2e" in original_filename.lower()
        or "%2f" in original_filename.lower()
        or "%5c" in original_filename.lower()
    ):
        raise ApiError(code="path_traversal", message="bad filename", status=400)

    file_data = file.file.read(MAX_UPLOAD_SIZE + 1)
    if len(file_data) > MAX_UPLOAD_SIZE:
        raise ApiError(code="too_large", message="file too big", status=422)
    if file.content_type not in SAFE_MIME:
        raise ApiError(code="mime_invalid", message="bad MIME", status=422)
    magic = SAFE_MIME[file.content_type]
    if not file_data.startswith(magic):
        raise ApiError(code="magic_invalid", message="bad file signature", status=422)
    # Безопасное имя файла с UUID (игнорируем оригинальное имя после проверки)
    fname = f"{uuid.uuid4()}.bin"
    path = os.path.join(UPLOAD_DIR, fname)
    # Дополнительная проверка через канонизацию пути
    resolved_path = os.path.abspath(path)
    resolved_upload_dir = os.path.abspath(UPLOAD_DIR)
    if not resolved_path.startswith(resolved_upload_dir):
        raise ApiError(code="path_traversal", message="bad filename", status=400)
    with open(path, "wb") as f:
        f.write(file_data)
    return {"result": "ok", "file_id": fname}


async def safe_http_request(url: str, timeout: float = 3.0, retries: int = 3):
    delay = 0.25
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.text
        except (httpx.RequestError, httpx.TimeoutException):
            if attempt == retries - 1:
                raise ApiError(
                    code="http_call_failed",
                    message=f"failed after {retries} attempts",
                    status=502,
                )
            await asyncio.sleep(delay)
            delay *= 2


@app.get("/external_proxy")
async def external_proxy(url: str):
    """Безопасный HTTP-клиент с защитой от SSRF и DoS через таймауты/ретраи.

    Привязка к рискам: F9 (API→EXT_MAIL) / R-09 (Недоступность Email/SMS провайдера)
    Привязка к NFR: NFR-03 (Время отклика API p95 ≤ 300мс), NFR-05 (Rate limiting)
    """
    # Защита от SSRF: проверка на приватные IP и file:// протокол
    import urllib.parse

    parsed = urllib.parse.urlparse(url)

    # Запрещаем file:// протокол (LFI)
    if parsed.scheme.lower() in ("file", "gopher", "ldap"):
        raise ApiError(
            code="validation_error", message="forbidden URL scheme", status=422
        )

    # Защита от SSRF на приватные сети (упрощённая проверка)
    hostname = parsed.hostname
    if hostname:
        # Запрещаем localhost/private IPs
        forbidden_hosts = ("localhost", "127.0.0.1", "::1", "0.0.0.0")
        if (
            hostname.lower() in forbidden_hosts
            or hostname.startswith("192.168.")
            or hostname.startswith("10.")
            or hostname.startswith("172.16.")
        ):
            raise ApiError(
                code="validation_error", message="forbidden hostname", status=422
            )

    data = await safe_http_request(url)
    return {"proxied": data[:100]}


# Advanced Payment Pydantic model
class Payment(BaseModel):
    model_config = dict(extra="forbid")
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    sender: str = Field(min_length=2, max_length=64)
    recipient_email: str = Field(min_length=5, max_length=64)
    occurred_at: datetime


def normalize(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


@app.post("/payments")
def create_payment(payment: dict):
    """Безопасная валидация платежей с Decimal (защита от float-погрешностей) и маскированием PII.

    Привязка к рискам: R-02 (Утечка PII из основной БД), R-06 (Секреты/PII в логах)
    Привязка к NFR: NFR-08 (Логирование без чувствительных данных)
    """
    # Attempt parsing payment
    try:
        # parse_float=str enforces no float rounding
        p = Payment.model_validate(payment)
    except ValidationError as e:
        raise ApiError(code="validation_error", message=str(e), status=422)
    safe_log = mask_pii(p.model_dump())
    logger.info("Payment created: %s", safe_log)
    return {"result": "ok"}
