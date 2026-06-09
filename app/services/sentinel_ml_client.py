"""Async client for the sentinel-ml FastAPI service.

sentinel-ml runs as an internal-only microservice in the cluster. This client
calls its ``/predict/liveflow`` endpoint to enrich uploads with ML predictions.

Design constraints (see sentinel-ml docs/integration-with-sentinel-upload-api):
- Non-blocking and fail-silent: if sentinel-ml is disabled, unreachable, or
  slow, the upload flow must continue unaffected. Any failure returns ``None``.
- Disabled by default. The call only runs when ``SENTINEL_ML_ENABLED`` is set,
  so production (where the env var is unset) makes zero network calls.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("sentinel")


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except ValueError:
        return default


# Cluster default: the internal ClusterIP service (port 80 -> container 8100).
# Local demo overrides this (e.g. http://localhost:8100).
SENTINEL_ML_URL = os.getenv("SENTINEL_ML_URL", "http://sentinel-ml.sentinel.svc.cluster.local")
SENTINEL_ML_TIMEOUT_MS = _env_int("SENTINEL_ML_TIMEOUT_MS", 500)
SENTINEL_ML_ENABLED = os.getenv("SENTINEL_ML_ENABLED", "false").lower() in {"1", "true", "yes"}


async def predict_liveflow(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Call sentinel-ml ``/predict/liveflow``.

    Returns the parsed JSON response, or ``None`` when the integration is
    disabled or the service is unavailable/slow/erroring.
    """
    if not SENTINEL_ML_ENABLED:
        return None

    url = f"{SENTINEL_ML_URL.rstrip('/')}/predict/liveflow"
    timeout = SENTINEL_ML_TIMEOUT_MS / 1000
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
    except Exception:
        logger.debug("sentinel-ml unavailable — skipping ML enrichment", exc_info=True)
        return None
