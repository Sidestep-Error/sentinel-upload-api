"""Tests for the sentinel-ml integration (upload enrichment + ml lookup route)."""

from unittest.mock import AsyncMock


class FakeUploads:
    def __init__(self):
        self.items = []

    async def find_one(self, _query, _projection):
        return None

    async def insert_one(self, doc):
        self.items.append(doc)
        return object()


class FakeMlPredictions:
    def __init__(self):
        self.docs = {}

    async def update_one(self, filt, update, upsert=False):
        key = filt["upload_id"]
        self.docs[key] = dict(update["$set"])
        return object()

    async def find_one(self, filt, _projection=None):
        return self.docs.get(filt["upload_id"])


class FakeDB:
    def __init__(self):
        self.uploads = FakeUploads()
        self.ml_predictions = FakeMlPredictions()


def _enable_ml(monkeypatch, result):
    monkeypatch.setattr("app.services.sentinel_ml_client.SENTINEL_ML_ENABLED", True)
    mock = AsyncMock(return_value=result)
    monkeypatch.setattr("app.services.sentinel_ml_client.predict_liveflow", mock)
    return mock


def test_upload_enriches_and_get_ml_returns_prediction(client, monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr("app.main.get_db", lambda: fake_db)
    ml_result = {
        "upload_result": {
            "prediction": {"label": "clean", "confidence": 0.91},
            "model_version": "abc123",
        },
        "upload_text_result": {
            "upload_id": "placeholder",
            "source": "upload_text",
            "prediction": {"label": "phishing", "confidence": 0.67},
            "model_version": "def456",
            "iocs": [{"type": "url", "value": "http://evil.example"}],
            "extracted_text": "hello ml",
            "text_truncated": False,
        },
        "summary": {"has_upload": True, "has_upload_text": True, "has_cve_relevance": False},
    }
    mock_predict = _enable_ml(monkeypatch, ml_result)

    r = client.post("/upload", files={"file": ("note.txt", b"hello ml", "text/plain")})
    assert r.status_code == 200
    sha = r.json()["sha256"]

    # The prediction was persisted under the upload's sha256.
    mock_predict.assert_awaited_once()
    payload = mock_predict.await_args.args[0]
    assert payload["upload"]["upload_id"] == sha
    assert payload["upload_text"]["upload_id"] == sha
    assert payload["upload_text"]["source"] == "upload_text"
    assert payload["upload_text"]["extracted_text"] == "hello ml"
    assert sha in fake_db.ml_predictions.docs
    assert fake_db.ml_predictions.docs[sha]["upload_id"] == sha
    assert "extracted_text" not in fake_db.ml_predictions.docs[sha]["upload_text_result"]

    # And the lookup route returns it.
    got = client.get(f"/uploads/{sha}/ml")
    assert got.status_code == 200
    body = got.json()
    assert body["upload_id"] == sha
    assert body["upload_result"]["prediction"]["label"] == "clean"
    assert "extracted_text" not in body["upload_text_result"]


def test_get_upload_ml_returns_404_when_missing(client, monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr("app.main.get_db", lambda: fake_db)

    r = client.get("/uploads/" + ("a" * 64) + "/ml")
    assert r.status_code == 404


def test_upload_skips_ml_when_disabled(client, monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr("app.main.get_db", lambda: fake_db)
    monkeypatch.setattr("app.services.sentinel_ml_client.SENTINEL_ML_ENABLED", False)
    mock_predict = AsyncMock()
    monkeypatch.setattr("app.services.sentinel_ml_client.predict_liveflow", mock_predict)

    r = client.post("/upload", files={"file": ("note.txt", b"hello ml", "text/plain")})
    assert r.status_code == 200

    mock_predict.assert_not_awaited()
    assert fake_db.ml_predictions.docs == {}


def test_upload_omits_upload_text_for_unsupported_file_type(client, monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr("app.main.get_db", lambda: fake_db)
    ml_result = {
        "upload_result": {
            "prediction": {"label": "clean", "confidence": 0.42},
            "model_version": "abc123",
        },
        "summary": {"has_upload": True, "has_upload_text": False, "has_cve_relevance": False},
    }
    mock_predict = _enable_ml(monkeypatch, ml_result)

    r = client.post("/upload", files={"file": ("image.png", b"png-bytes", "image/png")})
    assert r.status_code == 200

    mock_predict.assert_awaited_once()
    payload = mock_predict.await_args.args[0]
    assert "upload" in payload
    assert "upload_text" not in payload
