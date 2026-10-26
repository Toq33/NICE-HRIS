# 01. The 42 Modules

Phase numbers refer to `05-roadmap.md`. "Key rules" are binding build notes.

| # | Module | Submodules | Key rules | Phase |
|---|---|---|---|---|
| 1 | Management Dashboard | Workforce overview; attendance summary; leave status; payroll summary; recruitment status; employee turnover; pending approvals | Role-aware KPI tiles and charts. Reads other modules: v1 in Phase 2, complete in Phase 6 | 2, 6 |
| 2 | Company & Organization | Company profiles; branches; departments; sections; designations; grades; cost centers; org chart; reporting lines | Interactive org chart; reporting lines effective-dated | 1 |
| 3 | Employee Information | Employee ID; personal info; contact; emergency contacts; family and nominees; qualifications; experience; bank info; documents; employment history | Tabbed profile; sensitive fields permission-protected; names stored in English and Bangla | 1 |
| 4 | Workforce Planning | Department manpower plans; approved headcount; vacancy tracking; staffing budgets; replacement requests | Headcount vs actual per department | 4 |
| 5 | Recruitment | Requisitions; job descriptions; vacancy publishing; applicant database; screening; interview scheduling and evaluation; selection approval; offer letters | Kanban pipeline; optional public careers page | 4 |
| 6 | Employee Onboarding | Pre-joining documents; joining checklist; appointment letters; account creation; asset requests; orientation; department introduction | Checklist templates; converts a selected candidate into an employee | 4 |
| 7 | Probation & Confirmation | Probation periods; review reminders; supervisor evaluations; extension; confirmation approval and letters | Scheduled reminders | 4 |
| 8 | Attendance | Biometric/device integration; attendance import; daily attendance; late arrival; early departure; missing punches; manual corrections; approval | Raw punches immutable; daily result computed from punches + shift + approved corrections; safe to recompute; corrections via workflow | 2 |
| 9 | Shift & Roster | Shift definitions; duty rosters; rotating and overnight shifts; weekly rest days; shift exchanges; roster approval | Overnight shifts cross midnight correctly; roster batches assign many employees to a shift for a period | 2 |
| 10 | Leave | Leave types; entitlement rules; applications; approval; balances; accrual; carry-forward; encashment; unpaid leave; cancellation | Balance is the sum of ledger entries (accrual, taken, adjustment, carry-forward, encashment, expiry) | 2 |
| 11 | Holiday & Work Calendar | Company calendars; public holidays; branch holidays; optional holidays; working days; special schedules | Feeds attendance, leave, payroll. Friday off default | 2 |
| 12 | Overtime | Requests; supervisor approval; approved hours; rate configuration; holiday overtime; payroll integration | Rate rules configurable | 2 |
| 13 | Field Duty & Remote Work | Movement requests; field assignments; remote-work requests; check-in/out; visit records; approval | Mobile-friendly check-in with optional location capture | 2 |
| 14 | Salary Structure | Salary grades; basic; allowances; fixed and variable components; effective dates; employee assignment; revision history | Component engine with formulas (percent of basic, fixed amount). Revision = new row | 3 |
| 15 | Monthly Payroll | Periods; attendance and leave inputs; proration; earnings; deductions; arrears; retro adjustments; preview; validation; approval; period locking | Background job; reproducible; locked periods immutable. **Most critical module: heavy tests** | 3 |
| 16 | Bonus & Incentives | Festival, performance, sales bonuses; eligibility; calculation; approval; payment tracking | Eligibility rules configurable | 3 |
| 17 | Allowances & Reimbursements | Mobile, transport, meals, travel, medical claims; receipts; entitlement limits; approval; payroll or direct payment | Receipts via generic attachment system | 3 |
| 18 | Loans & Salary Advances | Applications; approval; disbursement; installment schedules; payroll deductions; outstanding balance; early settlement | Loan balance is a ledger | 3 |
| 19 | Benefits & Funds | Provident fund setup; employee/employer contributions; gratuity rules; insurance; eligibility; statements; settlement | Contribution rates configurable per tenant | 3 |
| 20 | Tax & Statutory Deductions | Configurable tax schedules; national insurance / social security schemes (NIS days, contributions, statutory report); declarations; taxable components; withholding; adjustments; deduction statements; statutory reports | Slab tables per income year; monthly withholding with year-end adjustment; NIS contributions use `nis_days` from the attendance summary | 3 |
| 21 | Salary Disbursement | Payment approval; bank transfer files; cash payments; batches; failed payments; reconciliation; acknowledgment | Bank/MFS export templates configurable | 3 |
| 22 | Payslips & Payroll Reports | Payslips; payroll register; earnings/deduction summaries; department and company costs; bank advice; year-to-date | PDF payslips with optional password. Monthly salary sheet grouped by department with signature blocks and amount in words | 3 |
| 23 | Performance | Goals; individual/team KPIs; review cycles; self and manager assessment; approval; history | Include 360 feedback survey option | 4 |
| 24 | Promotion, Increment & Transfer | Promotion requests; increment proposals; department/branch transfers; designation changes; approval; effective-date tracking; letters | Approved change creates effective-dated records and updates salary | 4 |
| 25 | Training & Development | Needs; calendar; nominations; attendance; assessments; certifications; costs; skills matrix | | 4 |
| 26 | Employee Relations & Grievances | Complaints; confidential grievances; case assignment; investigation; resolution; follow-up | Only assigned handlers see a case | 5 |
| 27 | Disciplinary | Incident reports; show-cause notices; responses; review proceedings; decisions; warning letters; action history | Restricted class | 5 |
| 28 | Employee Assets | Assignment; handover acknowledgment; return requests; damage/loss; clearance; IT access checklist | Asset movements are a ledger | 5 |
| 29 | Health, Safety & Welfare | Emergency info; incidents; safety training; restricted medical records; welfare requests; corrective actions | Medical data under strict field-level permission | 5 |
| 30 | Resignation & Separation | Resignation requests; notice periods; exit approval; termination; exit interviews; last working day; separation letters | | 5 |
| 31 | Clearance & Final Settlement | Department clearance; asset returns; access revocation; unpaid salary; leave encashment; benefit settlement; loan recovery; approval | Pulls from payroll, leave, loans, benefits, assets | 5 |
| 32 | Employee Self-Service | Profile updates; attendance view; leave requests; payslips; expense claims; loan requests; HR letters; documents; request tracking | Mobile-first; profile changes need approval | 2 |
| 33 | Manager Self-Service | Team directory; attendance review; leave approval; roster management; performance reviews; manpower requests; team reports | Data scope = own + direct reports | 2 |
| 34 | HR Helpdesk | Service requests; categories; assignment; priorities; response tracking; escalation; resolution history | SLA timers | 5 |
| 35 | Policies & Documents | Policy repository; version control; acknowledgment; expiry reminders; letter templates; document generation | Letters render to PDF with company letterhead; keep merge data + template version | 1 |
| 36 | Announcements & Communication | Company notices; department announcements; events; birthday/anniversary reminders; notification preferences | Basic in Phase 1, final in 6 | 1, 6 |
| 37 | Approval Workflow Engine | Module chains; amount-based approval; company/department routing; delegation; rejection reasons; escalation; history | See engine spec in `02`. Build and test first | 1 |
| 38 | Reports & Analytics | Headcount; attendance; leave utilisation; payroll and overtime costs; recruitment; turnover; performance; custom filters; scheduled reports; Excel/PDF export | Reusable report definition framework | 6 |
| 39 | Users, Roles & Permissions | User accounts; role permissions; company/branch/department access; record-level visibility; salary confidentiality; approval authority | Approval authority separate from view/edit | 0, 1 |
| 40 | Security & Audit | Optional 2FA; login history; session controls; audit logs; sensitive-field history; document access logs; backup and recovery | Immutable audit log | 1, 6 |
| 41 | Integrations | Biometric devices; accounting/ERP; bank payment formats; email/SMS; recruitment portals; API access; import/export logs | Adapter pattern; every connector has a log screen | 0, 6 |
| 42 | System Settings & Master Data | Employee categories; employment types; grades; leave rules; payroll components; numbering formats; currencies; timezone; notification templates; retention | Everything configurable per tenant | 0, 1 |

## Platform level (above tenants): Platform Admin
Plans, enabled modules per tenant, employee limits, tenant status (trial, active, suspended), usage view, create tenant. Built in Phase 0.

## Mobile
Employee Self-Service (32) and manager approvals must be fully usable on a phone. Required flows, taken from the current product: dashboard (today's status, leave balance, team present/on leave/absent, announcements, profile), check-in/out with geofence status, attendance records with date-range filter and status badges (Present, Late), leave request and tracking, payslip and PF statement with PDF download.
Decision: responsive installable web app (PWA) first; native app later if needed, reusing the same API.
