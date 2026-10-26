# 04. API and External Integrations

Every capability is available through a documented REST API so other software (accounting/ERP, biometric devices, banks, recruitment portals, client tools) can connect. The web app uses this same API.

## API design
- REST over HTTPS, JSON, versioned `/api/v1/`. Breaking changes only in a new version with a published deprecation period.
- OpenAPI 3 via drf-spectacular, interactive docs page, downloadable schema for SDK generation.
- Cursor pagination, filter and sort parameters, ISO 8601 dates, one error format with machine-readable codes, `Idempotency-Key` on create and payment requests.
- Bulk endpoints for imports (employees, attendance punches, salary data) with validation-only dry-run and per-row error report.
- Same permissions and data scope as the UI. Salary and medical fields need explicit permission.
- Rate limits per API key and per tenant; 429 with retry hint.
- Only enabled modules expose endpoints.

## Authentication
| Method | Use | Rules |
|---|---|---|
| Session/JWT cookie | Web users | HTTP-only, CSRF protected |
| API keys | Server-to-server | Created by tenant admin, shown once, stored hashed, scoped by module and read/write, optional IP allow-list, expiry, revocable, last-used shown, rotation with overlap |
| OAuth 2.0 client credentials | Partner integrations | Per-tenant consent, short-lived scoped tokens (django-oauth-toolkit) |

Each key/client acts as an integration user with its own role. Every call is audit-logged with the key id.

## Webhooks (outbound)
- Tenant admins register HTTPS endpoints and pick events: `employee.created`, `employee.separated`, `leave.approved`, `attendance.imported`, `payroll.run.approved`, `payslip.published`, `payment.batch.failed`, `requisition.approved` (extend as modules land).
- Signed HMAC-SHA256 with timestamp header. Delivered by Celery with retries, exponential backoff, dead-letter list, manual replay.
- Delivery log screen per endpoint (status, code, attempts, payload). Auto-disable after repeated failures and notify admin.
- Payloads carry ids and key fields only; salary and bank details only if the key has that scope.
- Block private/internal addresses (SSRF). HTTPS only.

## Integration framework (module 41)
- Catalog screen: each connector has settings, encrypted credentials, test-connection, enable/disable, schedule, run log with success/failure counts.
- Backend adapter pattern: `backend/integrations/<name>/` implements `test_connection`, `pull`, `push`, `map_fields`; runs as Celery tasks. Field mapping configurable per tenant.
- CSV/Excel import and export templates always available for systems without an API.
- Never log secrets, keys, or full sensitive payloads. Audit-log every action (create key, change scope, enable connector, replay webhook).

## Planned connectors (details to be specified later by the owner)
| Connector | Direction | Phase |
|---|---|---|
| Public REST API + webhooks | Both | foundation 0, complete 6 |
| Email (SMTP/API) | Out | 1 |
| Biometric devices (ZKTeco-style file import, then device/middleware sync; the current product also uses Hikvision-class devices) | In | 2 file, 6 sync |
| Bank payment files, MFS bulk payout | Out | 3 |
| Recruitment portals / careers page | Both | 4 |
| Accounting/ERP (payroll journal export, generic first) | Out | 6 |
| SMS gateway | Out | 6 |
| SSO (Google, Microsoft, OIDC, SAML) | In | 6 |

**Rule for the agent:** build the framework and a generic CSV/JSON connector now. Do not build a named third-party connector until the owner specifies it.
