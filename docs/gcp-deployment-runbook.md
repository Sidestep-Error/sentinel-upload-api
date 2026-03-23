# GCP Deployment Runbook — ChasAcademy namespace (sidestep-error)

Steg-för-steg för att sätta upp och deploya Sentinel Upload API till GCP-klustret
som används i utbildningen. Hetzner-deploymentet (sentinel-upload.secion.se) påverkas inte.

---

## Förutsättningar

| Vad | Status |
|-----|--------|
| GCP-projekt `chas-devsecops-2026` | Satt upp av instruktören |
| Namespace `sidestep-error` i klustret | Ska finnas — kontrollera med instruktören |
| `GCP_SA_KEY` i GitHub Secrets | Från Lab 2 — redan inne |
| `MAXWIND_LICENSE_KEY` i GitHub Secrets | Från Lab 2 — redan inne |
| `KUBECONFIG_GCP_B64` i GitHub Secrets | **Måste läggas till — se steg 1** |
| `sentinel-app-secrets` i klustret | **Måste skapas manuellt — se steg 2** |

---

## Steg 1 — Lägg till KUBECONFIG_GCP_B64 i GitHub Secrets

Hämta kubeconfigen för GCP-klustret från instruktören eller Mission Control.
Spara den som en lokal fil (t.ex. `gcp-kubeconfig.yaml`) och koda den:

```bash
# Linux / Git Bash
base64 -w0 gcp-kubeconfig.yaml

# PowerShell
[Convert]::ToBase64String([System.IO.File]::ReadAllBytes("C:\full\path\to\gcp-kubeconfig.yaml"))
```

Lägg till värdet i GitHub → Settings → Secrets and variables → Actions:
- **Name:** `KUBECONFIG_GCP_B64`
- **Value:** base64-strängen ovan

> Ta bort den lokala filen efteråt — den innehåller kluster-credentials.

---

## Steg 2 — Skapa secrets i GCP-klustret (en gång)

Secrets hanteras utanför git och deployas inte via CI. Skapa dem manuellt:

```bash
kubectl create secret generic sentinel-app-secrets \
  --from-literal=MONGODB_URI="mongodb+srv://<user>:<password>@<cluster>/<db>?retryWrites=true&w=majority" \
  --from-literal=THREATFOX_API_KEY="<din-nyckel>" \
  -n sidestep-error
```

Verifiera:
```bash
kubectl get secret sentinel-app-secrets -n sidestep-error
```

> Mall finns i `k8s/overlays/gcp/secret.example.yaml`.

---

## Steg 3 — Verifiera overlay lokalt (valfritt)

Kontrollera att Kustomize genererar rätt manifests innan push:

```bash
# Installera kustomize om du inte har det
# https://kubectl.docs.kubernetes.io/installation/kustomize/

kustomize build k8s/overlays/gcp/
```

Kontrollera att:
- `namespace: sidestep-error` på alla resurser
- `image:` pekar på `europe-north1-docker.pkg.dev/chas-devsecops-2026/student-apps/jonitsx-app`
- `serviceAccountName: sentinel-api-sa` i Deployment

---

## Steg 4 — Trigga deploy via CI

Deploy sker automatiskt vid push till `main`. Kontrollera att alla tre jobs går igenom:

```
test-and-build  ✓
matrix-tests    ✓
gcp-push        ✓  (bygger och pushar till GCP Artifact Registry)
deploy-gcp      ✓  (kör kubectl apply -k k8s/overlays/gcp/)
```

Följ körningen under: **GitHub → Actions → senaste workflow-körning**

---

## Steg 5 — Verifiera deployment i klustret

```bash
# Pods igång?
kubectl get pods -n sidestep-error

# Deployment status
kubectl rollout status deployment/sentinel-upload-api -n sidestep-error

# Loggar
kubectl logs -n sidestep-error deployment/sentinel-upload-api

# ClamAV
kubectl logs -n sidestep-error deployment/clamav
```

---

## Ingress / domän (ej konfigurerat ännu)

GCP-klustrets ingress-setup är inte känd i skrivande stund. När det är klart:

1. Lägg till `k8s/overlays/gcp/ingress.yaml` med GCP-anpassade annotationer
2. Lägg till filen i `k8s/overlays/gcp/kustomization.yaml` under `resources:`
3. Ta bort kommentaren om ingress i kustomization.yaml

---

## Felsökning

| Fel | Trolig orsak | Åtgärd |
|-----|-------------|--------|
| `ImagePullBackOff` | SA saknar pull-rättigheter på GCP AR | Kontakta instruktör — be om `roles/artifactregistry.reader` på SA:n |
| `artifactregistry... denied` (push) | SA saknar skrivrättigheter | Kontakta instruktör — be om `roles/artifactregistry.writer` |
| `no-default-sa` varning från OPA | Deployment använder default SA | `sentinel-api-sa` ServiceAccount skapas av overlay — ska lösa sig |
| `secret "sentinel-app-secrets" not found` | Secret ej skapat i klustret | Kör steg 2 ovan |
| `KUBECONFIG_GCP_B64` error i CI | Secret saknas eller felaktigt kodat | Kontrollera GitHub Secret — koda om vid behov |
| Deploy-jobbet hoppas över | Push gick inte till `main` | Jobbet triggas bara på `push: branches: [main]` |
