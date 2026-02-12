from pathlib import Path
from collections import deque
from threading import Lock
from time import monotonic
import os

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import get_db
from app.models import UploadRecord
from app.scanner import scan_bytes

app = FastAPI(title="Sentinel Upload API")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "application/pdf",
    "image/png",
    "image/jpeg",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except ValueError:
        return default


RATE_LIMIT_UPLOADS_PER_MINUTE = _env_int("UPLOAD_RATE_LIMIT_PER_MINUTE", 10)
RATE_LIMIT_WINDOW_SECONDS = _env_int("UPLOAD_RATE_LIMIT_WINDOW_SECONDS", 60)

_rate_limit_lock = Lock()
_upload_request_times: dict[str, deque[float]] = {}


def enforce_upload_rate_limit(client_id: str):
    now = monotonic()
    with _rate_limit_lock:
        timestamps = _upload_request_times.setdefault(client_id, deque())
        while timestamps and now - timestamps[0] >= RATE_LIMIT_WINDOW_SECONDS:
            timestamps.popleft()

        if len(timestamps) >= RATE_LIMIT_UPLOADS_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: max {RATE_LIMIT_UPLOADS_PER_MINUTE} uploads per minute",
            )

        timestamps.append(now)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    client_ip = request.client.host if request.client else "unknown"
    enforce_upload_rate_limit(client_ip)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File too large")

    scan = scan_bytes(file.filename or "unknown", content)
    # Fail-closed: scanner errors are treated as rejected uploads.
    status = "accepted" if scan.status == "clean" else "rejected"

    record = UploadRecord(
        filename=file.filename,
        content_type=file.content_type,
        status=status,
        scan_status=scan.status,
        scan_engine=scan.engine,
        scan_detail=scan.detail,
    )

    db_status = "skipped"
    try:
        db = get_db()
        await db.uploads.insert_one(record.model_dump())
        db_status = "stored"
    except Exception:
        # Allow uploads even if DB is not configured or available.
        db_status = "unavailable"

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "status": status,
        "scan_status": scan.status,
        "scan_engine": scan.engine,
        "scan_detail": scan.detail,
        "db_status": db_status,
    }


@app.get("/uploads")
async def list_uploads(limit: int = 50):
    try:
        db = get_db()
        cursor = db.uploads.find({}, {"_id": 0}).sort("_id", -1).limit(limit)
        items = [item async for item in cursor]
        return {"items": items}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
