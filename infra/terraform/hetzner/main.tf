# main.tf — CI/CD-infrastruktur för Hetzner k3s-kluster
#
# Ansvarsområde: Skapar en dedikerad ServiceAccount med minimal behörighet
# för att CI/CD-pipelinen ska kunna trigga deploys utan att ha full
# admin-access till klustret.
#
# Principen "least privilege":
#   CI behöver bara kunna köra "kubectl rollout restart" på vår deployment.
#   Istället för att ge CI hela admin-kubeconfigen skapar vi en SA med
#   exakt de rättigheter som krävs — inget mer.
#
# Resurser som hanteras:
#   - kubernetes_service_account  (ci-deploy)
#   - kubernetes_secret           (ci-deploy-token) — långlivad SA-token
#   - kubernetes_role             (ci-deploy-role)  — minimal RBAC
#   - kubernetes_role_binding     (ci-deploy-binding)

terraform {
  # State lagras lokalt för Hetzner-infrastrukturen.
  # Varför inte GCS som för GCP-projektet?
  #   Hetzner-infrastrukturen är enklare och körs bara lokalt — inte i CI.
  #   Om teamet vill dela state i framtiden kan GCS-backend läggas till här.
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
  }
}

# Kubeconfig-sökvägen är en variabel så att olika teammedlemmar
# kan använda sin lokala fil utan att ändra koden.
provider "kubernetes" {
  config_path = var.kubeconfig_path
}

# ─── ServiceAccount ───────────────────────────────────────────────────────────
# Dedikerad SA för CI/CD — används bara för att trigga rollout restarts.
# Separationen från app-SA:n (sentinel-api-sa) gör att CI-credentials
# och app-credentials aldrig blandas ihop.
resource "kubernetes_service_account" "ci_deploy" {
  metadata {
    name      = "ci-deploy"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/part-of" = "sentinel-platform"
      "managed-by"                = "terraform"
      "purpose"                   = "ci-cd"
    }
  }
}

# ─── SA-token ─────────────────────────────────────────────────────────────────
# Kubernetes 1.24+ skapar inte längre tokens automatiskt för SA:er.
# Vi skapar en explicit långlivad token via en Secret av typen
# kubernetes.io/service-account-token.
#
# Tokenen base64-kodas och lagras som KUBECONFIG_HETZNER_B64 i GitHub Secrets.
# Se outputs.tf för instruktioner om hur kubeconfigen genereras.
resource "kubernetes_secret" "ci_deploy_token" {
  metadata {
    name      = "ci-deploy-token"
    namespace = var.namespace
    annotations = {
      # Kopplar token-secreten till vår SA
      "kubernetes.io/service-account.name" = kubernetes_service_account.ci_deploy.metadata[0].name
    }
    labels = {
      "managed-by" = "terraform"
      "purpose"    = "ci-cd"
    }
  }

  type = "kubernetes.io/service-account-token"
}

# ─── Role ─────────────────────────────────────────────────────────────────────
# Minimal RBAC-roll — bara exakt det som krävs för "kubectl rollout restart"
# följt av "kubectl rollout status".
#
# Varför detta?
#   "kubectl rollout restart" patchar deployment:ens pod-template med en
#   restart-annotation (kubectl.kubernetes.io/restartedAt).
#   k8s kräver get innan patch.
#
#   "kubectl rollout status" behöver list + watch för att kunna bevaka
#   deploymentens framsteg tills rollout är klar.
resource "kubernetes_role" "ci_deploy_role" {
  metadata {
    name      = "ci-deploy-role"
    namespace = var.namespace
    labels = {
      "managed-by" = "terraform"
      "purpose"    = "ci-cd"
    }
  }

  rule {
    api_groups = ["apps"]
    resources  = ["deployments"]
    verbs      = ["get", "list", "watch", "patch", "update"]
  }
}

# ─── RoleBinding ──────────────────────────────────────────────────────────────
# Binder rollen till SA:n — utan denna har SA:n inga rättigheter
# trots att rollen är definierad.
resource "kubernetes_role_binding" "ci_deploy_binding" {
  metadata {
    name      = "ci-deploy-binding"
    namespace = var.namespace
    labels = {
      "managed-by" = "terraform"
      "purpose"    = "ci-cd"
    }
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.ci_deploy_role.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.ci_deploy.metadata[0].name
    namespace = var.namespace
  }
}
