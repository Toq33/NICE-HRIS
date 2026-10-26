# 05. Roadmap and Phase Prompts

Build one phase at a time. Each phase ends with: working demo data, passing tests, updated OpenAPI docs, ER diagram + data dictionary in `docs/db/`, and a short user guide.

| Phase | Goal | Modules |
|---|---|---|
| 0. Foundation | Repo, Docker, CI, auth, tenancy, design system, app shell, Platform Admin, API foundation, API key model | infrastructure, 39 (basic), 42 (basic), 41 (API foundation) |
| 1. Core HR | Organization, employee records, permissions, workflow engine, audit, settings, policies, basic notifications | 2, 3, 39, 37, 40, 42, 35, 36 (basic) |
| 2. Time and Presence | Calendars, attendance, shifts, leave, overtime, field/remote work, self-service shells, first dashboard | 8, 9, 10, 11, 12, 13, 32, 33, 1 (v1) |
| 3. Payroll and Compensation | Salary structure through payslips and disbursement | 14, 15, 16, 17, 18, 19, 20, 21, 22 |
| 4. Talent Lifecycle | Hiring to growth | 4, 5, 6, 7, 23, 24, 25 |
| 5. Relations, Assets and Exit | Cases, assets, welfare, helpdesk, separation, settlement | 26, 27, 28, 29, 30, 31, 34 |
| 6. Insight and Integration | Full dashboard, analytics, public API/webhooks/connectors, hardening | 1 (complete), 38, 41, 36 and 40 (final) |

## Phase 0 kickoff prompt
You are a senior full-stack engineer. Read `AGENTS.md` and all files in `docs/`. We are starting **Phase 0 (Foundation)** only.

Deliver:
1. Monorepo with `backend/` (Django 5 + DRF + PostgreSQL + Celery/Redis) and `frontend/` (React + TS + Vite + Tailwind); Docker Compose starts everything with one command.
2. Multi-tenant core: tenant-scoped base model and manager, plus a test proving cross-tenant isolation.
3. Authentication, basic users/roles/permissions, and a Platform Admin area to create tenants and enable modules.
4. Light glassmorphism design system and component library (`docs/03`), with a hidden `/design-system` page.
5. App shell with role-aware navigation, empty placeholders for all 42 modules, and seeded demo tenants.
6. Database baseline (`docs/02`): base models, naming rules, migrations, seed data. API foundation (`docs/04`): versioned REST, OpenAPI docs, API key model.
7. CI, linting, README with setup steps.

Before coding, give a short implementation plan and list assumptions or questions. After finishing, summarise what was built, how to run and test it, and what Phase 1 needs. **Do not start Phase 1 until I confirm.**

## Prompt template for Phases 1-6
"Start **Phase N (<name>)**. Modules: <list from docs/01-modules.md>. Reuse the shared engines (docs/02), follow the database standards (docs/02), API standards (docs/04) and glass design system (docs/03). Give a plan first, then build, then summarise. Do not start the next phase until I confirm."
