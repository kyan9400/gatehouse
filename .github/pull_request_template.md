## What changed?

<!-- Explain the user or operator outcome. -->

## Verification

- [ ] `ruff check app tests`
- [ ] `pytest -q`
- [ ] `npm run typecheck && npm test && npm run build`
- [ ] Kubernetes/Terraform validation (if infrastructure changed)

## Safety

- [ ] No credentials or real access-request data are included.
- [ ] Rollback path is documented for production-impacting changes.
- [ ] Threat-model impact is understood.
