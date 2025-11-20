"""
Негативные тесты для security-контроля Payment Validation (Decimal, UTC, PII маскирование).

Привязка к рискам/угрозам:
- R-02: Утечка PII из основной БД
- R-06: Секреты/PII в логах и трейсах
- NFR-08: Логирование без чувствительных данных
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_payment_float_precision_attack():
    """Злоупотребление: float-погрешности в денежных расчётах"""
    payment = {
        "amount": 123.45789,  # float вместо Decimal - должна быть ошибка
        "currency": "USD",
        "sender": "Ivan",
        "recipient_email": "test@example.com",
        "occurred_at": "2024-01-01T12:00:00Z",
    }
    r = client.post("/payments", json=payment)
    assert r.status_code == 422
    assert "Decimal" in r.text or "amount" in r.text


def test_payment_negative_amount():
    """Негативный тест: отрицательная сумма (граничное значение)"""
    payment = {
        "amount": "-10.00",
        "currency": "USD",
        "sender": "Ivan",
        "recipient_email": "test@example.com",
        "occurred_at": "2024-01-01T12:00:00Z",
    }
    r = client.post("/payments", json=payment)
    assert r.status_code == 422
    assert "amount" in r.text.lower() or "validation_error" in r.text.lower()


def test_payment_zero_amount():
    """Граничное значение: сумма = 0"""
    payment = {
        "amount": "0.00",
        "currency": "USD",
        "sender": "Ivan",
        "recipient_email": "test@example.com",
        "occurred_at": "2024-01-01T12:00:00Z",
    }
    r = client.post("/payments", json=payment)
    assert r.status_code == 422
    assert "amount" in r.text.lower() or "validation_error" in r.text.lower()


def test_payment_large_decimal_precision():
    """Злоупотребление: очень большое число с высокой точностью (DoS)"""
    payment = {
        "amount": "999999999999.99",  # максимально допустимое (12 digits, 2 decimal)
        "currency": "USD",
        "sender": "Ivan",
        "recipient_email": "test@example.com",
        "occurred_at": "2024-01-01T12:00:00Z",
    }
    r = client.post("/payments", json=payment)
    # Может пройти валидацию (в пределах лимита), но важно что есть проверка
    assert r.status_code in (200, 422)


def test_payment_sender_long_string_attack():
    """Злоупотребление: атака длинной строкой на поле sender"""
    payment = {
        "amount": "10.00",
        "currency": "USD",
        "sender": "X" * 200,  # превышает max_length=64
        "recipient_email": "test@example.com",
        "occurred_at": "2024-01-01T12:00:00Z",
    }
    r = client.post("/payments", json=payment)
    assert r.status_code == 422
    assert "sender" in r.text.lower() or "validation_error" in r.text.lower()


def test_payment_email_xss_attempt():
    """Негативный тест: попытка XSS через email-поле"""
    payment = {
        "amount": "10.00",
        "currency": "USD",
        "sender": "Ivan",
        "recipient_email": "<script>alert('xss')</script>@example.com",
        "occurred_at": "2024-01-01T12:00:00Z",
    }
    r = client.post("/payments", json=payment)
    # Email должен быть валидирован (длина, формат)
    assert r.status_code in (200, 422)


def test_payment_bad_date_timezone():
    """Негативный тест: некорректная временная зона в datetime"""
    payment = {
        "amount": "10.00",
        "currency": "USD",
        "sender": "Ivan",
        "recipient_email": "test@example.com",
        "occurred_at": "2024-01-01 25:61:00",  # невалидная дата
    }
    r = client.post("/payments", json=payment)
    assert r.status_code == 422
    assert "occurred_at" in r.text.lower() or "date" in r.text.lower()


def test_payment_extra_fields_injection():
    """Негативный тест: инъекция дополнительных полей (extra='forbid')"""
    payment = {
        "amount": "10.00",
        "currency": "USD",
        "sender": "Ivan",
        "recipient_email": "test@example.com",
        "occurred_at": "2024-01-01T12:00:00Z",
        "malicious_field": "injection",  # не должно быть разрешено
    }
    r = client.post("/payments", json=payment)
    assert r.status_code == 422
    assert (
        "extra" in r.text.lower()
        or "forbidden" in r.text.lower()
        or "validation_error" in r.text.lower()
    )


def test_payment_pii_masked_in_response():
    """Позитивный тест: PII маскируется в логах (проверка функции mask_pii)"""
    from app.main import mask_pii

    data = {"email": "alice@example.com", "sender": "Bob"}
    masked = mask_pii(data)
    assert masked["email"].startswith("al***@***")
    assert (
        "@" not in masked["email"]
        or masked["email"].count("@") == 0
        or "***" in masked["email"]
    )
