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
def mask_pii(data: dict) -> dict:
    masked = dict(data)
    if "email" in masked:
        val = masked["email"]
        if isinstance(val, str):
            masked["email"] = val[:2] + "***@***" + val[-3:] if "@" in val else "***"
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
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
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
    file_data = file.file.read(MAX_UPLOAD_SIZE + 1)
    if len(file_data) > MAX_UPLOAD_SIZE:
        raise ApiError(code="too_large", message="file too big", status=422)
    if file.content_type not in SAFE_MIME:
        raise ApiError(code="mime_invalid", message="bad MIME", status=422)
    magic = SAFE_MIME[file.content_type]
    if not file_data.startswith(magic):
        raise ApiError(code="magic_invalid", message="bad file signature", status=422)
    fname = f"{uuid.uuid4()}.bin"
    path = os.path.join(UPLOAD_DIR, fname)
    if not os.path.abspath(path).startswith(os.path.abspath(UPLOAD_DIR)):
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
    # Attempt parsing payment
    try:
        # parse_float=str enforces no float rounding
        p = Payment.model_validate(payment)
    except ValidationError as e:
        raise ApiError(code="validation_error", message=str(e), status=422)
    safe_log = mask_pii(p.model_dump())
    logger.info("Payment created: %s", safe_log)
    return {"result": "ok"}
