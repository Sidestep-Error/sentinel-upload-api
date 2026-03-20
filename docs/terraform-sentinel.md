# Terraform — Sentinel infrastruktur (GCP)

Terraform hanterar **infrastruktur-resurser** i `sidestep-error`-namespacet.
App-deployments hanteras separat av CI/CD via Kustomize.

```
Terraform ansvar          kubectl/kustomize ansvar
─────────────────         ────────────────────────
ServiceAccount            Deployment
Secret                    Service
                          ConfigMap
                          NetworkPolicy
```

---

## Struktur

```
infra/terraform/sentinel/
├── main.tf                   ← provider + resurser
├── variables.tf              ← variabler med beskrivningar
├── outputs.tf                ← sammanfattning efter apply
└── terraform.tfvars.example  ← mall för känsliga värden (gitignorerad)
```

---

## Komma igång (första gången)

### 1. Skapa tfvars-fil

```bash
cd infra/terraform/sentinel
cp terraform.tfvars.example terraform.tfvars
```

Fyll i `terraform.tfvars` med riktiga värden:

```hcl
kubeconfig_path   = "~/.kube/sidestep-error-kubeconfig.yaml"
mongodb_uri       = "mongodb+srv://..."
threatfox_api_key = "din-nyckel"
```

> `terraform.tfvars` är gitignorerad — ska aldrig committas.

### 2. Initiera Terraform

```bash
terraform init
```

### 3. Planera och applicera

```bash
terraform plan
terraform apply
```

Kontrollera outputen — du ska se `ServiceAccount` och `Secret` skapas i klustret.

---

## Verifiera i klustret

```bash
kubectl get serviceaccount sentinel-api-sa -n sidestep-error
kubectl get secret sentinel-app-secrets -n sidestep-error
```

---

## Ansvarsuppdelning — varför så här?

| Lager | Verktyg | Anledning |
|-------|---------|-----------|
| Infrastruktur (SA, secrets) | Terraform | Deklarativt, versionerat, audit trail |
| App-deployment | kubectl + Kustomize | Snabbare image-uppdateringar i CI, inget Terraform-state att låsa |
| CI/CD-pipeline | GitHub Actions | Automatiserad leverans vid push till main |

Terraform är inte optimalt för att hantera image-taggar i CI — det kräver `terraform apply` vid varje deploy vilket är långsamt och kräver antingen lokal state eller Terraform Cloud. Kustomize + kubectl i CI är rätt verktyg för det jobbet.

---

## Uppdatera secrets

Om MongoDB URI eller ThreatFox-nyckeln byts ut:

```bash
# Uppdatera terraform.tfvars, sedan:
terraform apply
```

Terraform uppdaterar bara det som förändrats — övriga resurser rörs inte.

---

## Relaterade dokument

- [gcp-deployment-runbook.md](gcp-deployment-runbook.md) — full deploy-guide
- [gcp-deployment-design.md](gcp-deployment-design.md) — designbeslut och motivering
