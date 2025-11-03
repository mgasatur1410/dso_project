from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_item():
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    assert "type" in body and body["status"] == 404


def test_validation_error():
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422
    body = r.json()
    assert body["detail"] == "name must be 1..100 chars"


def test_error_rfc7807():
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    assert "type" in body and "correlation_id" in body and body["status"] == 404
    assert "item not found" in body["detail"]


def test_upload_big_file():
    data = b"a" * (1024 * 1024 + 5)
    r = client.post("/upload", files={"file": ("f.png", data, "image/png")})
    assert r.status_code == 422
    body = r.json()
    assert "too_large" in r.text or body["status"] == 422


def test_upload_invalid_mime():
    r = client.post("/upload", files={"file": ("f.txt", b"badtext", "text/plain")})
    assert r.status_code == 422
    assert "mime_invalid" in r.text


def test_upload_invalid_signature():
    r = client.post("/upload", files={"file": ("f.png", b"notpngfile", "image/png")})
    assert r.status_code == 422
    assert "magic_invalid" in r.text
