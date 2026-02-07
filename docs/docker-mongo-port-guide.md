# Docker + MongoDB Port Guide

## Goal

Avoid host port conflicts (for example with Hyper-V) while keeping container-to-container communication stable.

## Environment modes

- Local Docker Mongo mode:
  - Use `.env.local.example` as template for `.env`.
  - Keep `MONGODB_URI` unset/commented.
- Atlas mode:
  - Use `.env.atlas.example` as template for `.env`.
  - Set `MONGODB_URI` to your Atlas `mongodb+srv://...` value.

## Why this is the best approach

- It separates host concerns from container networking.
- It avoids machine-specific breakage when `27017` is already occupied.
- It keeps the app configuration portable across team members and CI.
- It follows Docker Compose best practice: service-to-service traffic should use service name + internal port.

## Correct setup in `docker-compose.yml`

Use a custom host port, but keep MongoDB container port at `27017`:

```yaml
services:
  mongo:
    image: mongo:7
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_ROOT_USERNAME}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD}
    ports:
      - "28017:27017" # host:container
```

Use internal Docker DNS + container port in the app connection string with auth:

```yaml
services:
  app:
    environment:
      - MONGODB_URI=mongodb://${MONGO_ROOT_USERNAME}:${MONGO_ROOT_PASSWORD}@mongo:27017/${MONGO_DB}?authSource=admin
```

## Important notes

- `mongo:27017` is internal container networking and should normally stay unchanged.
- `28017` is only the host machine port and can be changed to any free port.
- Keep credentials in `.env` (copy from `.env.example`), not hardcoded in compose.
- If you connect to MongoDB from your host tools (for example MongoDB Compass), use `localhost:28017`.

## Verification

```powershell
docker compose down
docker compose up --build
curl -F "file=@README.md;type=text/markdown" http://localhost:8000/upload
curl http://localhost:8000/uploads
```

Expected:

- Upload response includes `"db_status":"stored"`.
- `/uploads` returns an `items` list.
