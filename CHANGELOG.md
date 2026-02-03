# CHANGELOG

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
