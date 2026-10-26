# NICE HRIS — Multi-Tenant HRM SaaS (Bangladesh-First, 42 Modules, Light Glassmorphism)

A multi-tenant SaaS Human Resource Management web application built with **Django 5 + Django REST Framework + PostgreSQL + Celery/Redis** on the backend and a **React 18 + TypeScript + Vite + Tailwind CSS Light Glassmorphism PWA** on the frontend.

---

## Architecture Highlights
- **Single-Company & Multi-Company Tenants:** Driven by `tenant.multi_company_enabled` and company count. Single-company tenants never see company switchers or inter-company controls; multi-company conglomerate tenants get an instant Legal Entity Company Switcher, inter-company transfers, and consolidated group reporting.
- **Strict Tenant Isolation:** Every tenant-owned model inherits from `TenantModel` (`UUIDv7` primary keys, `tenant_id` composite indexes, auto-scoping `TenantManager`, and cross-tenant write prevention). Verified by automated cross-tenant isolation tests.
- **Effective Dating, Soft Delete & Append-Only Ledgers:** Salary structures, reporting lines, and career movements use `EffectiveDatedModel` (revisions add rows; never overwrite). HR records soft-delete only (`deleted_at`). Leave, Loan, Provident Fund, and Asset balances are strictly append-only ledgers (`LedgerModel`).
- **Bangladesh Localisation & Statutory Config:** `BDT` (`NUMERIC(14,2)`), `Asia/Dhaka`, Friday default weekly off, Lakh/Crore currency formatting (`৳ 1,25,000.00`), Taka-in-words on payslips & salary sheets, English + Bangla Unicode names, configurable **NIS Days** on the Monthly Attendance Summary feeding statutory deductions, and statutory disclaimers ("needs review by a local HR/tax professional").
- **Light Glassmorphism UI:** Translucent frosted glass panels over a pastel gradient with 3 blurred colour blobs, strong glass (`>= 0.80` alpha) for dense tables/forms/modals, and `@supports` / `prefers-reduced-transparency` / `prefers-reduced-motion` accessibility fallbacks.

---

## Quick Start

### Option 1: Docker Compose (One Command)
```bash
docker compose up --build
```
- **Frontend PWA:** `http://localhost:5173`
- **Backend API (`/api/v1/`):** `http://localhost:8000/api/v1/`
- **Interactive OpenAPI / Swagger Docs:** `http://localhost:8000/api/v1/docs/`

### Option 2: Local Native Development
1. **Start Backend & Seed Demo Data:**
   ```bash
   cd backend
   ./.venv/bin/python manage.py migrate
   ./.venv/bin/python manage.py seed_demo
   ./.venv/bin/python manage.py runserver 0.0.0.0:8000
   ```
2. **Start Frontend Dev Server:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## Running Lint, Tests & OpenAPI Generation
```bash
cd backend
./.venv/bin/ruff check .
./.venv/bin/pytest -v
./.venv/bin/python manage.py spectacular --file ../docs/openapi-schema.yaml
```

---

## Pre-Seeded Demo Accounts
| Persona | Email | Password | Mode |
|---|---|---|---|
| **Group HR Director (Multi-Company)** | `group.hr@jamunagroup.bd` | `Pass1234!` | Multi-Company Group (`Jamuna Conglomerate Group`, 3 Legal Entities, 36 Employees) |
| **HR Admin (Single-Company)** | `hr.admin@padmaapparel.bd` | `Pass1234!` | Single-Company (`Padma Apparel & Textiles Ltd.`, 1 Entity, 32 Employees) |
| **Line Manager (Module 33)** | `manager@padmaapparel.bd` | `Pass1234!` | Manager Self-Service (Salary & Medical Masked) |
| **Employee ESS Mobile (Module 32)** | `employee@padmaapparel.bd` | `Pass1234!` | Mobile-First Employee Self-Service PWA |
| **Platform Superadmin** | `platform.admin@nicehris.bd` | `Pass1234!` | Platform Admin (`/platform-admin` — Plans & 42-Module Matrix) |
