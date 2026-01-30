from fastapi import FastAPI, UploadFile, File, HTTPException

app = FastAPI(title="Sentinel Upload API")

ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "application/pdf",
    "image/png",
    "image/jpeg",
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type")

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "status": "accepted",
    }