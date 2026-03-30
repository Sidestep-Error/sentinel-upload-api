# Hetzner — Automatisk deploy via CI/CD

## Bakgrund

Sentinel Upload API körs på en Hetzner VPS med k3s. Tidigare triggades
deploys manuellt via ett lokalt skript (`deploy-main`). Det här runbooket
beskriver hur vi automatiserat deploys via GitHub Actions med principen
**least privilege** — CI får bara exakt de rättigheter som krävs.

---

## Varför least privilege?

Hetzner-klustrets kubeconfig ger full admin-access. Att lagra den i
GitHub Secrets innebär att om secrets läcker kan en angripare ta full
kontroll över klustret.

Istället skapar vi en dedikerad ServiceAccount (`ci-deploy`) med en
minimal RBAC-roll som bara tillåter `kubectl rollout restart` på
deployments i `sentinel`-namespacet. En läckt CI-token kan bara
trigga en omstart — ingenting annat.

---

## Infrastruktur (Terraform)

Terraform-koden i `infra/terraform/hetzner/` skapar:

| Resurs | Namn | Syfte |
|--------|------|-------|
| ServiceAccount | `ci-deploy` | Identitet för CI/CD |
| Secret | `ci-deploy-token` | Långlivad SA-token (k8s 1.24+) |
| Role | `ci-deploy-role` | Tillåter `get/patch/update` på deployments |
| RoleBinding | `ci-deploy-binding` | Binder rollen till SA:n |

### Köra Terraform

```bash
cd infra/terraform/hetzner
terraform init
terraform plan
terraform apply
```

Terraform behöver tillgång till Hetzner-klustrets kubeconfig. Default
använder den `~/.kube/config` — se `terraform.tfvars.example`.

---

## Generera kubeconfig för GitHub Secrets

Efter `terraform apply` — kör på Hetzner-servern:

```bash
# Hämta token och CA
TOKEN=$(kubectl get secret ci-deploy-token -n sentinel \
  -o jsonpath='{.data.token}' | base64 -d)

CA=$(kubectl get secret ci-deploy-token -n sentinel \
  -o jsonpath='{.data.ca\.crt}')

# Hämta server-URL och byt ut localhost mot publika IP
SERVER=$(kubectl config view --minify \
  -o jsonpath='{.clusters[0].cluster.server}' \
  | sed 's|127.0.0.1|<SERVERNS-PUBLIKA-IP>|')

# Skapa kubeconfig
cat <<EOF > /tmp/ci-deploy-kubeconfig.yaml
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: $CA
    server: $SERVER
  name: hetzner
contexts:
- context:
    cluster: hetzner
    user: ci-deploy
  name: hetzner
current-context: hetzner
users:
- name: ci-deploy
  user:
    token: $TOKEN
EOF

# Base64-koda för GitHub Secrets
base64 -w0 /tmp/ci-deploy-kubeconfig.yaml

# Radera temporär fil
rm /tmp/ci-deploy-kubeconfig.yaml
```

Kopiera outputen → GitHub → Settings → Secrets → **`KUBECONFIG_HETZNER_B64`**.

---

## CI/CD-jobbet (deploy-hetzner)

Jobbet i `.github/workflows/ci.yml` körs automatiskt efter `dockerhub-push`
vid push till `main`. Det:

1. Dekodas kubeconfigen från `KUBECONFIG_HETZNER_B64`
2. Kör `kubectl rollout restart deployment/sentinel-upload-api -n sentinel`
3. Väntar på att rollout är klar (`rollout status --timeout=120s`)
4. Raderar kubeconfigen oavsett utfall (`if: always()`)

---

## Säkerhetsöverväganden

- SA-tokenen har **ingen** tillgång utanför `sentinel`-namespacet
- Tokenen kan bara patcha deployments — inte läsa secrets, skapa pods etc.
- Kubeconfigen raderas alltid från CI-runnern efter deploy
- Om `KUBECONFIG_HETZNER_B64` läcker: rotera token med `kubectl delete secret ci-deploy-token -n sentinel` och kör `terraform apply` igen

---

## Felsökning

| Fel | Trolig orsak | Lösning |
|-----|-------------|---------|
| `Unauthorized` | Token ogiltig eller saknas | Kontrollera att `KUBECONFIG_HETZNER_B64` är korrekt base64-kodad |
| `forbidden: User cannot patch deployments` | RBAC saknas | Kör `terraform apply` på nytt |
| `connection refused` | Server-IP felaktig i kubeconfig | Uppdatera kubeconfigen med rätt publik IP |
| `deployment not found` | Fel namespace | Kontrollera att namespace är `sentinel` |
