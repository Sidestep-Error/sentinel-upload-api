from fastapi.testclient import TestClient
from app.main import app
from app.scanner import ScanResult

client = TestClient(app)


def test_upload_accepts_allowed_type():
    files = {"file": ("hello.txt", b"hello", "text/plain")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "accepted"
    assert body["content_type"] == "text/plain"
    assert body["scan_status"] == "clean"


def test_upload_accepts_markdown_type():
    files = {"file": ("README.md", b"# hello", "text/markdown")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "accepted"
    assert body["content_type"] == "text/markdown"
    assert body["scan_status"] == "clean"


def test_upload_blocks_disallowed_type():
    files = {"file": ("evil.exe", b"MZ...", "application/octet-stream")}
    r = client.post("/upload", files=files)
    assert r.status_code == 415


def test_upload_rejects_malicious_signature():
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    files = {"file": ("eicar.txt", eicar, "text/plain")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "rejected"
    assert body["scan_status"] == "malicious"


def test_upload_rejects_when_scanner_errors(monkeypatch):
    def fake_scan_bytes(_filename, _content):
        return ScanResult(status="error", engine="clamav", detail="ClamAV unavailable")

    monkeypatch.setattr("app.main.scan_bytes", fake_scan_bytes)
    files = {"file": ("hello.txt", b"hello", "text/plain")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "rejected"
    assert body["scan_status"] == "error"
