# Operations guide

## Deploy

1. Build and scan the tagged API and web images in GitHub Actions.
2. Copy the image tags into the environment's GitOps repository or Kustomize overlay.
3. Store `GATEHOUSE_DATABASE_URL` and `GATEHOUSE_API_KEY` in the cluster's external secret provider.
4. Apply the overlay and wait for both deployments to become ready.

```bash
kubectl apply -k infra/kubernetes/overlays/staging
kubectl -n gatehouse rollout status deploy/gatehouse-api --timeout=5m
kubectl -n gatehouse rollout status deploy/gatehouse-web --timeout=5m
```

## Verify

```bash
kubectl -n gatehouse port-forward svc/gatehouse-api 8000:80
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
curl -fsS http://127.0.0.1:8000/metrics | grep gatehouse_
```

## Roll back

```bash
kubectl -n gatehouse rollout undo deploy/gatehouse-api
kubectl -n gatehouse rollout undo deploy/gatehouse-web
kubectl -n gatehouse rollout status deploy/gatehouse-api --timeout=5m
```

## Incident first response

- **Decision failures:** check API logs for `409` stale-version responses and confirm the requester still has a pending request.
- **Readiness failures:** check PostgreSQL connectivity and the secret version, then inspect `kubectl describe pod` events.
- **Audit mismatch:** stop decisions, preserve the database snapshot, compare the chain from the first differing `event_hash`, and rotate API credentials if tampering is suspected.

Never delete access-request rows during an incident. Retain the evidence and use a denied/expired decision to close the workflow.
