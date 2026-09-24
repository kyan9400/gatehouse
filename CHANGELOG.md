# Changelog

## [Unreleased]

- Moved web build tooling (`@types/react`, `@types/react-dom`, `@vitejs/plugin-react`, `typescript`, `vite`) from `dependencies` to `devDependencies` in `apps/web`.
- Treated blank `GATEHOUSE_*` environment values as unset so optional deployment settings fall back to safe defaults.
- Linked the live FastAPI / OpenAPI demo from the README.

## [0.1.1] - 2026-08-28

- Corrected policy guidance for production read, production mutation, and staging requests in the review console.
- Upgraded Vitest to the patched 3.2.6 release.
- Pinned the Terraform AWS provider lockfile for reproducible infrastructure builds.
- Linked the live dashboard from the README.

## [0.1.0] - 2026-08-28

- Added tenant-scoped access request and approval workflows.
- Added policy-aware TTLs, risk scoring, idempotent writes, and optimistic locking.
- Added hash-linked audit events and Prometheus health signals.
- Added React review desk, Docker Compose, Kubernetes overlays, Terraform, and GitHub Actions release automation.
