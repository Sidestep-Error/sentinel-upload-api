# variables.tf — konfigurationsvärden för Hetzner CI/CD-infrastruktur

variable "kubeconfig_path" {
  description = "Sökväg till kubeconfig för Hetzner k3s-klustret"
  type        = string
  # Default matchar var kubectl normalt letar efter config
  default     = "~/.kube/config"
}

variable "namespace" {
  description = "Kubernetes-namespace där sentinel-upload-api kör"
  type        = string
  default     = "sentinel"
}
