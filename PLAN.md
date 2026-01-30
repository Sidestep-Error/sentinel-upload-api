Snabb översikt (vad ni ska göra och varför)

Ni ska inte bygga en avancerad applikation.
Ni ska bygga en säker leveransmaskin där applikationen bara är ett fordon för:

CI/CD

supply-chain security

policy enforcement

runtime detection

incident response

👉 Appen ska vara tillräckligt enkel för att ni alltid kan fokusera på DevSecOps-delarna.

Rekommenderat projekt (tydligt svar på din fråga)
❌ Avrådan: Full “File Upload Scanner”

Kräver async jobs, storage, AV-hantering

Stor risk att fastna i app-logik

✅ Rekommendation: “Secure Upload API (DevSecOps Demo)”

Detta är en avskalad, kontrollerad version som funkar perfekt för kursen.

Vad appen gör (medvetet enkelt):

POST /upload – tar emot en fil

Validerar:

filstorlek

filtyp (allowlist)

Sparar temporärt (ephemeral)

Kör ClamAV eller mock-scanner

Loggar resultat (OK / MALICIOUS)

GET /health

GET /metrics (Prometheus-vänlig)

Varför detta är perfekt för kursen:

Tydligt säkerhetscase

Lätt att definiera SLIs/SLOs

Perfekt för Falco (file access, exec)

Lätt att simulera incident (malware, DoS, crash)

👉 Detta ger max poäng per investerad timme.

Antaganden vi gör (för att komma framåt)

Eftersom kursen inte specificerar allt, gör vi rimliga, accepterade antaganden:

Kubernetes: lokalt (kind / k3d / minikube)

Registry: GitHub Container Registry

CI/CD: GitHub Actions

IaC: Terraform (för Hetzner – minimal setup eller mock)

Monitoring: Prometheus + Grafana (helm eller manifests)

Logging: Loki eller enklare stdout + kubectl logs

Secrets: GitHub Secrets + K8s secrets

Detta är HELT i linje med kursens innehåll.

Team-organisation (5 personer, kritiskt för att hinna)

Dela upp roller – detta är viktigt för VG.

Roll	Ansvar
App/SRE	App, SLIs/SLOs, chaos
CI/CD	GitHub Actions, build/test
Security	Trivy, SBOM, Cosign
K8s/Policy	Gatekeeper, manifests
Runtime/IR	Falco, runbooks, post-mortem
Vecka-för-vecka-plan (6 veckor, realistisk)
Vecka 1 – Foundation

Mål: Allt bygger, inget säkert än

Repo + branch protection

Minimal app (FastAPI / Express)

Dockerfile (non-root redan nu)

CI: build + unit test + docker build

Deliverable:
✅ CI bygger image på varje PR

Vecka 2 – Security i pipeline

Mål: Stoppa osäkra builds

Trivy image scan (FAIL på HIGH/CRITICAL)

Dependency scan

SBOM (Syft)

SECURITY.md

Deliverable:
✅ Pipeline blockerar sårbara builds

Vecka 3 – Supply-chain & signering

Mål: Lita på det ni deployar

Cosign signering

Verifiering i deploy-steget

Policy: bara signerade images

Deliverable:
✅ End-to-end trusted images

Vecka 4 – Kubernetes & policy

Mål: Tvinga säkerhet i runtime

Deployment + Service

Gatekeeper:

❌ :latest

❌ root

✅ resource limits

✅ labels

✅ readOnlyRootFilesystem

Deliverable:
✅ App kör i K8s – osäkra manifests blockeras

Vecka 5 – Runtime security & observability

Mål: Se och upptäck incidenter

Falco:

shell in container

suspicious file access

Metrics (latency, error rate)

Alerts (1–2 st räcker)

Definiera SLIs/SLOs

Deliverable:
✅ Alert triggas vid simulerad attack

Vecka 6 – SRE, incident & presentation

Mål: Visa mognad

Chaos test:

kill pod

latency spike

Runbook:

“Upload API unavailable”

Post-mortem (simulerad)

Shared Responsibility Model

Kostnadsanalys (kort!)

Deliverable:
✅ VG-redo presentation

Exempel på tydliga SLIs/SLOs (enkelt men proffsigt)

SLI:

HTTP 2xx rate

p95 latency på /upload

SLO:

99.5% successful uploads / 30d

p95 < 500 ms

Koppling till NIST CSF (som lärarna älskar)
NIST	Vad ni visar
PROTECT	Trivy, SBOM, Gatekeeper
DETECT	Falco, metrics, alerts
RESPOND	Runbooks, post-mortem

Skriv detta rakt ut i dokumentationen.