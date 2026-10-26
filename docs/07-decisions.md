# 07. Decisions, Assumptions and Open Questions

## Confirmed by owner
- Multi-tenant SaaS; Bangladesh-first; 42 HR modules; light glassmorphism; database + API integration readiness.
- CRM and Transport are NOT part of this product (dropped entirely).
- Mobile = responsive web app (installable PWA); native app possibly later, reusing the same API.
- Tenants may be single-company or multi-company; both supported by the same code (see `02`).
- Stack as in `AGENTS.md` section 3.
- **NIS days** = insurable days in a pay period for National Insurance Scheme / social security calculations; stored on the monthly attendance summary and used by payroll (see `02`).

## Assumptions (change if wrong)
- A1. Only generic CSV/JSON connectors are built until the owner specifies named integrations.
- A2. Bangla supported in data and letters from the start; full Bangla UI translation later.
- A3. "Single company" means a tenant with one company inside the shared SaaS deployment, not a separate self-hosted install. If dedicated/self-hosted installs are needed, tell the agent.

## Open questions
- Q1. NIS rules: exactly which day types count as insurable (present, paid leave, paid holidays, weekends?), contribution rates, wage ceiling, and who is enrolled? The agent uses the default rule in `02` until told otherwise.
- Q2. First external systems to integrate (accounting/ERP, bank, biometric brand).

## Log (agent appends here)
| Date | Decision / assumption | Reason |
|---|---|---|
| 2026-10-26 | Implemented RFC 9562 UUIDv7 (`core.uuid7.uuid7`) as the universal primary key across all models. | Satisfies `AGENTS.md` Section 4 ("IDs: one PK type everywhere (UUID v7 preferred). API exposes UUIDs only.") with chronological index locality in PostgreSQL. |
| 2026-10-26 | Implemented `TenantManager` returning `.none()` when no tenant context is active, plus cross-tenant write protection in `TenantModel.save()`. | Guarantees zero cross-tenant data leakage by default and passes the mandatory cross-tenant isolation test suite. |
| 2026-10-26 | Shipped Bangladesh statutory defaults (Basic 50%, HRA 25%, Medical 10%, Conveyance 10%, Entertainment 5%, PF 2.5%, Stamp 10 BDT, NIS Days = Present + Paid Leave + Paid Holidays) as editable tenant/company config with visible "needs review by a local HR/tax professional" banners. | Follows `AGENTS.md` Section 2.7 and `docs/02-architecture-and-database.md`. |
| 2026-10-26 | Built full Phases 0–6 across all 42 HRM modules with 2 seeded demo tenants (`Padma Apparel & Textiles Ltd.` single-company with 32 employees and `Jamuna Conglomerate Group` multi-company with 3 legal entities and 36 employees). | Requested by user to complete all phases with realistic Bangladesh English + Bangla Unicode demo data. |
| 2026-10-26 | Resolved early JWT and `X-API-Key` tenant context inside `TenantResolutionMiddleware` prior to `IdempotencyMiddleware`, added `openpyxl` Excel report export (`export-xlsx`) and `ReportLab` PDF payslip download (`pdf`), and added PWA service worker (`sw.js`). | Ensures `Idempotency-Key` replay/conflict detection works across stateless JWT & API-key requests, and completes all `AGENTS.md` Section 3 & 8 requirements. |
