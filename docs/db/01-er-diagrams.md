# Database Entity-Relationship (ER) Diagrams by Module Group

All tenant-owned tables inherit from `TenantModel` (`id` UUIDv7, `tenant_id` FK with composite index, `is_active`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`).

---

## 1. Platform & Identity Group (Phase 0 & Module 39, 40)

```mermaid
erDiagram
    PLAN ||--o{ TENANT : "subscribes"
    TENANT ||--o{ ENABLED_MODULE : "toggles 1..42"
    TENANT ||--o{ USER : "owns"
    TENANT ||--o{ ROLE : "defines"
    ROLE ||--o{ ROLE_PERMISSION : "grants"
    USER ||--o{ DATA_SCOPE : "scoped by"
    ROLE ||--o{ DATA_SCOPE : "assigned in"
    USER ||--o{ LOGIN_HISTORY : "audits"

    PLAN {
        uuid id PK
        string code UK
        string name
        int max_employees
        int max_companies
        numeric monthly_price_bdt
    }
    TENANT {
        uuid id PK
        string slug UK
        string name
        string name_bn
        string status
        boolean multi_company_enabled
        int employee_limit
        string default_currency
        string default_timezone
    }
    ENABLED_MODULE {
        uuid id PK
        uuid tenant_id FK
        int module_number
        string module_slug
        boolean is_enabled
    }
    USER {
        uuid id PK
        uuid tenant_id FK
        string email UK
        string full_name
        string experience_mode
        boolean is_platform_admin
        boolean can_view_salary
        boolean can_view_medical
    }
```

---

## 2. Organization & Employee Group (Phase 1: Modules 2 & 3)

```mermaid
erDiagram
    TENANT ||--o{ COMPANY : "1 (single) or 1..N (multi)"
    COMPANY ||--o{ BRANCH : "has"
    COMPANY ||--o{ DEPARTMENT : "has"
    DEPARTMENT ||--o{ SECTION : "contains"
    COMPANY ||--o{ GRADE : "defines"
    GRADE ||--o{ DESIGNATION : "ranks"
    COMPANY ||--o{ COST_CENTER : "tracks"
    COMPANY ||--o{ EMPLOYEE : "employs"
    EMPLOYEE ||--o{ REPORTING_LINE : "effective-dated"
    EMPLOYEE ||--o{ EMERGENCY_CONTACT : "contacts"
    EMPLOYEE ||--o{ FAMILY_MEMBER : "nominees & dependents"
    EMPLOYEE ||--o{ EMPLOYEE_QUALIFICATION : "degrees"
    EMPLOYEE ||--o{ EMPLOYEE_EXPERIENCE : "prior history"
    EMPLOYEE ||--o{ EMPLOYMENT_RECORD : "contracts & transfers"
    EMPLOYEE ||--o{ EMPLOYEE_DOCUMENT : "verified files"

    COMPANY {
        uuid id PK
        uuid tenant_id FK
        string code
        string name
        string name_bn
        string currency
        string timezone
        boolean is_primary
    }
    EMPLOYEE {
        uuid id PK
        uuid tenant_id FK
        uuid company_id FK
        string employee_code
        string full_name
        string full_name_bn
        date joining_date
        string employment_status
        numeric gross_salary_bdt
        string national_id_encrypted
        string bank_account_encrypted
    }
    REPORTING_LINE {
        uuid id PK
        uuid tenant_id FK
        uuid employee_id FK
        uuid manager_id FK
        date effective_from
        date effective_to
    }
```

---

## 3. Time & Presence Group (Phase 2: Modules 8, 9, 10, 11, 12, 13)

```mermaid
erDiagram
    COMPANY ||--o{ WORK_CALENDAR : "configures"
    WORK_CALENDAR ||--o{ HOLIDAY : "includes"
    COMPANY ||--o{ SHIFT : "defines"
    SHIFT ||--o{ ROSTER_BATCH : "schedules"
    EMPLOYEE ||--o{ ATTENDANCE_PUNCH : "immutable raw"
    EMPLOYEE ||--o{ ATTENDANCE_DAY : "computed daily"
    EMPLOYEE ||--o{ MONTHLY_ATTENDANCE_SUMMARY : "includes nis_days"
    EMPLOYEE ||--o{ LEAVE_LEDGER : "append-only"
    EMPLOYEE ||--o{ LEAVE_REQUEST : "applies"
    EMPLOYEE ||--o{ OVERTIME_REQUEST : "requests"
    EMPLOYEE ||--o{ FIELD_DUTY_MOVEMENT : "logs GPS"
```

---

## 4. Payroll & Compensation Group (Phase 3: Modules 14–22)

```mermaid
erDiagram
    COMPANY ||--o{ SALARY_COMPONENT : "formulas"
    EMPLOYEE ||--o{ EMPLOYEE_SALARY_STRUCTURE : "effective-dated"
    COMPANY ||--o{ STATUTORY_SCHEME : "NIS config"
    COMPANY ||--o{ TAX_SLAB : "income year"
    COMPANY ||--o{ PAYROLL_PERIOD : "monthly lockable"
    PAYROLL_PERIOD ||--o{ PAYROLL_RUN : "calculates"
    PAYROLL_RUN ||--o{ PAYSLIP : "freezes snapshot"
    PAYROLL_RUN ||--o{ PAYMENT_BATCH : "BEFTN / bKash / Nagad"
    EMPLOYEE ||--o{ EMPLOYEE_LOAN : "borrows"
    EMPLOYEE_LOAN ||--o{ LOAN_LEDGER : "append-only"
    EMPLOYEE ||--o{ PROVIDENT_FUND_LEDGER : "append-only"
```

---

## 5. Talent Lifecycle, Relations, Assets & Exit Group (Phases 4 & 5: Modules 4–7, 23–31, 34)

```mermaid
erDiagram
    DEPARTMENT ||--o{ MANPOWER_PLAN : "headcount budget"
    DEPARTMENT ||--o{ JOB_REQUISITION : "opens"
    JOB_REQUISITION ||--o{ JOB_APPLICANT : "kanban stage"
    JOB_APPLICANT ||--o{ INTERVIEW : "panel rounds"
    JOB_APPLICANT ||--o{ OFFER : "offers"
    EMPLOYEE ||--o{ ONBOARDING_CHECKLIST : "completes"
    EMPLOYEE ||--o{ PROBATION_REVIEW : "evaluates"
    COMPANY ||--o{ REVIEW_CYCLE : "appraisal cycles"
    EMPLOYEE ||--o{ GOAL : "KPIs & weights"
    EMPLOYEE ||--o{ PERFORMANCE_APPRAISAL : "360 review"
    PERFORMANCE_APPRAISAL ||--o{ APPRAISAL_SURVEY : "peer & manager 360"
    EMPLOYEE ||--o{ CAREER_MOVEMENT : "effective-dated"
    TRAINING_PROGRAM ||--o{ TRAINING_NOMINATION : "enrolls & certifies"
    EMPLOYEE ||--o{ GRIEVANCE_CASE : "confidential"
    EMPLOYEE ||--o{ DISCIPLINARY_CASE : "restricted"
    COMPANY_ASSET ||--o{ ASSET_MOVEMENT_LEDGER : "append-only"
    EMPLOYEE ||--o{ HEALTH_SAFETY_RECORD : "encrypted medical"
    EMPLOYEE ||--o{ RESIGNATION_REQUEST : "exits"
    RESIGNATION_REQUEST ||--o| FINAL_SETTLEMENT : "clears & settles"
    FINAL_SETTLEMENT ||--o{ CLEARANCE_ITEM : "department sign-off"
```

---

## 6. Governance, Workflows & Integrations Group (Modules 35–38, 40–42)

```mermaid
erDiagram
    WORKFLOW_DEFINITION ||--o{ APPROVAL_REQUEST : "routes"
    APPROVAL_REQUEST ||--o{ APPROVAL_DECISION : "append-only steps"
    LETTER_TEMPLATE ||--o{ GENERATED_LETTER : "snapshots merge_data"
    TENANT ||--o{ ATTACHMENT : "10MB virus-scanned S3/MinIO"
    TENANT ||--o{ API_KEY : "SHA-256 hashed"
    TENANT ||--o{ OAUTH2_CLIENT : "client_credentials"
    TENANT ||--o{ WEBHOOK_ENDPOINT : "HMAC-SHA256 HTTPS"
    WEBHOOK_ENDPOINT ||--o{ WEBHOOK_DELIVERY : "retries & logs"
    INTEGRATION_CONNECTOR_CONFIG ||--o{ INTEGRATION_RUN_LOG : "tracks"
    TENANT ||--o{ AUDIT_LOG : "immutable"
```
