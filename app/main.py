import os
from pathlib import Path

from fastapi import Depends, FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth import auth_mode, require_auth
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/auth/config")
def auth_config():
    mode = auth_mode()
    return {
        "mode": mode,
        "firebase_web_api_key": os.getenv("FIREBASE_WEB_API_KEY", "").strip() if mode == "firebase" else "",
    }


@app.post("/upload")
async def upload(file: UploadFile = File(...), _auth=Depends(require_auth)):
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
async def list_uploads(limit: int = 50, _auth=Depends(require_auth)):
    try:
        db = get_db()
        cursor = db.uploads.find({}, {"_id": 0}).sort("_id", -1).limit(limit)
        items = [item async for item in cursor]
        return {"items": items}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
