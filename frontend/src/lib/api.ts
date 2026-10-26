export const API_BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";

export interface ModuleMeta {
  number: number;
  slug: string;
  name: string;
  group: string;
  phase: string;
  submodules: string[];
  key_rules: string;
}

export const ALL_42_MODULES_CATALOG: ModuleMeta[] = [
  {
    number: 1,
    slug: "management-dashboard",
    name: "Management Dashboard",
    group: "Overview",
    phase: "2, 6",
    submodules: ["Workforce overview", "Attendance summary", "Leave status", "Payroll summary", "Recruitment status", "Employee turnover", "Pending approvals"],
    key_rules: "Role-aware KPI tiles and charts. Reads other modules: v1 in Phase 2, complete in Phase 6",
  },
  {
    number: 2,
    slug: "company-organization",
    name: "Company & Organization",
    group: "Core HR",
    phase: "1",
    submodules: ["Company profiles", "Branches", "Departments", "Sections", "Designations", "Grades", "Cost centers", "Org chart", "Reporting lines"],
    key_rules: "Interactive org chart; reporting lines effective-dated",
  },
  {
    number: 3,
    slug: "employee-information",
    name: "Employee Information",
    group: "Core HR",
    phase: "1",
    submodules: ["Employee ID", "Personal info", "Contact", "Emergency contacts", "Family and nominees", "Qualifications", "Experience", "Bank info", "Documents", "Employment history"],
    key_rules: "Tabbed profile; sensitive fields permission-protected; names stored in English and Bangla",
  },
  {
    number: 4,
    slug: "workforce-planning",
    name: "Workforce Planning",
    group: "Talent Lifecycle",
    phase: "4",
    submodules: ["Department manpower plans", "Approved headcount", "Vacancy tracking", "Staffing budgets", "Replacement requests"],
    key_rules: "Headcount vs actual per department",
  },
  {
    number: 5,
    slug: "recruitment",
    name: "Recruitment",
    group: "Talent Lifecycle",
    phase: "4",
    submodules: ["Requisitions", "Job descriptions", "Vacancy publishing", "Applicant database", "Screening", "Interview scheduling and evaluation", "Selection approval", "Offer letters"],
    key_rules: "Kanban pipeline; optional public careers page",
  },
  {
    number: 6,
    slug: "employee-onboarding",
    name: "Employee Onboarding",
    group: "Talent Lifecycle",
    phase: "4",
    submodules: ["Pre-joining documents", "Joining checklist", "Appointment letters", "Account creation", "Asset requests", "Orientation", "Department introduction"],
    key_rules: "Checklist templates; converts a selected candidate into an employee",
  },
  {
    number: 7,
    slug: "probation-confirmation",
    name: "Probation & Confirmation",
    group: "Talent Lifecycle",
    phase: "4",
    submodules: ["Probation periods", "Review reminders", "Supervisor evaluations", "Extension", "Confirmation approval and letters"],
    key_rules: "Scheduled reminders",
  },
  {
    number: 8,
    slug: "attendance",
    name: "Attendance",
    group: "Time & Presence",
    phase: "2",
    submodules: ["Biometric/device integration", "Attendance import", "Daily attendance", "Late arrival", "Early departure", "Missing punches", "Manual corrections", "Approval"],
    key_rules: "Raw punches immutable; daily result computed from punches + shift + approved corrections; Monthly Summary includes NIS Days",
  },
  {
    number: 9,
    slug: "shift-roster",
    name: "Shift & Roster",
    group: "Time & Presence",
    phase: "2",
    submodules: ["Shift definitions", "Duty rosters", "Rotating and overnight shifts", "Weekly rest days", "Shift exchanges", "Roster approval"],
    key_rules: "Overnight shifts cross midnight correctly; roster batches assign many employees to a shift",
  },
  {
    number: 10,
    slug: "leave",
    name: "Leave",
    group: "Time & Presence",
    phase: "2",
    submodules: ["Leave types", "Entitlement rules", "Applications", "Approval", "Balances", "Accrual", "Carry-forward", "Encashment", "Unpaid leave", "Cancellation"],
    key_rules: "Balance is the sum of ledger entries (accrual, taken, adjustment, carry-forward, encashment, expiry)",
  },
  {
    number: 11,
    slug: "holiday-work-calendar",
    name: "Holiday & Work Calendar",
    group: "Time & Presence",
    phase: "2",
    submodules: ["Company calendars", "Public holidays", "Branch holidays", "Optional holidays", "Working days", "Special schedules"],
    key_rules: "Feeds attendance, leave, payroll. Friday off default",
  },
  {
    number: 12,
    slug: "overtime",
    name: "Overtime",
    group: "Time & Presence",
    phase: "2",
    submodules: ["Requests", "Supervisor approval", "Approved hours", "Rate configuration", "Holiday overtime", "Payroll integration"],
    key_rules: "Rate rules configurable",
  },
  {
    number: 13,
    slug: "field-duty-remote-work",
    name: "Field Duty & Remote Work",
    group: "Time & Presence",
    phase: "2",
    submodules: ["Movement requests", "Field assignments", "Remote-work requests", "Check-in/out", "Visit records", "Approval"],
    key_rules: "Mobile-friendly check-in with optional location capture",
  },
  {
    number: 14,
    slug: "salary-structure",
    name: "Salary Structure",
    group: "Payroll & Compensation",
    phase: "3",
    submodules: ["Salary grades", "Basic", "Allowances", "Fixed and variable components", "Effective dates", "Employee assignment", "Revision history"],
    key_rules: "Component engine with formulas (percent of basic, fixed amount). Revision = new row",
  },
  {
    number: 15,
    slug: "monthly-payroll",
    name: "Monthly Payroll",
    group: "Payroll & Compensation",
    phase: "3",
    submodules: ["Periods", "Attendance and leave inputs", "Proration", "Earnings", "Deductions", "Arrears", "Retro adjustments", "Preview", "Validation", "Approval", "Period locking"],
    key_rules: "Background job; reproducible; locked periods immutable",
  },
  {
    number: 16,
    slug: "bonus-incentives",
    name: "Bonus & Incentives",
    group: "Payroll & Compensation",
    phase: "3",
    submodules: ["Festival, performance, sales bonuses", "Eligibility", "Calculation", "Approval", "Payment tracking"],
    key_rules: "Eligibility rules configurable",
  },
  {
    number: 17,
    slug: "allowances-reimbursements",
    name: "Allowances & Reimbursements",
    group: "Payroll & Compensation",
    phase: "3",
    submodules: ["Mobile, transport, meals, travel, medical claims", "Receipts", "Entitlement limits", "Approval", "Payroll or direct payment"],
    key_rules: "Receipts via generic attachment system",
  },
  {
    number: 18,
    slug: "loans-salary-advances",
    name: "Loans & Salary Advances",
    group: "Payroll & Compensation",
    phase: "3",
    submodules: ["Applications", "Approval", "Disbursement", "Installment schedules", "Payroll deductions", "Outstanding balance", "Early settlement"],
    key_rules: "Loan balance is an append-only ledger",
  },
  {
    number: 19,
    slug: "benefits-funds",
    name: "Benefits & Funds",
    group: "Payroll & Compensation",
    phase: "3",
    submodules: ["Provident fund setup", "Employee/employer contributions", "Gratuity rules", "Insurance", "Eligibility", "Statements", "Settlement"],
    key_rules: "Contribution rates configurable per tenant",
  },
  {
    number: 20,
    slug: "tax-statutory-deductions",
    name: "Tax & Statutory Deductions",
    group: "Payroll & Compensation",
    phase: "3",
    submodules: ["Configurable tax schedules", "National insurance / social security schemes (NIS days)", "Declarations", "Taxable components", "Withholding", "Adjustments", "Statutory reports"],
    key_rules: "Slab tables per income year; NIS contributions use nis_days from the attendance summary",
  },
  {
    number: 21,
    slug: "salary-disbursement",
    name: "Salary Disbursement",
    group: "Payroll & Compensation",
    phase: "3",
    submodules: ["Payment approval", "Bank transfer files", "Cash payments", "Batches", "Failed payments", "Reconciliation", "Acknowledgment"],
    key_rules: "Bank/MFS (bKash/Nagad/BEFTN) export templates configurable",
  },
  {
    number: 22,
    slug: "payslips-payroll-reports",
    name: "Payslips & Payroll Reports",
    group: "Payroll & Compensation",
    phase: "3",
    submodules: ["Payslips", "Payroll register", "Earnings/deduction summaries", "Department and company costs", "Bank advice", "Year-to-date"],
    key_rules: "PDF payslips; Monthly salary sheet grouped by department with signature blocks and amount in words (Taka)",
  },
  {
    number: 23,
    slug: "performance",
    name: "Performance",
    group: "Talent Lifecycle",
    phase: "4",
    submodules: ["Goals", "Individual/team KPIs", "Review cycles", "Self and manager assessment", "Approval", "History"],
    key_rules: "Include 360 feedback survey option",
  },
  {
    number: 24,
    slug: "promotion-increment-transfer",
    name: "Promotion, Increment & Transfer",
    group: "Talent Lifecycle",
    phase: "4",
    submodules: ["Promotion requests", "Increment proposals", "Department/branch transfers", "Designation changes", "Approval", "Effective-date tracking", "Letters"],
    key_rules: "Approved change creates effective-dated records and updates salary",
  },
  {
    number: 25,
    slug: "training-development",
    name: "Training & Development",
    group: "Talent Lifecycle",
    phase: "4",
    submodules: ["Needs", "Calendar", "Nominations", "Attendance", "Assessments", "Certifications", "Costs", "Skills matrix"],
    key_rules: "Skill progression and training cost tracking",
  },
  {
    number: 26,
    slug: "employee-relations-grievances",
    name: "Employee Relations & Grievances",
    group: "Relations, Assets & Exit",
    phase: "5",
    submodules: ["Complaints", "Confidential grievances", "Case assignment", "Investigation", "Resolution", "Follow-up"],
    key_rules: "Only assigned handlers see a case",
  },
  {
    number: 27,
    slug: "disciplinary",
    name: "Disciplinary",
    group: "Relations, Assets & Exit",
    phase: "5",
    submodules: ["Incident reports", "Show-cause notices", "Responses", "Review proceedings", "Decisions", "Warning letters", "Action history"],
    key_rules: "Restricted class",
  },
  {
    number: 28,
    slug: "employee-assets",
    name: "Employee Assets",
    group: "Relations, Assets & Exit",
    phase: "5",
    submodules: ["Assignment", "Handover acknowledgment", "Return requests", "Damage/loss", "Clearance", "IT access checklist"],
    key_rules: "Asset movements are a ledger",
  },
  {
    number: 29,
    slug: "health-safety-welfare",
    name: "Health, Safety & Welfare",
    group: "Relations, Assets & Exit",
    phase: "5",
    submodules: ["Emergency info", "Incidents", "Safety training", "Restricted medical records", "Welfare requests", "Corrective actions"],
    key_rules: "Medical data under strict field-level permission",
  },
  {
    number: 30,
    slug: "resignation-separation",
    name: "Resignation & Separation",
    group: "Relations, Assets & Exit",
    phase: "5",
    submodules: ["Resignation requests", "Notice periods", "Exit approval", "Termination", "Exit interviews", "Last working day", "Separation letters"],
    key_rules: "Notice period and exit interview tracking",
  },
  {
    number: 31,
    slug: "clearance-final-settlement",
    name: "Clearance & Final Settlement",
    group: "Relations, Assets & Exit",
    phase: "5",
    submodules: ["Department clearance", "Asset returns", "Access revocation", "Unpaid salary", "Leave encashment", "Benefit settlement", "Loan recovery", "Approval"],
    key_rules: "Pulls from payroll, leave, loans, benefits, assets",
  },
  {
    number: 32,
    slug: "employee-self-service",
    name: "Employee Self-Service",
    group: "Self-Service & Support",
    phase: "2",
    submodules: ["Profile updates", "Attendance view", "Leave requests", "Payslips", "Expense claims", "Loan requests", "HR letters", "Documents", "Request tracking"],
    key_rules: "Mobile-first PWA experience; geofence check-in/out; profile changes need approval",
  },
  {
    number: 33,
    slug: "manager-self-service",
    name: "Manager Self-Service",
    group: "Self-Service & Support",
    phase: "2",
    submodules: ["Team directory", "Attendance review", "Leave approval", "Roster management", "Performance reviews", "Manpower requests", "Team reports"],
    key_rules: "Data scope = own + direct reports",
  },
  {
    number: 34,
    slug: "hr-helpdesk",
    name: "HR Helpdesk",
    group: "Self-Service & Support",
    phase: "5",
    submodules: ["Service requests", "Categories", "Assignment", "Priorities", "Response tracking", "Escalation", "Resolution history"],
    key_rules: "SLA timers",
  },
  {
    number: 35,
    slug: "policies-documents",
    name: "Policies & Documents",
    group: "Governance & Platform",
    phase: "1",
    submodules: ["Policy repository", "Version control", "Acknowledgment", "Expiry reminders", "Letter templates", "Document generation"],
    key_rules: "Letters render to PDF with company letterhead; keep merge data + template version",
  },
  {
    number: 36,
    slug: "announcements-communication",
    name: "Announcements & Communication",
    group: "Governance & Platform",
    phase: "1, 6",
    submodules: ["Company notices", "Department announcements", "Events", "Birthday/anniversary reminders", "Notification preferences"],
    key_rules: "Basic in Phase 1, final in 6",
  },
  {
    number: 37,
    slug: "approval-workflow-engine",
    name: "Approval Workflow Engine",
    group: "Governance & Platform",
    phase: "1",
    submodules: ["Module chains", "Amount-based approval", "Company/department routing", "Delegation", "Rejection reasons", "Escalation", "History"],
    key_rules: "Central approval engine reused by all modules; mandatory rejection reason",
  },
  {
    number: 38,
    slug: "reports-analytics",
    name: "Reports & Analytics",
    group: "Governance & Platform",
    phase: "6",
    submodules: ["Headcount", "Attendance", "Leave utilisation", "Payroll and overtime costs", "Recruitment", "Turnover", "Performance", "Custom filters", "Scheduled reports", "Excel/PDF export"],
    key_rules: "Reusable report definition framework",
  },
  {
    number: 39,
    slug: "users-roles-permissions",
    name: "Users, Roles & Permissions",
    group: "Governance & Platform",
    phase: "0, 1",
    submodules: ["User accounts", "Role permissions", "Company/branch/department access", "Record-level visibility", "Salary confidentiality", "Approval authority"],
    key_rules: "Approval authority separate from view/edit",
  },
  {
    number: 40,
    slug: "security-audit",
    name: "Security & Audit",
    group: "Governance & Platform",
    phase: "1, 6",
    submodules: ["Optional 2FA", "Login history", "Session controls", "Audit logs", "Sensitive-field history", "Document access logs", "Backup and recovery"],
    key_rules: "Immutable audit log",
  },
  {
    number: 41,
    slug: "integrations",
    name: "Integrations",
    group: "Governance & Platform",
    phase: "0, 6",
    submodules: ["Biometric devices", "Accounting/ERP", "Bank payment formats", "Email/SMS", "Recruitment portals", "API access", "Import/export logs"],
    key_rules: "Adapter pattern; every connector has a log screen",
  },
  {
    number: 42,
    slug: "system-settings-master-data",
    name: "System Settings & Master Data",
    group: "Governance & Platform",
    phase: "0, 1",
    submodules: ["Employee categories", "Employment types", "Grades", "Leave rules", "Payroll components", "Numbering formats", "Currencies", "Timezone", "Notification templates", "Retention"],
    key_rules: "Everything configurable per tenant; statutory rules flagged 'needs professional review'",
  },
];

let _accessToken: string | null = localStorage.getItem("nice_hris_token");
let _activeCompanyId: string | null = localStorage.getItem("nice_hris_company_id");

export function setAuthToken(token: string | null) {
  _accessToken = token;
  if (token) {
    localStorage.setItem("nice_hris_token", token);
  } else {
    localStorage.removeItem("nice_hris_token");
  }
}

export function getAuthToken(): string | null {
  return _accessToken;
}

export function setActiveCompanyHeader(companyId: string | null) {
  _activeCompanyId = companyId;
  if (companyId) {
    localStorage.setItem("nice_hris_company_id", companyId);
  } else {
    localStorage.removeItem("nice_hris_company_id");
  }
}

export async function apiFetch<T = any>(
  path: string,
  options: RequestInit & { idempotencyKey?: string } = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (_accessToken) {
    headers["Authorization"] = `Bearer ${_accessToken}`;
  }
  if (_activeCompanyId) {
    headers["X-Company-ID"] = _activeCompanyId;
  }
  if (options.idempotencyKey) {
    headers["Idempotency-Key"] = options.idempotencyKey;
  }

  const url = path.startsWith("http") ? path : `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    const msg = errBody?.error?.message || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return res.json();
}

export async function apiDownloadFile(path: string, filename: string): Promise<void> {
  const headers: Record<string, string> = {};
  if (_accessToken) {
    headers["Authorization"] = `Bearer ${_accessToken}`;
  }
  if (_activeCompanyId) {
    headers["X-Company-ID"] = _activeCompanyId;
  }
  const url = path.startsWith("http")
    ? path
    : `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, { headers, credentials: "include" });
  if (!res.ok) {
    throw new Error(`Download failed: HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}
