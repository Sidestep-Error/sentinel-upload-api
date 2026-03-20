# outputs.tf — visas efter terraform apply

output "namespace" {
  description = "Kubernetes-namespace"
  value       = var.namespace
}

output "service_account" {
  description = "ServiceAccount som app-deployments ska använda"
  value       = kubernetes_service_account.sentinel_api.metadata[0].name
}

output "secret_name" {
  description = "Namn på secrets-resursen i klustret"
  value       = kubernetes_secret.sentinel_app_secrets.metadata[0].name
}

output "infrastructure_summary" {
  description = "Sammanfattning av hanterad infrastruktur"
  value       = <<-EOT

============================================
 Sidestep Error | Sentinel Infrastructure
============================================

Namespace       : ${var.namespace}
ServiceAccount  : ${kubernetes_service_account.sentinel_api.metadata[0].name}
Secret          : ${kubernetes_secret.sentinel_app_secrets.metadata[0].name}

Nästa steg:
  App-deployment hanteras av CI/CD via k8s/overlays/gcp/
  Triggas automatiskt vid push till main-branchen.

============================================
  EOT
}
