Sentinel Upload API

Minimal FastAPI app for secure file upload handling.

Docs index

- PLAN.md
- SECURITY.md
- GITHUB-BEST-PRACTICE.md
- docs/architecture.md
- docs/docker-mongo-port-guide.md
- docs/shared-responsibility.md
- sre/sli-slo.md
- runbooks/upload-api-unavailable.md
- sre/postmortem-template.md
- ToDo.md
- CHANGELOG.md

Run locally (Docker)

```powershell
docker build -f docker/Dockerfile -t sentinel-upload-api:dev .
docker run --name sentinel -p 8000:8000 sentinel-upload-api:dev
```

Run locally with MongoDB (docker compose)

```powershell
# First time: copy example env and set your own password
Copy-Item .env.example .env
docker compose up --build
```

UI

- Open http://localhost:8000/
- Logo asset: app/static/assets/sidestep-logo.png
- Use the UI upload console to test /upload.
- Uploaded Files list is populated when MongoDB is running.

MongoDB

- Set MONGODB_URI to enable storage.
- Example: mongodb://localhost:27017/sentinel_upload
- In docker compose we now use authenticated MongoDB with env-driven config.

MongoDB hardening updates (what changed and why)

- MongoDB now starts with username/password.
  - Why: prevents unauthenticated read/write access in local dev.
- App uses `MONGODB_URI` with credentials from environment variables.
  - Why: avoids hardcoded secrets and supports per-developer settings.
- MongoDB host port is configurable (`MONGO_HOST_PORT`, default `28017`).
  - Why: avoids conflicts on machines where `27017` is already used.
- MongoDB healthcheck is enabled and app waits for healthy DB before start.
  - Why: removes startup race conditions and reduces `Database unavailable` errors.

Health check

```powershell
curl http://localhost:8000/health
```

List uploads (requires MongoDB)

```powershell
curl http://localhost:8000/uploads
```

Upload (PowerShell)

```powershell
curl -F "file=@README.md;type=text/markdown" http://localhost:8000/upload
```

Expected response

Optional: Run locally (venv)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r app/requirements.txt
uvicorn app.main:app --reload
```

```json
{"filename":"README.md","content_type":"text/markdown","status":"accepted"}
```
