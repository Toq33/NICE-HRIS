# Data Dictionary — NICE HRIS (Phases 0–6 Complete)

All database conventions strictly follow `docs/02-architecture-and-database.md`:
- **Primary Keys:** UUID v7 (`core.uuid7.uuid7`) across all tables; API exposes UUIDs only.
- **Tenant Isolation:** Shared PostgreSQL schema; `tenant_id` (`NOT NULL`, `ON DELETE PROTECT`) on every tenant table, enforced by `TenantManager`.
- **Money & Rates:** All monetary columns use `NUMERIC(14,2)` + `currency` (`CHAR(3)`, default `'BDT'`). Rates and quantities use `NUMERIC(9,4)`. Never float.
- **Timestamps & Dates:** `timestamptz` stored in UTC (`Asia/Dhaka` display default); pure dates use `date`.
- **Soft Delete & Immutability:** `deleted_at` and `is_active` on all `TenantModel` tables; `LedgerModel` (`LeaveLedger`, `LoanLedger`, `ProvidentFundLedger`, `AssetMovementLedger`) and `AuditLog` / `ApprovalDecision` / `AttendancePunch` are strictly append-only.

## Table Summary by App

| App | Model / Table | Base Class | Key Columns & Rules |
|---|---|---|---|
| `platform_admin` | `Plan` | `models.Model` | `code`, `max_employees`, `max_companies`, `monthly_price_bdt NUMERIC(14,2)` |
| `platform_admin` | `Tenant` | `models.Model` | `slug`, `status`, `multi_company_enabled`, `employee_limit`, `weekly_off_days` |
| `platform_admin` | `EnabledModule` | `models.Model` | `tenant_id`, `module_number (1..42)`, `is_enabled` |
| `accounts` | `User` | `AbstractBaseUser`, `SensitiveFieldMixin` | Argon2 password, `tenant_id`, `default_company_id`, `experience_mode`, `can_view_salary`, `can_view_medical`, encrypted `totp_secret` |
| `accounts` | `Role`, `RolePermission`, `DataScope` | `TenantModel` | Separate `has_approval_authority`, `can_view_confidential_salary`, `scope_type` |
| `accounts` | `LoginHistory` | `models.Model` | Immutable login attempts with `ip_address`, `user_agent`, `succeeded` |
| `organization` | `Company` | `TenantModel` | Legal entity inside a tenant (`1` in single-company mode, `1..N` in multi-company mode) |
| `organization` | `Branch`, `Department`, `Section`, `Grade`, `Designation`, `CostCenter` | `CompanyOwnedModel` | Full organizational hierarchy below `Company`; geofence coords on `Branch` |
| `organization` | `Employee` | `CompanyOwnedModel`, `SensitiveFieldMixin` | `employee_code`, `full_name`, `full_name_bn`, `gross_salary_bdt NUMERIC(14,2)`, Fernet-encrypted `national_id_encrypted` & `bank_account_encrypted` |
| `organization` | `ReportingLine`, `EmergencyContact`, `FamilyMember`, `EmployeeQualification`, `EmployeeExperience`, `EmploymentRecord`, `EmployeeDocument` | `EffectiveDatedModel` / `TenantModel` | Effective-dated reporting lines & employment contracts (`effective_to IS NULL` partial index), family nominees, qualifications, prior experience, and verified documents (Mod 3) |
| `workflows` | `WorkflowDefinition`, `ApprovalRequest`, `ApprovalDecision` | `TenantModel` / `CompanyOwnedModel` | Generic approval engine (Mod 37) with append-only `ApprovalDecision` and mandatory rejection reason |
| `workflows` | `PolicyDocument`, `LetterTemplate`, `GeneratedLetter` | `CompanyOwnedModel` | Merge-field letter generator storing `merge_data` JSONB + `template_version` (Mod 35) |
| `workflows` | `Announcement`, `Notification`, `ReportDefinition` | `TenantModel` / `CompanyOwnedModel` | Notices, in-app notifications, and reusable report definitions (Mod 36 & 38) |
| `time_presence` | `WorkCalendar`, `Holiday`, `Shift`, `RosterBatch` | `CompanyOwnedModel` | Friday default off; overnight shifts crossing midnight (`crosses_midnight`) (Mod 9 & 11) |
| `time_presence` | `AttendancePunch`, `AttendanceDay`, `MonthlyAttendanceSummary` | `CompanyOwnedModel` | Immutable punches; daily computed status; monthly summary with **`nis_days`** column (Mod 8 & 20) |
| `time_presence` | `LeaveType`, `LeaveLedger`, `LeaveRequest` | `CompanyOwnedModel` / `LedgerModel` / `RequestModel` | Leave balance = sum of append-only `LeaveLedger` entries (Mod 10) |
| `time_presence` | `OvertimeRequest`, `FieldDutyMovement` | `RequestModel` | Configurable OT rate `NUMERIC(9,4)`; mobile GPS check-in (Mod 12 & 13) |
| `payroll` | `SalaryComponent`, `EmployeeSalaryStructure` | `CompanyOwnedModel` / `EffectiveDatedModel` | 50/25/10/10/5% BD structure; revisions create new effective-dated rows (Mod 14) |
| `payroll` | `StatutoryScheme`, `TaxSlab` | `EffectiveDatedModel` / `CompanyOwnedModel` | Configurable NIS social security & income tax slabs flagged for local professional review (Mod 20) |
| `payroll` | `PayrollPeriod`, `PayrollRun`, `Payslip`, `PaymentBatch` | `CompanyOwnedModel` | Frozen input snapshots, `nis_days`, `net_in_words` (Taka), immutable once `LOCKED` (Mod 15, 21, 22) |
| `payroll` | `BonusRun`, `ExpenseClaim`, `EmployeeLoan`, `LoanLedger`, `ProvidentFundLedger` | `CompanyOwnedModel` / `RequestModel` / `LedgerModel` | Append-only loan & PF ledgers (Mod 16, 17, 18, 19) |
| `talent_relations` | `ManpowerPlan`, `JobRequisition`, `JobApplicant`, `Interview`, `Offer`, `OnboardingChecklist`, `ProbationReview`, `ReviewCycle`, `Goal`, `PerformanceAppraisal`, `AppraisalSurvey`, `CareerMovement`, `TrainingProgram`, `TrainingNomination` | `CompanyOwnedModel` / `RequestModel` / `EffectiveDatedModel` | Full Phase 4 Talent Lifecycle including interview panels, offers, KPI goals, 360° surveys, and training nominations (Mod 4–7, 23–25) |
| `talent_relations` | `GrievanceCase`, `DisciplinaryCase`, `CompanyAsset`, `AssetMovementLedger`, `HealthSafetyRecord`, `ResignationRequest`, `FinalSettlement`, `ClearanceItem`, `HelpdeskTicket` | `CompanyOwnedModel` / `LedgerModel` / `SensitiveFieldMixin` | Full Phase 5 Relations, Assets, Encrypted Medical Records, Separation, Department Clearance & Settlement (Mod 26–31, 34) |
| `system_settings` | `TenantSetting`, `NumberSequence`, `Attachment`, `AuditLog`, `IdempotencyRecord` | `TenantModel` / `CompanyOwnedModel` | Shared 10MB virus-scanned `Attachment` table with signed URL audit logging, immutable `AuditLog`, per-company sequence generator, idempotent request cache (Mod 40 & 42) |
| `integrations` | `APIKey`, `OAuth2Client`, `WebhookEndpoint`, `WebhookDelivery`, `IntegrationConnectorConfig`, `IntegrationRunLog` | `TenantModel` | SHA-256 hashed API keys, OAuth2 `client_credentials` clients, SSRF-safe HTTPS webhooks with HMAC-SHA256 signing & replay, `csv_json` adapter (Mod 41) |
