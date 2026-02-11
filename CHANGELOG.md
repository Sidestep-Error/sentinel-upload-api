# CHANGELOG

## 2026-02-11

- Added an upload mock scanner (`app/scanner.py`) to detect malicious signatures without storing file content.
- Added ClamAV service integration in Docker Compose with scanner modes (`auto`, `clamav`, `mock`).
- Extended upload metadata model with scan fields (`scan_status`, `scan_engine`, `scan_detail`).
- Updated `/upload` flow to scan in memory, enforce max file size, and persist scan result metadata in MongoDB.
- Added upload tests for clean and malicious file paths.

## 2026-02-07

- Added Nginx reverse proxy service in Docker Compose as public entrypoint (`NGINX_HOST_PORT`).
- Added Atlas/local environment mode templates (`.env.atlas.example`, `.env.local.example`).
- Updated app startup to respect `PORT` for Render compatibility.
- Improved Mongo DB selection fallback in `app/db.py` when URI has no default database path.
- Updated deployment docs for Docker Compose, Atlas usage, and Render flow.

## 2026-02-03

- Implemented MongoDB-backed upload metadata flow in the API (`/upload` stores metadata, `/uploads` lists records).
- Added Docker Compose support for app + MongoDB and documented local startup with compose.
- Hardened MongoDB runtime setup with env-driven credentials, healthcheck, and app startup dependency on healthy DB.
- Added `.env.example` and updated docs (`README.md` and `docs/docker-mongo-port-guide.md`) with port/auth best practices.
- Resolved host port conflict strategy by exposing MongoDB on `28017` while keeping internal container communication on `27017`.

## 2026-02-02

- Identified a UI bug where the file picker could open twice for some users.
- Patched `app/static/index.html` to prevent double-trigger from dropzone/label clicks.
- Added safer file input handling so the same file can be selected again after upload.
