# ToDo

- [ ] Add bug-report button in UI (link to GitHub Issues)
- [x] Add Trivy image scan in CI (fail on HIGH/CRITICAL)
- [x] Add dependency scanning (pip-audit or Trivy fs)
- [x] Generate SBOM (Syft) and store as CI artifact
- [x] Switch base image to Alpine to reduce OS CVEs
- [x] Add MongoDB storage for upload metadata
- [x] Add file-scanning for malicious code to uploaded files (mock scanner)
- [x] Integrate ClamAV scanner service (auto mode with mock fallback)
- [x] Enforce fail-closed policy when scanner is unavailable
- [ ] Sign images with Cosign (bonus)
- [x] Add Kubernetes manifests (Deployment, Service, Ingress)
- [x] Gatekeeper policies: no :latest, non-root, resource limits, labels, readOnlyRootFilesystem
- [ ] Add Falco runtime rule and test alert
- [ ] Define SLIs/SLOs in metrics pipeline
- [ ] Set up monitoring (Prometheus/Grafana) and logging
- [ ] Write incident runbook for upload API unavailable
- [ ] Fill in shared responsibility model and cost notes
- [x] Change Mongo port fom 27017 to 28017 since 27017 is blocked by HyperV
- [ ] Add Firebase Auth + FastAPI tokencheck

## Open issues (2026-05-26)

- [ ] **ClamAV signature updates** — `backend`-nätverket har `internal: true`, vilket blockerar `freshclam`s tillgång till `database.clamav.net`. ClamAV kör nu med image-bundled signaturer (OK för demo, ej för prod).
  - Förslag på lösningar (i ordning, från enklast till mest "rätt"):
    1. Skapa `docker-compose.dev.yml` overlay som sätter `internal: false` på backend för lokal dev.
    2. Lägg till en `freshclam`-sidecar på `frontend`-nätverket som monterar `clamav_db`-volymen och uppdaterar signaturer periodiskt.
    3. I produktion: använd cluster-internt egress via NetworkPolicy (lämna `internal: true` i compose).
- [ ] **ThreatFox API 403 Forbidden** — bara denna feed failar; Feodo (4 events) och URLhaus (826 events) fungerar.
  - Verifieringssteg i ordning:
    1. Öppna `.env`, kolla att `THREATFOX_API_KEY=<värde>` saknar citationstecken och whitespace runt värdet.
    2. Logga in på https://auth.abuse.ch/ och verifiera att nyckeln är aktiv och inte utgången.
    3. Bekräfta att det är en ThreatFox-nyckel (abuse.ch har separata nycklar per feed).
    4. Om allt ovan ser OK ut: testa nyckeln manuellt med `curl -X POST -H "Auth-Key: <key>" -H "Content-Type: application/json" -d '{"query":"get_iocs","days":1}' https://threatfox-api.abuse.ch/api/v1/`. Då vet vi om det är vår kod eller deras API.
- [ ] **Onboarding-not för `.env`-variabelnamn** — variabelnamn-bytet `MONGO_ROOT_USERNAME` → `MONGO_USERNAME` (och motsvarande för PASSWORD) i en tidigare merge gjordes utan team-broadcast. Lägg till en kort sektion i README eller en `MIGRATION.md` med checklistan: "om din `.env` är från före 2026-XX-XX, byt namn på dessa rader". Förhindrar att fler i teamet hamnar i samma timeout som hände 2026-05-26.

