# variables.tf — konfigurationsvärden för Sentinel-infrastrukturen
#
# Känsliga variabler (sensitive = true) visas aldrig i terraform plan/apply-output
# och maskeras i Terraform Cloud-loggar. De hamnar dock krypterade i tfstate —
# därför ska tfstate aldrig committas till git (se .gitignore).
#
# Värden sätts i terraform.tfvars (gitignorerad).
# Kopiera terraform.tfvars.example och fyll i riktiga värden.

variable "kubeconfig_path" {
  description = "Sökväg till kubeconfig-filen för GCP-klustret"
  type        = string
  # Default matchar var filen ligger efter Lab-utbildningen.
  # Ändra i terraform.tfvars om din sökväg avviker.
  default     = "~/.kube/sidestep-error-kubeconfig.yaml"
}

variable "namespace" {
  description = "Kubernetes-namespace för Sentinel (kursens namespace, ägs av instruktören)"
  type        = string
  default     = "sidestep-error"
}

variable "team_name" {
  description = "Teamets namn — används som label på resurser för spårbarhet i klustret"
  type        = string
  default     = "sidestep-error"
}

variable "mongodb_uri" {
  description = "MongoDB Atlas connection string inkl. databasnamn och auth"
  type        = string
  # sensitive = true döljer värdet i plan/apply-output och Terraform Cloud-loggar
  sensitive   = true
}

variable "threatfox_api_key" {
  description = "ThreatFox API-nyckel (abuse.ch) — ska aldrig exponeras i loggar eller git"
  type        = string
  sensitive   = true
}
