from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_upload_accepts_allowed_type():
    files = {"file": ("hello.txt", b"hello", "text/plain")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "accepted"
    assert body["content_type"] == "text/plain"


def test_upload_accepts_markdown_type():
    files = {"file": ("README.md", b"# hello", "text/markdown")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "accepted"
    assert body["content_type"] == "text/markdown"


def test_upload_blocks_disallowed_type():
    files = {"file": ("evil.exe", b"MZ...", "application/octet-stream")}
    r = client.post("/upload", files=files)
    assert r.status_code == 415
