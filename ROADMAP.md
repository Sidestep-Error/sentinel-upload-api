# ROADMAP — Sentinel Upload API

> **Senast uppdaterad:** 2026-05-26
> **Status:** Post-delivery / hotfix- och hardening-fas.
> Kursen är levererad (2026-04-01). Den här roadmapen styr prioriteringen
> framåt.

Den ursprungliga 6-veckorsplanen för kursen finns kvar som historiskt
referensmaterial i [PLAN.md](PLAN.md). Backlog med ägarfördelning finns
i [ToDo.md](ToDo.md) och [ToDo-intern.md](ToDo-intern.md).

---

## Vision

Sentinel Upload API ska fortsätta vara ett **trovärdigt
referensprojekt för DevSecOps-praktik**: en liten, säker applikation
där hela leveranskedjan — från `git push` till runtime — kan användas
för att demonstrera, testa och utbilda kring CI/CD, supply chain
security, policy enforcement, runtime detection och incident response.

Vi bygger inte fler app-features om de inte tjänar minst ett av följande:

1. Bredda säkerhetsytan på ett pedagogiskt sätt
2. Förbättra observability eller resiliens
3. Minska driftsbörda eller risk

---

## Faser

### Fas 0 — Grund (KLAR ✅)

Kursveckorna 1–10. Levererat enligt PLAN.md.

- [x] Repo + branch protection + PR-workflow
- [x] FastAPI-app med `/upload`, `/uploads`, `/health`, `/metrics/summary`
- [x] Dockerfile non-root, Alpine/Debian-slim, split prod/dev deps
- [x] Docker Compose med Nginx + API + MongoDB + ClamAV
- [x] CI: `pip-audit`, `ruff`, `pytest` (matrix 3.11/3.12), Trivy, Syft SBOM, `kubeconform`
- [x] Härdad MongoDB (auth, healthcheck, TTL-index, env-driven URI)
- [x] Härdad container-runtime (cap_drop, no-new-privileges, read_only, tmpfs)
- [x] Kubernetes på Hetzner k3s (Deployment, Service, Ingress, NetworkPolicy)
- [x] cert-manager + Let's Encrypt → HTTPS på `sentinel-upload.secion.se`
- [x] Terraform: least-privilege `ci-deploy` SA + RBAC
- [x] Automatisk deploy till Hetzner via `kubectl rollout restart` i CI
- [x] Threat intel-pipeline (CISA KEV, Feodo, URLhaus, ThreatFox)
- [x] GeoIP-anrikad threat map UI
- [x] Riskbedömning + deduplication + fail-closed-policy på `/upload`
- [x] Rate limiting med dynamisk cleanup
- [x] Server-side filvalidering (path traversal, content-type spoofing, XSS via filnamn)
- [x] Härdad `docker-compose.yml` (network-isolering, frontend/backend)
- [x] Individuell reflektionsrapport + gruppresentation

---

### Fas 1 — Stabilisering (PÅGÅR — Q2 2026)

**Mål:** Stänga eftersläntande items från kursens ToDo och säkra att
produktion fortsätter rulla utan manuell babysitting.

**Prioriterade items:**

- [ ] **Cosign image signing** — signera produktionsimages med digest,
  verifiera i deploy-steget. Implementera enligt mönstret i
  [docs/ci_cd_notes.md](docs/ci_cd_notes.md). *(Bonus från Vecka 3 i PLAN)*
- [ ] **Falco runtime-regel + test-alert** — minst en regel som larmar
  vid `shell in container` eller suspekt filåtkomst i `sentinel`-namespacet.
  Demonstrera triggning. *(Vecka 5 i PLAN)*
- [ ] **Definiera SLIs/SLOs formellt i `sre/sli-slo.md`** — utgå från
  redan exponerade metrics (`/health`, `/metrics/summary`). Förslag:
  - SLI: HTTP 2xx rate på `/upload`
  - SLI: p95 latency på `/upload`
  - SLO: 99,5 % lyckade uppladdningar / 30 dagar
  - SLO: p95 < 500 ms
- [ ] **Prometheus + Grafana** (Joline) — minst dashboard med:
  upload-rate, error-rate, p95 latency, scan-status-fördelning,
  rate-limit-hits.
- [ ] **Bug-report-knapp i UI** — länk till GitHub Issues med
  förifylld template (browser, version, steg).
- [ ] **Hotfix-cleanup:** verifiera att `hotfix/upload-requestheaders-fix`
  är komplett mergad och att inga `requestHeaders`-rester finns kvar
  efter Firebase-borttagningen.

**Definition of Done för fas 1:** Allt i ToDo.md som inte är markerat
"bonus" är klart eller medvetet bortprioriterat med motivering i
denna fil.

---

### Fas 2 — Operations-mognad (Q3 2026)

**Mål:** Gå från "fungerar i produktion" till "kan driftas av någon
som inte byggde det".

- [ ] **Komplettera runbooks** — utöka `runbooks/upload-api-unavailable.md`
  med åtgärder för: ClamAV-pod restart-loop, MongoDB-anslutningsfel,
  cert-manager-renewal-fail, full disk på Hetzner-noden.
- [ ] **Chaos test** (Vecka 6 i PLAN) — dokumenterad körning av:
  - Pod kill (`kubectl delete pod`)
  - Latency injection (chaos-mesh eller `tc`)
  - ClamAV down → verifiera fail-closed beteende
- [ ] **Post-mortem från en simulerad incident** — fyll i
  `sre/postmortem-template.md` med ett realistiskt scenario.
- [ ] **Shared Responsibility Model** — utöka
  [docs/shared-responsibility.md](docs/shared-responsibility.md) med
  konkreta cell-för-cell-svar (Hetzner vs team, GCP vs team).
- [ ] **Kostnadsanalys** — sammanställ månadlig driftskostnad
  (Hetzner VPS, MaxMind GeoIP, domän, eventuell Atlas) och
  jämför mot motsvarande managed-stack på GCP/AWS.
- [ ] **Image-tag-policy enforcement** — Gatekeeper-constraint som
  blockerar `:latest`-tag i `sentinel`-namespacet. Verifiera att alla
  manifest använder commit-SHA-tag.
- [ ] **Backup/restore-rutin för MongoDB** — dokumentera och testa.
  RPO/RTO-mål.

---

### Fas 3 — Säkerhetsdjup (Q4 2026)

**Mål:** Höja säkerhetshöjden bortom kursminimum.

- [ ] **Authentication tillbaka, korrekt** — om use-caset kräver det,
  återinför auth med mer mogen lösning än Firebase. Kandidater:
  - OAuth2/OIDC mot extern IdP
  - Mutual TLS för API-klienter
  - API-nyckel + HMAC-signering
  - Lämna `AUTH_MODE=off` om publikt demo räcker
- [ ] **Audit log** — separat append-only log för säkerhetsrelevanta
  events (upload accepted/rejected, rate limit hit, scan error,
  auth failure om återinförd).
- [ ] **WAF eller fronting-CDN** — Cloudflare/Caddy framför Nginx för
  DDoS-skydd, geoblockering, bot-mitigation.
- [ ] **Secret rotation-rutin** — dokumentera och testa rotation av:
  Docker Hub-token, kubeconfig-token (`ci-deploy`), Cosign-nyckel,
  ThreatFox API-key.
- [ ] **Dependabot + automatisk patch-PR** — eller Renovate.
- [ ] **OWASP API Top 10-genomgång** — dokumenterad self-assessment
  mot varje punkt.
- [ ] **SLSA-nivå-uppgradering** — sikta på SLSA Level 2 eller 3 för
  build-provenance (kräver Cosign + provenance attestation).

---

### Fas 4 — Pedagogiskt material (löpande)

**Mål:** Återanvändbart för framtida kursomgångar och egen portfolio.

- [ ] Skapa kort screencast/walkthrough som visar:
  push → CI → signering → deploy → live.
- [ ] Markdown-tutorial: "Bygg din egen DevSecOps-pipeline från noll"
  med detta repo som referens.
- [ ] Lab-mall: medvetet sårbar baseline-image + härdad slutimage,
  med Trivy-diff (likt Lab 2 i kursen).
- [ ] Översätt valda runbooks till engelska för bredare räckvidd.

---

## Vad vi medvetet INTE bygger

För att hålla fokus tackar vi nej till:

- **Avancerad applogik** — file-versioning, sharing-länkar, kommentarer
  på uppladdningar etc. Appen är ett *fordon* för säkerhetsarbete.
- **Multi-tenancy.** En tenant räcker för det här syftet.
- **Realtid-collab/WebSocket.** Lägger till mycket attackyta utan
  pedagogisk vinst.
- **Full async job queue** (Celery/RQ) — synkron scanning + APScheduler
  räcker, och bakgrundsjobb är redan demonstrerat via threat intel.
- **GCP som primär prod** — Hetzner är produktionsmiljön. GCP är
  inlärningsplattform och `gcp-push`/`deploy-gcp`-jobben är pausade.

---

## Beslut och rationale

**2026-02-18:** Firebase auth borttagen. *Varför:* minska attackyta för
publikt demo som inte kräver login. AUTH_MODE-kod kvar för att kunna
slå på igen om behov uppstår.

**2026-02-25:** Hetzner k3s valt som primär produktion framför GKE.
*Varför:* äkta driftsansvar utan managed control plane → SRE-lärande.
GKE behållet som lärandeyta.

**2026-03-30:** GCP-jobben i CI (`gcp-push`, `terraform-gcp`,
`deploy-gcp`) inaktiverade (`if: false`). *Varför:* GCP-miljön avvecklad
efter kursen, men koden behållen för referens.

**Pågående:** ROADMAP konsolideras härifrån. ToDo.md/ToDo-intern.md
behålls som arbetslistor men ROADMAP styr fasprioritet.

---

## Hur du jobbar mot denna roadmap

1. Plocka ett item från **aktuell fas** (helst Fas 1 just nu).
2. Skapa branch enligt namnschemat i [CLAUDE.md](CLAUDE.md) och
   [GITHUB-BEST-PRACTICE.md](GITHUB-BEST-PRACTICE.md).
3. När item är klart: bocka av här, uppdatera relevant sektion i
   [CHANGELOG.md](CHANGELOG.md), och justera [ToDo.md](ToDo.md).
4. Om en ny idé dyker upp: lägg den i rätt fas (eller "Inte bygger")
   istället för att smyga in den i pågående arbete.
