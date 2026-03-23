# main.tf — Sentinel Upload API infrastruktur (GCP / sidestep-error)
#
# Ansvarsområde: infrastruktur-resurser i klustret som sällan ändras.
# App-deployments (Deployment, Service, NetworkPolicy m.m.) hanteras
# INTE här — de deployas av CI/CD via kubectl apply -k k8s/overlays/gcp/
#
# Uppdelningen följer industri-best-practice:
#   Terraform  →  långlivad infrastruktur (SA, secrets, RBAC)
#   kubectl    →  kortlivade app-resurser (image-uppdateringar vid varje deploy)
#
# Terraform är inte optimalt för image-uppdateringar i CI — det kräver
# terraform apply vid varje push vilket är långsamt och kräver remote state.
#
# Resurser som hanteras:
#   - kubernetes_service_account  (sentinel-api-sa)
#   - kubernetes_secret           (sentinel-app-secrets)
#
# Resurser som INTE hanteras (och varför):
#   - Namespace: kursgemensamt, ägs av instruktören — vi rör det inte
#   - Deployment/Service: hanteras av CI via k8s/overlays/gcp/

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
  }
}

# Kubeconfig-sökvägen är en variabel (inte hårdkodad som i Lab-koden)
# så att olika teammedlemmar kan använda sin lokala fil utan att ändra koden.
provider "kubernetes" {
  config_path = var.kubeconfig_path
}

# ─── ServiceAccount ───────────────────────────────────────────────────────────
# OPA Gatekeeper-policyn "no-default-sa" i GCP-klustret blockerar pods som
# kör med default ServiceAccount. Vi skapar en dedikerad SA för vår app.
#
# SA:n refereras i k8s/overlays/gcp/deployment-patch.yaml via
# serviceAccountName: sentinel-api-sa
resource "kubernetes_service_account" "sentinel_api" {
  metadata {
    name      = "sentinel-api-sa"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"    = "sentinel-upload-api"
      "app.kubernetes.io/part-of" = "sentinel-platform"
      "managed-by"                = "terraform"
      "team"                      = var.team_name
    }
  }
}

# ─── App Secrets ──────────────────────────────────────────────────────────────
# Känsliga värden hämtas från terraform.tfvars (gitignorerad).
# Kopiera terraform.tfvars.example till terraform.tfvars och fyll i värden.
#
# Varför Terraform för secrets och inte kubectl create secret direkt?
#   - Deklarativt: vi vet alltid vad som ska finnas i klustret
#   - Idempotent: terraform apply är säkert att köra igen vid rotation
#   - Audit trail: git-historiken visar när secrets uppdaterades (inte värdet)
#
# Variablerna är märkta sensitive=true i variables.tf — Terraform döljer
# dem i plan/apply-output och de hamnar aldrig i terraform.tfstate i klartext.
resource "kubernetes_secret" "sentinel_app_secrets" {
  metadata {
    name      = "sentinel-app-secrets"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name"    = "sentinel-upload-api"
      "app.kubernetes.io/part-of" = "sentinel-platform"
      "managed-by"                = "terraform"
      "team"                      = var.team_name
    }
  }

  type = "Opaque"

  # data-attributet tar emot värden i klartext — Terraform konverterar
  # internt till base64 innan resursen skapas i klustret (k8s kräver base64).
  data = {
    MONGODB_URI       = var.mongodb_uri
    THREATFOX_API_KEY = var.threatfox_api_key
  }
}
