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


def test_payment_float_amount():
    payment = {
        "amount": 123.45789,  # float, should be error (needs string/Decimal)
        "currency": "USD",
        "sender": "Ivan",
        "recipient_email": "test@example.com",
        "occurred_at": "2024-01-01T12:00:00Z",
    }
    r = client.post("/payments", json=payment)
    assert r.status_code == 422
    assert "Decimal" in r.text or "amount" in r.text  # Validation error


def test_payment_bad_date():
    payment = {
        "amount": "10.00",
        "currency": "USD",
        "sender": "Ivan",
        "recipient_email": "test@example.com",
        "occurred_at": "2024-01-01 25:61:00",  # invalid
    }
    r = client.post("/payments", json=payment)
    assert r.status_code == 422
    assert "occurred_at" in r.text or "date" in r.text


def test_payment_sender_too_long():
    payment = {
        "amount": "10.00",
        "currency": "USD",
        "sender": "X" * 80,
        "recipient_email": "test@example.com",
        "occurred_at": "2024-01-01T10:00:00Z",
    }
    r = client.post("/payments", json=payment)
    assert r.status_code == 422
    assert "sender" in r.text


def test_masked_pii_in_log():
    # Here we check that mask_pii utility masks emails (this is for coverage, pseudo-log)
    from app.main import mask_pii

    data = {"email": "alice@example.com"}
    masked = mask_pii(data)
    assert masked["email"].startswith("al***@***")
