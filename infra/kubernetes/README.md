# Kubernetes deployment

The base uses immutable image tags, non-root pods, default-deny API network policy, resource limits, and liveness/readiness probes. `dev` and `staging` overlays only change the image tag and replica count.

```bash
kubectl apply -k infra/kubernetes/overlays/staging
kubectl -n gatehouse rollout status deployment/gatehouse-api
kubectl -n gatehouse rollout status deployment/gatehouse-web
kubectl -n gatehouse rollout undo deployment/gatehouse-api
```

Create `base/secret.example.yaml` as a sealed/external secret in a real cluster; never commit a populated Secret manifest.
