# ToDo

- [ ] Add bug-report button in UI (link to GitHub Issues)
- [ ] Add Trivy image scan in CI (fail on HIGH/CRITICAL)
- [ ] Add dependency scanning (pip-audit or Trivy fs)
- [ ] Generate SBOM (Syft) and store as CI artifact
- [ ] Sign images with Cosign (bonus)
- [ ] Add Kubernetes manifests (Deployment, Service, Ingress)
- [ ] Gatekeeper policies: no :latest, non-root, resource limits, labels, readOnlyRootFilesystem
- [ ] Add Falco runtime rule and test alert
- [ ] Define SLIs/SLOs in metrics pipeline
- [ ] Set up monitoring (Prometheus/Grafana) and logging
- [ ] Write incident runbook for upload API unavailable
- [ ] Fill in shared responsibility model and cost notes
