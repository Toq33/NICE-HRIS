# 08. User & Administrator Guide — NICE HRIS

## 1. Quick Start & Demo Personas
The application comes pre-seeded with **2 complete Bangladesh demo tenants** and **Platform Admin** so you can immediately explore every capability using the **Tenant / Role Switcher** in the top navigation bar:

1. **Multi-Company Conglomerate Tenant (`Jamuna Conglomerate Group`):**
   - **Group HR Director:** `group.hr@jamunagroup.bd` (`Pass1234!`) — Has access to all 3 legal entities (`Jamuna Tech Solutions Ltd.`, `Jamuna Agro & Foods Ltd.`, `Jamuna Logistics & Supply Chain Ltd.`), sees the **Legal Entity Company Switcher** in the top bar, and can view confidential salary and medical fields.
   - **Line Manager (Module 33):** `manager@jamunagroup.bd` (`Pass1234!`) — Manager Self-Service experience; salary & medical fields are automatically masked (`•••••••• (Restricted)`).
   - **Employee Self-Service (Module 32):** `employee@jamunagroup.bd` (`Pass1234!`) — Mobile-first PWA experience with Geofence Check-In/Out, Leave Request, and Payslip PDF view.
2. **Single-Company Tenant (`Padma Apparel & Textiles Ltd.`):**
   - **HR Admin:** `hr.admin@padmaapparel.bd` (`Pass1234!`) — Single-company mode (`multi_company_enabled = false`). Notice that the Company Switcher is automatically hidden so single-entity clients have a clean, uncluttered experience.
3. **Platform Superadmin (Above Tenants):**
   - **Platform Admin:** `platform.admin@nicehris.bd` (`Pass1234!`) — Manages subscription plans, provisions new tenants, and toggles which of the **42 HRM modules** are enabled per tenant at `/platform-admin`.

---

## 2. Key Workflows Across the 42 Modules

- **Design System (`/design-system`):** Click **Design System** in the top bar to inspect all Light Glassmorphism tokens, buttons, strong-glass tables, steppers, Kanban boards, org chart nodes, and accessibility fallbacks.
- **Organization & Employee Directory (Modules 2 & 3):** Browse the effective-dated interactive Org Chart, step through employees using the Record Pager (`1 / 32`), view English & Bangla Unicode names, and verify field-level encryption/masking on National ID and Bank Account numbers.
- **Attendance & NIS Insurable Days (Module 8):** Open the **Monthly Attendance Summary** tab to see the `Draft > Confirmed > Approved` stepper and the **`NIS Days`** column (computed from Present + Paid Leave + Paid Holidays) that feeds statutory payroll calculations.
- **Leave Balance Ledgers (Module 10):** View leave applications and switch to the **Append-Only Leave Balance Ledger** tab to see immutable `ACCRUAL` and `TAKEN` entries.
- **Monthly Payroll, Salary Sheet & Payslips (Modules 14, 15, 20, 22):**
  - Inspect the Monthly Salary Sheet with standard Bangladesh breakdown (Basic 50%, House Rent 25%, Medical 10%, Conveyance 10%, Entertainment 5%, PF 2.5%, NIS, AIT, Revenue Stamp 10 BDT).
  - View the **Total Net Payable in Words (Taka)** (e.g., *"Sixteen Lakh... Taka Only"*) and the 4-column **Prepared / Checked / Authorized / Approved** signature block.
  - Click **Lock Period** to permanently lock a payroll run (locked runs are immutable).
- **Approval Workflow Engine (Module 37):** Approve or reject pending requests across modules. Rejecting a request opens a modal enforcing a mandatory rejection reason.
- **Public REST API, OpenAPI Docs & Webhooks (Module 41):**
  - Interactive Swagger UI: `http://localhost:8000/api/v1/docs/`
  - ReDoc Reference: `http://localhost:8000/api/v1/redoc/`
  - Raw OpenAPI 3 Schema: `http://localhost:8000/api/v1/schema/`
