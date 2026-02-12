import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app
from app.main import _upload_request_times
from app.main import enforce_upload_rate_limit
from app.scanner import ScanResult


@pytest.fixture
def client():
    _upload_request_times.clear()
    with TestClient(app) as test_client:
        yield test_client


def test_upload_accepts_allowed_type(client):
    files = {"file": ("hello.txt", b"hello", "text/plain")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "accepted"
    assert body["content_type"] == "text/plain"
    assert body["scan_status"] == "clean"


def test_upload_accepts_markdown_type(client):
    files = {"file": ("README.md", b"# hello", "text/markdown")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "accepted"
    assert body["content_type"] == "text/markdown"
    assert body["scan_status"] == "clean"


def test_upload_blocks_disallowed_type(client):
    files = {"file": ("evil.exe", b"MZ...", "application/octet-stream")}
    r = client.post("/upload", files=files)
    assert r.status_code == 415


def test_upload_rejects_malicious_signature(client):
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    files = {"file": ("eicar.txt", eicar, "text/plain")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "rejected"
    assert body["scan_status"] == "malicious"


def test_upload_rejects_when_scanner_errors(client, monkeypatch):
    def fake_scan_bytes(_filename, _content):
        return ScanResult(status="error", engine="clamav", detail="ClamAV unavailable")

    monkeypatch.setattr("app.main.scan_bytes", fake_scan_bytes)
    files = {"file": ("hello.txt", b"hello", "text/plain")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "rejected"
    assert body["scan_status"] == "error"


def test_upload_rate_limit_returns_429_when_exceeded(monkeypatch):
    monkeypatch.setattr("app.main.RATE_LIMIT_UPLOADS_PER_MINUTE", 3)
    monkeypatch.setattr("app.main.RATE_LIMIT_WINDOW_SECONDS", 60)
    _upload_request_times.clear()

    for _ in range(3):
        enforce_upload_rate_limit("ci-test-client")

    with pytest.raises(HTTPException) as exc:
        enforce_upload_rate_limit("ci-test-client")

    assert exc.value.status_code == 429
