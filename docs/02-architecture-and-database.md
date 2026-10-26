# 02. Architecture and Database

## Tenancy
- Tenant = subscribing client. Company = legal entity inside a tenant. A tenant has 1 company (single-company mode) or many (multi-company mode); same schema and code for both.
- Company-owned tables carry `tenant_id` AND `company_id`; user data scope can be limited to specific companies. Unique numbers (employee ID, payslip no) are unique per company unless the tenant chooses a shared sequence.
- Multi-company features: inter-company transfer (closes employment in one company, opens in another, keeps one person record), consolidated group reports, group-level policies with company overrides. Below company: Branch > Department > Section > Designation / Grade / Cost Center.
- Shared PostgreSQL schema; `tenant_id` on every tenant-owned table.
- Custom base model and manager scope every query to the current tenant (from authenticated user or subdomain, e.g. `acme.hrm.example.com`).
- Automated test: tenant A can never read tenant B via any API endpoint. Runs in CI on every commit.
- Optional later: PostgreSQL Row-Level Security as second defence.
- Platform layer: Plan, Subscription, EnabledModule, tenant status.

## Core patterns every module reuses
| Pattern | Requirement |
|---|---|
| Effective dating | `effective_from` / `effective_to` on salary, designation, department, grade, reporting line, employment record |
| Soft delete | `is_active` / `deleted_at`; never hard-delete HR data |
| Audit | created/updated by+at automatic; field-level history on sensitive fields |
| Attachments | one generic attachment system |
| Numbering | configurable per-tenant sequences (employee ID, requisition no, ticket no, loan no) |
| Notifications | in-app + email now, SMS later; template-based; per-user preferences |
| API | versioned `/api/v1/`, consistent pagination/filter/error format |
| Approvals | all via Workflow Engine |

## Cross-cutting engines (build once, Phases 0-1)
1. **Roles/Permissions/Data scope.** Permission = module + action (view, create, edit, delete, approve, export). Roles are tenant-defined. Data scope: company, branch, department, or "own and direct reports". Field-level protection for salary and medical data. Approval authority is configured separately.
2. **Approval Workflow Engine.** Chains per module and request type; sequential and parallel steps; conditions (amount, department, company); delegation during leave; escalation after time limit; mandatory rejection reason; full history. Modules raise a generic ApprovalRequest and receive the result via callback. ApprovalRequest points to subject by `subject_type` + `subject_id`; steps and decisions are append-only.
3. **Audit and Security.** Immutable log (who, what, when, old, new, IP). Login history, optional TOTP 2FA, session timeout and device list, document access log.
4. **Notifications.** Event-driven from any module.
5. **Document and Letter generation.** Templates with merge fields, PDF with letterhead, policy versioning and acknowledgment.
6. **Reporting framework.** Reusable report definition (filters, columns, grouping); screen, Excel, PDF, scheduled email.

## Database rules
- 3NF for transactional data; denormalise only for marked reporting tables.
- Money `NUMERIC(14,2)` + currency code. Rates `NUMERIC(9,4)`. Never float.
- `timestamptz` UTC; dates as `date`.
- One PK type (UUID v7 or bigint identity); API exposes UUIDs.
- Unique constraints always include `tenant_id`. Every tenant table has a composite index starting with `tenant_id`.
- Key indexes: attendance `(tenant_id, employee_id, work_date)`; leave ledger `(tenant_id, employee_id, leave_type_id, posted_on)`; payroll lines `(payroll_run_id, employee_id)`; audit `(tenant_id, entity, entity_id, created_at)`.
- Exclusion constraints (`btree_gist`) on effective-dated tables: no two current salaries or reporting lines per employee.
- Check constraints: end after start, non-negative amounts, allowed status values.
- Partial indexes for current rows (`effective_to IS NULL`) and active rows (`deleted_at IS NULL`).
- Plan monthly partitioning for raw punches, audit log, notifications, import/export logs.
- JSONB only for genuinely flexible data (integration payloads, custom fields, report definitions, letter merge data).
- Every FK has explicit `on_delete` (usually PROTECT) and an index.

## Abstract base models
| Base | Columns / behaviour | Used by |
|---|---|---|
| TenantModel | id, tenant_id, created_at, updated_at, created_by, updated_by, deleted_at | all tenant tables |
| EffectiveDatedModel | effective_from, effective_to, change_reason, approved_by | salary, designation, department, grade, reporting line, employment |
| LedgerModel | append-only; amount/quantity, reason, source type+id; no update/delete | leave, loan, fund, asset |
| RequestModel | status, submitted_at, decided_at, approval_request ref | leave, overtime, claims, transfers |
| SensitiveFieldMixin | encrypted at rest, masked in lists, access logged | bank account, national ID, medical, salary |

## Entity groups (refine, but keep boundaries)
- Platform: Tenant, Plan, EnabledModule
- Identity: User, Role, Permission, UserRole, DataScope, LoginHistory
- Organization: Company, Branch, Department, Section, Designation, Grade, CostCenter, ReportingLine
- Employee: Employee, EmploymentRecord, Contact, EmergencyContact, FamilyMember, Qualification, Experience, BankAccount, Document
- Time: Shift, Roster, AttendanceLog (raw), AttendanceDay (computed), AttendanceSummary (monthly, Draft>Confirmed>Approved), LeaveType, LeavePolicy, LeaveLedger, LeaveRequest, Holiday, Calendar, OvertimeRequest, FieldDuty
- Payroll: SalaryGrade, SalaryComponent, EmployeeSalary, PayrollPeriod, PayrollRun, PayrollLine, Adjustment, Loan, LoanInstallment, FundAccount, TaxSlab, Payment, PaymentBatch, Payslip
- Talent: Requisition, Vacancy, Applicant, Interview, Offer, OnboardingChecklist, ProbationReview, Goal, ReviewCycle, Appraisal, Survey, TrainingProgram, Nomination
- Cases and exit: Grievance, DisciplinaryCase, Asset, AssetAssignment, SafetyIncident, Resignation, ClearanceItem, FinalSettlement, Ticket
- Shared: WorkflowDefinition, ApprovalRequest, ApprovalStep, Attachment, Notification, AuditLog, Policy, LetterTemplate, NumberSequence, ReportDefinition, ImportExportLog

## Tables needing extra care
- **Leave:** store ledger entries; balance = sum (cached, re-checkable).
- **Attendance:** raw punches immutable; compute daily from punches + shift + approved corrections; recompute is safe and repeatable.
- **Salary:** revision creates a new row; never update the old one.
- **Payroll:** run freezes inputs; each PayrollLine stores amounts + snapshot of salary, attendance, leave inputs; corrections go to later periods.
- **Documents/letters:** metadata in DB, files in object storage; keep merge data and template version.
- **Audit log:** append-only; app DB role has no UPDATE/DELETE on it.

## Environments and operations
- Every schema change is a reviewed Django migration; never edit an applied one; risky changes in two steps (nullable + backfill, then enforce).
- Local (Docker), CI (fresh DB per run), staging (seed), production.
- Seed/master data (leave types, salary components, tax slab templates, holiday templates, letter templates) are versioned fixtures loaded by a tenant provisioning command.
- App DB user is not superuser; migrations use a separate privileged role.
- Generate ER diagram per module group and a data dictionary into `docs/db/` at the end of each phase.
- Backups: daily full + WAL archiving; restore drill quarterly. Encryption keys kept outside the DB. Per-tenant retention settings; scripted tenant export and deletion procedure. Read replica later for reports.

## Statutory social security (NIS days)
Owner-confirmed: **NIS days** = the count of eligible/insurable days an employee completes in a pay period, used for National Insurance Scheme (social security) calculations.
- Model it generically as a configurable **StatutoryScheme** (name, e.g. NIS; employee rate, employer rate, wage ceiling/floor, contribution basis, effective-dated) plus per-employee enrolment (member number, enrolment date, exempt flag).
- `AttendanceSummary` stores `nis_days` per employee per period, computed by a configurable rule (default: days present + paid leave + paid holidays; unpaid leave and absence excluded). The rule is tenant/company configuration, shown and editable on the summary before approval, with manual override logged in the audit trail.
- Payroll reads `nis_days` and the scheme to compute employee and employer contributions; results appear as payslip lines and in a statutory contribution report/export (module 20).
- Do not hard-code any country's rates or ceilings; ship an empty or example scheme flagged "needs review by a local payroll/legal professional".

## Bangladesh localisation (all configuration with editable defaults)
Calendar (Friday off, Saturday configurable, Eid holiday blocks, optional religious and branch holidays); leave types (casual, sick, earned/annual, maternity, paternity, unpaid); payroll components (basic, house rent, medical, conveyance, mobile, entertainment, festival bonus, performance bonus, overtime, provident fund, gratuity, advance and loan recovery, stamp deduction, AIT/tax); tax slabs per income year with monthly withholding and year-end adjustment; payment outputs (bank transfer CSV per bank, cash sheets, bKash/Nagad-style bulk lists as export templates); BDT with lakh grouping option and amount-in-words (Taka); Bangla Unicode for names, addresses, letters; ZKTeco-style device exports by file import first, device sync later.
