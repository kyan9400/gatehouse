.PHONY: api-lint api-test web-install web-check build infra

api-lint:
	cd services/api && python -m ruff check app tests

api-test:
	cd services/api && python -m pytest -q

web-install:
	cd apps/web && npm ci

web-check:
	cd apps/web && npm run typecheck && npm test && npm run build

build:
	docker compose build

infra:
	kubectl kustomize infra/kubernetes/overlays/dev
