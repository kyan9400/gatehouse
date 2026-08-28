# Contributing

1. Create a focused branch from `main`.
2. Add or update tests with behavior changes.
3. Run `ruff check app tests`, `pytest -q`, and the web typecheck/build locally.
4. Describe the threat-model impact and rollback plan in the pull request.

Keep API changes backwards-compatible within a minor release. Never commit credentials, database files, generated build output, or real access-request data.
