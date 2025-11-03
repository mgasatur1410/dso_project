from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_external_proxy_timeout():
    # Невалидный адрес вызовет timeout/retry
    r = client.get("/external_proxy", params={"url": "http://10.255.255.1"})
    assert r.status_code in (502, 504)
    assert "http_call_failed" in r.text
