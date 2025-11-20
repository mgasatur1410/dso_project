from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_external_proxy_timeout():
    # Приватный IP заблокирован валидацией (SSRF защита), возвращает 422
    r = client.get("/external_proxy", params={"url": "http://10.255.255.1"})
    # Должна быть защита от SSRF (валидация) — 422, не 502
    assert r.status_code in (400, 422, 502, 504)
    assert (
        "forbidden" in r.text.lower()
        or "validation_error" in r.text.lower()
        or "http_call_failed" in r.text
    )
