# GCP Deployment — Design och motivering

Det här dokumentet förklarar vad vi byggt, varför vi valt den lösningen,
och hur det hänger ihop med kursens DevSecOps-mål.

---

## Bakgrund och mål

Projektet kör redan i produktion på en egen Hetzner-server (sentinel-upload.secion.se).
Utbildningen kräver att applikationen också deployas till GCP-klustret i
namespacet `sidestep-error` — utan att störa den befintliga Hetzner-deploymentet.

**Krav vi satte upp:**
- Hetzner-deploymentet ska fungera precis som förut
- GCP-deploymentet ska drivas av samma CI/CD-pipeline (ingen manuell deploy)
- Inga credentials eller secrets i git
- Följa de OPA Gatekeeper-policies som finns i GCP-klustret

---

## Lösning: Kustomize overlays

### Varför Kustomize?

Vi har redan `k8s/base/` med alla Kubernetes-manifests för Hetzner.
Istället för att duplicera allt eller skriva om, använder vi
**Kustomize overlays** — ett verktyg inbyggt i `kubectl` för att
hantera miljöspecifika variationer av samma bas.

```
k8s/
├── base/                   ← Hetzner (oförändrat)
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ...
└── overlays/
    └── gcp/                ← GCP (nytt)
        ├── kustomization.yaml
        ├── namespace.yaml
        ├── serviceaccount.yaml
        └── deployment-patch.yaml
```

GCP-overlayern cherry-pickar de resurser som är relevanta från base och
lägger på GCP-specifika ändringar ovanpå, utan att röra base-filerna.

### Vad overlayern ändrar

| Vad | Hetzner (base) | GCP (overlay) | Anledning |
|-----|---------------|---------------|-----------|
| Namespace | `sentinel` | `sidestep-error` | Kursens namespace i GCP-klustret |
| Image | `jonitsx/sentinel-upload-api` (Docker Hub) | GCP Artifact Registry | Kortare pull-väg, autentisering via GCP SA |
| ServiceAccount | default | `sentinel-api-sa` | OPA-policy `no-default-sa` i klustret |
| ClusterIssuer | Inkluderad (cert-manager) | **Exkluderad** | Hetzner-specifik, finns inte på GCP |
| Ingress | nginx + Let's Encrypt | **Ej konfigurerat än** | GCP-klustrets ingress-setup okänd |

### Varför inte duplicera filerna?

Att kopiera alla YAML-filer till en `gcp/`-mapp hade fungerat men innebär
att samma ändring måste göras på två ställen. Med overlays underhåller vi
bara skillnaderna — resten ärvs automatiskt från base.

---

## CI/CD-pipeline

### Flöde efter förändringen

```
push → main
  │
  ├─ test-and-build        Tester, lint, dep-scan, kubeconform, Trivy, SBOM
  ├─ matrix-tests          Python 3.11 + 3.12
  │
  ├─ dockerhub-push        → Docker Hub (:main + :SHA)   [Hetzner]
  │
  ├─ gcp-push              → GCP Artifact Registry       [GCP, nytt]
  │       ↓
  └─ deploy-gcp            → kubectl apply -k k8s/overlays/gcp/  [GCP, nytt]
```

`dockerhub-push` och `gcp-push` körs parallellt (båda behöver bara
`test-and-build` och `matrix-tests`), vilket håller nere total körtid.

### Varför separata push-jobb?

Hetzner-deploymentet drar image från Docker Hub.
GCP-deploymentet ska dra från GCP Artifact Registry (AR) — samma registry
som vi använde i Lab 2. Anledningar:

- **Auth:** AR autentiseras med GCP Service Account (samma `GCP_SA_KEY`
  som i Lab 2) — inget extra Docker Hub-konto behövs för GCP
- **Latens:** Image är redan i samma GCP-region som klustret
- **Supply-chain:** En image per registry ger tydligare spårbarhet

### Image-taggning med commit SHA

I deploy-steget sätts image-taggen till `github.sha` (inte `:main`):

```yaml
kustomize edit set image \
  jonitsx/sentinel-upload-api=.../jonitsx-app:${{ github.sha }}
```

**Varför?** En tag som `:main` kan pekas om till en ny image utan att
k8s märker det (immutable tags är bäst practice). Med SHA vet vi exakt
vilken image som kör — viktigt för spårbarhet och incident response.
Samma princip använde vi för cosign-signering i Lab 2.

---

## Secrets-hantering

Secrets deployas **inte** via CI eller git. De skapas manuellt i
klustret en gång och lever sedan kvar:

```bash
kubectl create secret generic sentinel-app-secrets \
  --from-literal=MONGODB_URI="..." \
  --from-literal=THREATFOX_API_KEY="..." \
  -n sidestep-error
```

**Varför inte i CI?** Att ha secrets som CI-variabler som sedan
skrivs till klustret ökar attackytan. Manuell hantering av k8s-secrets
är acceptabelt i utbildningsmiljö. I produktion skulle vi använda
External Secrets Operator eller GCP Secret Manager.

Kubeconfigen för GCP-klustret lagras base64-kodad i GitHub Secrets
(`KUBECONFIG_GCP_B64`) och skrivs till en temporär fil under deploy-jobbet —
filen raderas alltid i ett `if: always()`-steg för att inte läcka credentials.

---

## OPA Gatekeeper-compliance

GCP-klustret har ett antal förinstallerade policies. Vi har adresserat
dessa i overlayern:

| Policy | Hur vi möter den |
|--------|-----------------|
| `no-default-sa` | Dedikerad `sentinel-api-sa` ServiceAccount i overlay |
| `no-latest-tag` | Image taggas med `github.sha` i CI, aldrig `:latest` |
| `require-non-root` | `runAsNonRoot: true`, `runAsUser: 10001` — ärvs från base |
| `require-resource-limits` | CPU/memory limits — ärvs från base |
| `require-readonly-rootfs` | `readOnlyRootFilesystem: true` + `/tmp` emptyDir — ärvs från base |
| `require-labels` | `app.kubernetes.io/name` och `part-of` — ärvs från base |

---

## Koppling till NIST CSF

| NIST-funktion | Vad detta steg bidrar med |
|--------------|--------------------------|
| **PROTECT** | Image från GCP AR (kortare leveranskedja), OPA-policies enforced, secrets ur git |
| **DETECT** | Deployment med SHA-tag → tydlig audit trail om incident inträffar |
| **RESPOND** | Runbook finns i `docs/gcp-deployment-runbook.md` för att kunna agera snabbt |

---

## Vad som återstår

- [ ] Konfigurera Ingress för GCP-klustret när domän/ingress-controller är känd
- [ ] Hämta kubeconfig från instruktör och lägg till `KUBECONFIG_GCP_B64` i GitHub Secrets
- [ ] Skapa `sentinel-app-secrets` i `sidestep-error`-namespace i GCP-klustret
- [ ] (Framtida) Lägg till cosign-verifiering i deploy-steget
- [ ] (Framtida) Ersätt manuell secrets-hantering med External Secrets Operator
