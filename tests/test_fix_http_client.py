"""
Негативные тесты для security-контроля HTTP Client (таймауты, ретраи, защита от DoS).

Привязка к рискам/угрозам:
- F9 (API→EXT_MAIL) / R-09: Недоступность внешнего провайдера
- NFR-03: Время отклика API (p95 ≤ 300мс)
- NFR-05: Ограничение запросов (Rate limiting)
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_external_proxy_timeout_attack():
    """Злоупотребление: атака на медленный внешний сервис (DoS)"""
    # Приватный IP заблокирован валидацией (SSRF защита)
    r = client.get("/external_proxy", params={"url": "http://10.255.255.1"})
    assert r.status_code in (400, 422, 502, 504)
    assert (
        "forbidden" in r.text.lower()
        or "http_call_failed" in r.text
        or "validation_error" in r.text
    )


def test_external_proxy_invalid_url():
    """Негативный тест: некорректный URL"""
    r = client.get("/external_proxy", params={"url": "not-a-url"})
    assert r.status_code in (400, 422, 502)


def test_external_proxy_ssrf_localhost():
    """Злоупотребление: SSRF-атака (попытка доступа к localhost)"""
    r = client.get("/external_proxy", params={"url": "http://127.0.0.1:22"})
    # Должна быть защита от SSRF (если не реализована - это уязвимость)
    assert r.status_code in (400, 422, 502)


def test_external_proxy_ssrf_private_network():
    """Злоупотребление: SSRF-атака на приватную сеть"""
    r = client.get("/external_proxy", params={"url": "http://192.168.1.1"})
    assert r.status_code in (400, 422, 502)


def test_external_proxy_file_protocol():
    """Злоупотребление: использование file:// протокола (LFI)"""
    r = client.get("/external_proxy", params={"url": "file:///etc/passwd"})
    assert r.status_code in (400, 422, 502)


def test_external_proxy_no_timeout_infinite_hang():
    """Негативный тест: проверка что валидация URL срабатывает быстро (не висит бесконечно)"""
    import time

    start = time.time()
    # Приватный IP должен быть заблокирован валидацией до запроса
    r = client.get(
        "/external_proxy", params={"url": "http://10.255.255.1"}, timeout=10.0
    )
    elapsed = time.time() - start
    # Должен вернуть ошибку валидации очень быстро (< 1с), без HTTP-запроса
    assert elapsed < 2.0  # с запасом
    assert r.status_code in (400, 422, 502, 504)
