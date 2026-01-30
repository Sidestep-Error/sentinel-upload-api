Sentinel Upload API

Minimal FastAPI app for secure file upload handling.

Run locally (venv)

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r app/requirements.txt
uvicorn app.main:app --reload

Health check

curl http://localhost:8000/health

Upload (PowerShell)

curl -F "file=@README.md;type=text/markdown" http://localhost:8000/upload

Expected response

{"filename":"README.md","content_type":"text/markdown","status":"accepted"}
