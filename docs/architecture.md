# Architecture (High Level)

## Components

- FastAPI service with /health and /upload
- Static UI served from / (app/static)
- Container image based on Alpine for reduced OS CVEs
- MongoDB stores upload metadata (`/upload` and `/uploads`)
- Nginx reverse proxy is the public entrypoint in Docker Compose
- Docker image built in CI
- GitHub Actions CI: test and build
- Kubernetes deployment (planned)
- Security scanning and SBOM in CI (Trivy + Syft)

## Flow

Developer -> GitHub PR -> CI (tests + scan + SBOM) -> Container registry -> Kubernetes

## Notes

- Security gates are enforced in CI and by policy in Kubernetes.
- Observability is provided via logs and metrics (planned).
- For cloud deployment, app runs on Render and connects to MongoDB Atlas via `MONGODB_URI`.
