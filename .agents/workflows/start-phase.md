---
description: Plan and start a roadmap phase
---
1. Ask which phase (0-6). Read `docs/05-roadmap.md` and the modules for that phase in `docs/01-modules.md`.
2. Confirm the previous phase is committed and tests pass.
3. Write a short plan: scope, shared engines reused, assumptions, open questions. Wait for confirmation if architecture changes.
4. Build: models and migrations, services, API, tests, UI, seed data.
5. Run lint, tests, tenant-isolation suite. Regenerate OpenAPI schema and `docs/db/`.
6. Summarise: built, how to run/test, left out, what the next phase needs. Stop.
