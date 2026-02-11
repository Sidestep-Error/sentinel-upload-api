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
# Local Docker Mongo mode
Copy-Item .env.local.example .env
docker compose up --build
```

Run with MongoDB Atlas connection string

```powershell
# Atlas mode
Copy-Item .env.atlas.example .env
# Edit .env and set MONGODB_URI to your Atlas URI
docker compose up --build
```

UI

- Open http://localhost:8080/
- Logo asset: app/static/assets/sidestep-logo.png
- Use the UI upload console to test /upload.
- Uploaded Files list is populated when MongoDB is running.

Nginx reverse proxy

- Nginx is now the public entrypoint in docker compose.
- FastAPI is internal-only in the compose network.
- Nginx host port is configurable (`NGINX_HOST_PORT`, default `8080`).

MongoDB

- Local mode: keep `MONGODB_URI` unset/commented so app uses local Mongo service.
- Atlas mode: set `MONGODB_URI` to Atlas `mongodb+srv://...` URI.
- In docker compose we use env-driven config for both modes.

MongoDB hardening updates (what changed and why)

- MongoDB now starts with username/password.
  - Why: prevents unauthenticated read/write access in local dev.
- App uses `MONGODB_URI` with credentials from environment variables.
  - Why: avoids hardcoded secrets and supports per-developer settings.
- MongoDB host port is configurable (`MONGO_HOST_PORT`, default `28017`).
  - Why: avoids conflicts on machines where `27017` is already used.
- MongoDB healthcheck is enabled and app waits for healthy DB before start.
  - Why: removes startup race conditions and reduces `Database unavailable` errors.
- If you changed local Mongo credentials after first startup, re-initialize local DB:
  - `docker compose down -v`
  - `docker compose up --build`

Health check

```powershell
curl http://localhost:8080/health
```

List uploads (requires MongoDB)

```powershell
curl http://localhost:8080/uploads
```

Upload (PowerShell)

```powershell
curl -F "file=@README.md;type=text/markdown" http://localhost:8080/upload
```

Upload scanning behavior

- Files are scanned in-memory (no file content is persisted).
- MongoDB stores upload metadata and scan outcome (`scan_status`, `scan_engine`, `scan_detail`).
- `SCANNER_MODE=auto` (default): try ClamAV first, fallback to mock scanner if ClamAV is unavailable.
- `SCANNER_MODE=clamav`: require ClamAV.
- `SCANNER_MODE=mock`: mock scanner only.
- Mock scanner flags EICAR marker and suspicious filename patterns.
- Upload policy is fail-closed: non-clean scan results (`malicious` or `error`) are rejected.

Publish on a subdomain (production outline)

1. Create DNS record:
   - Add `A` record: `api.yourdomain.com -> <your server public IP>`.
2. Run the app stack on the server:
   - `docker compose up -d --build`
3. Expose HTTP/HTTPS on the server:
   - Map Nginx to `80:80` for production (set `NGINX_HOST_PORT=80`), and terminate TLS.
4. Enable TLS:
   - Option A: put Caddy/Traefik in front for automatic Let's Encrypt.
   - Option B: keep Nginx and use certbot to manage certificates.
5. Security baseline:
   - Keep `.env` only on server (never commit secrets).
   - Restrict firewall to ports `80/443` only.

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
