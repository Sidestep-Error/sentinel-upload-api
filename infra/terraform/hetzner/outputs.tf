# outputs.tf — visas efter terraform apply

output "service_account" {
  description = "CI/CD ServiceAccount"
  value       = kubernetes_service_account.ci_deploy.metadata[0].name
}

output "next_steps" {
  description = "Instruktioner för att generera kubeconfig från SA-token"
  value       = <<-EOT

============================================
 Hetzner | CI/CD Infrastructure
============================================

ServiceAccount  : ${kubernetes_service_account.ci_deploy.metadata[0].name}
Namespace       : ${var.namespace}
Token Secret    : ${kubernetes_secret.ci_deploy_token.metadata[0].name}

Nästa steg — generera kubeconfig för GitHub Secrets:

1. Hämta token och CA från klustret (kör på Hetzner-servern):

   TOKEN=$(kubectl get secret ci-deploy-token -n ${var.namespace} \
     -o jsonpath='{.data.token}' | base64 -d)

   CA=$(kubectl get secret ci-deploy-token -n ${var.namespace} \
     -o jsonpath='{.data.ca\.crt}')

   SERVER=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}' \
     | sed 's|127.0.0.1|<SERVERNS-PUBLIKA-IP>|')

2. Skapa kubeconfig-fil:

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

3. Base64-koda och lägg in i GitHub Secrets som KUBECONFIG_HETZNER_B64:

   base64 -w0 /tmp/ci-deploy-kubeconfig.yaml

4. Radera den temporära filen:

   rm /tmp/ci-deploy-kubeconfig.yaml

============================================
  EOT
}
