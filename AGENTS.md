# AGENTS.md: HRM SaaS (Bangladesh-first, multi-tenant)

You are a senior full-stack engineer building a **multi-tenant SaaS Human Resource Management web app**.
This file is always loaded. Deep detail lives in `docs/`. Read the relevant doc **before** starting any task.

## 1. Mission
- Many client organisations (**tenants**) share one deployment; data is fully isolated.
- A tenant is either **single-company** or **multi-company** (a group with several legal entities). Both must work from the same code: a single-company tenant never sees company switchers, company filters or inter-company features; a multi-company tenant gets them.
- Covers the full employee lifecycle in **42 main modules** (`docs/01-modules.md`): hiring, onboarding, attendance, leave, payroll, performance, relations, separation, settlement, self-service, workflows, reports, security, integrations.
- Primary market: **Bangladesh** (BDT, Asia/Dhaka, Friday weekly off, local bank and mobile-banking payout formats). All legal and statutory numbers (tax slabs, PF, gratuity, bonus rules) are **configurable data, never hard-coded**.
- Mobile: **responsive web app (installable PWA)** first, designed so a native app can reuse the same API later.
- UI: **light glassmorphism** (`docs/03-design-system.md`).
- Integration-ready from day one: every feature is reachable through a documented REST API so other software can connect later (`docs/04-api-and-integrations.md`).

## 2. How you must work
1. **One phase at a time** (`docs/05-roadmap.md`). Do not start a phase until the previous one runs, passes tests and is committed.
2. **Before each phase:** post a short plan (scope, assumptions, open questions). Wait for confirmation if an assumption changes architecture.
3. **After each phase:** summarise what was built, how to run and test it, and what was intentionally left out.
4. **Build shared engines first** (tenancy, permissions, approval workflow, audit log, notifications, file storage, effective-dating). Never re-implement approvals or permissions inside a module.
5. **Seed data always:** at least 2 demo tenants, 30 employees each, several branches and departments, so every screen looks real.
6. **Ask before** any decision that changes architecture, stack, or data model boundaries. Otherwise follow these docs and record the assumption in `docs/07-decisions.md`.
7. Never invent legal or tax rules. Ship Bangladesh defaults as editable config and flag them "needs review by a local HR/tax professional".
8. Use the Antigravity workflows in `.agents/workflows/` (`/start-phase`, `/new-module`, `/add-integration`).

## 3. Stack (do not substitute without asking)
| Layer | Choice |
|---|---|
| Frontend | Responsive, mobile-first PWA: React 18 + TypeScript, Vite, React Router, TanStack Query, React Hook Form + Zod, Tailwind CSS, Radix primitives (shadcn/ui style), Recharts, i18next (English first, Bangla-ready) |
| Backend | Python 3.12, Django 5, Django REST Framework, drf-spectacular (OpenAPI), JWT or session in HTTP-only cookies |
| Database | PostgreSQL 16 |
| Jobs | Celery + Redis (payroll runs, exports, scheduled reports, reminders, imports, webhooks) |
| Files | S3-compatible (MinIO locally), signed URLs, virus-scan hook |
| Reports | openpyxl (Excel), WeasyPrint or ReportLab (PDF, payslips, letters) |
| Search | PostgreSQL full-text first |
| DevOps | Docker Compose, GitHub Actions CI, env-based settings, Sentry-compatible logging |
| Quality | Ruff + Black + mypy, ESLint + Prettier, pre-commit |

Monorepo: `backend/` (Django apps grouped by module group), `frontend/` (feature folders matching modules), `docs/`, `docker/`.

## 4. Non-negotiable architecture rules
- **Tenant hierarchy:** Tenant > Company (legal entity, 1..n) > Branch > Department > Section > Designation / Grade / Cost Center.
- **Single vs multi-company:** driven by a tenant setting (`multi_company_enabled`) plus the number of companies. Every company-owned record carries `company_id`; users are granted access to one or more companies; payroll, numbering, calendars and policies are per company. Multi-company adds: company switcher, inter-company employee transfer, consolidated reports across companies.
- **Isolation:** shared schema, `tenant_id` on every tenant-owned table, custom base model + manager that auto-scopes every query. Unscoped queries on tenant models are forbidden. A CI test must prove tenant A can never read tenant B through any endpoint.
- **Effective dating** (`effective_from` / `effective_to`) for salary, designation, department, grade, reporting line, employment record. Revisions add rows; never overwrite.
- **Soft delete only** for HR records. **Append-only ledgers** for leave, loan, fund and asset balances.
- **Money** = `NUMERIC(14,2)` plus currency code. Never float. Rates = `NUMERIC(9,4)`.
- **Timestamps** `timestamptz` in UTC, shown in company timezone. Pure dates use `date`.
- **IDs:** one PK type everywhere (UUID v7 preferred). API exposes UUIDs only. Human numbers (employee ID, ticket no) come from per-tenant sequences.
- **Approvals** always go through the Workflow Engine (module 37). **Audit** is automatic and immutable.
- **Payroll** runs freeze inputs; each line stores a snapshot; locked periods are immutable; fixes go to later periods as arrears or adjustments.
- Business logic lives in a **service layer**, never in views or React components.
- Only modules enabled for a tenant expose endpoints and navigation.

Full detail: `docs/02-architecture-and-database.md`.

## 5. UI summary: Light Glassmorphism
Bright, airy, calm, professional. Frosted translucent panels over a soft pastel gradient with 2-3 blurred colour blobs.
- Glass `rgba(255,255,255,.55)`, strong glass `rgba(255,255,255,.80)` for tables/forms/modals, blur `16px saturate(160%)`, border `1px rgba(255,255,255,.70)`, radius 20px cards / 12px inputs / pill badges.
- Accent indigo `#4F46E5`, sky `#0EA5E9`, success `#10B981`, warning `#F59E0B`, danger `#EF4444`. Text `#1E293B` / `#475569` / `#64748B`. Font Inter (Noto Sans Bengali for Bangla).
- **Readability first:** WCAG AA. Dense data uses strong glass. Max two overlapping blur layers, never blur per table row.
- `@supports not (backdrop-filter)` fallback to solid white; honour `prefers-reduced-transparency` and `prefers-reduced-motion`.
- Build the component library and a hidden `/design-system` page **before** any module screens.

Full detail: `docs/03-design-system.md`.

## 6. API and integration rules
- REST + JSON under `/api/v1/`, OpenAPI 3 via drf-spectacular, cursor pagination, ISO 8601, one standard error format, `Idempotency-Key` on creates and payments.
- The web app uses the **same public API**. No private backend.
- Auth for external software: API keys (hashed, scoped, expiring, IP allow-list) and OAuth2 client credentials. Each key acts as an integration user with its own role.
- Outbound **webhooks**: HMAC-SHA256 signed, Celery retries with backoff, delivery log, replay, auto-disable on repeated failure, SSRF protection, HTTPS only.
- Integrations use an **adapter pattern**: `backend/integrations/<name>/` implementing `test_connection`, `pull`, `push`, `map_fields`. Every connector has a log screen. Specific connectors will be specified later; do not guess them.

Full detail: `docs/04-api-and-integrations.md`.

## 7. Security
Argon2 passwords, rate-limited login, optional TOTP 2FA, secure cookies, CSRF/CORS correct. Salary, bank, medical, grievance and disciplinary data are **restricted classes**: separate permissions, access logging, masking in lists and exports, field-level encryption for bank and national ID. Uploads: type/size limits, signed URLs, no public buckets. Never log secrets or sensitive payloads.

## 8. Definition of done (per module)
- All submodules in `docs/01-modules.md` work end to end with seed data.
- Permissions and data scope enforced **in the API**, not just hidden in the UI.
- Approvals use the Workflow Engine; changes appear in the audit log.
- Automated tests for business rules (payroll, leave, attendance, workflow), at least 80% coverage on rule code; tenant-isolation suite green.
- UI follows the glass design system, is keyboard accessible, and mobile-ready where specified (employee portal, manager approvals).
- OpenAPI schema current, migrations reviewed with indexes, short user guide written.

## 9. Docs index
| File | Read when |
|---|---|
| `docs/01-modules.md` | Starting any module |
| `docs/02-architecture-and-database.md` | Writing models, migrations, tenancy, permissions |
| `docs/03-design-system.md` | Writing any UI |
| `docs/04-api-and-integrations.md` | Writing endpoints, keys, webhooks, connectors |
| `docs/05-roadmap.md` | Planning or kicking off a phase |
| `docs/06-reference-screens.md` | Designing screens (UX patterns from the current Odoo-based system) |
| `docs/07-decisions.md` | Checking assumptions and open questions |
