import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app, _upload_request_times


@pytest.fixture
def client():
    _upload_request_times.clear()
    with patch("app.main.run_threat_intel_update_job"), \
         patch("app.main.BackgroundScheduler"):
        with TestClient(app) as test_client:
            yield test_client
