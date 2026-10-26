---
description: Add an integration connector
---
1. Only proceed if the owner has specified the connector. Otherwise ask.
2. Read `docs/04-api-and-integrations.md`.
3. Create `backend/integrations/<name>/` with test_connection, pull, push, map_fields as Celery tasks.
4. Store credentials encrypted; add catalog entry, settings screen, schedule, run log screen, configurable field mapping.
5. Add webhooks/events if relevant; audit-log all actions; never log secrets.
6. Tests with mocked external service; document in OpenAPI and user guide.
