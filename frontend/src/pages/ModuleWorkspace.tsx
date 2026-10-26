import React, { useEffect, useState } from "react";
import {
  Avatar,
  Button,
  CalendarGrid,
  DataTable,
  GlassCard,
  GlassPanel,
  Input,
  KanbanBoard,
  KPITile,
  Modal,
  OrgChartNode,
  PivotTable,
  SignatureBlock,
  StatusPill,
  StatutoryDisclaimerBanner,
  Stepper,
  Tabs,
} from "../components/glass";
import { ModuleCreateDrawer } from "../components/ModuleCreateDrawer";
import { ALL_42_MODULES_CATALOG, apiDownloadFile, apiFetch } from "../lib/api";
import { formatBDT } from "../i18n";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  AreaChart,
  Area,
} from "recharts";
import {
  Building2,
  Calendar,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Download,
  FileText,
  Key,
  Lock,
  MapPin,
  Network,
  Plus,
  Printer,
  RefreshCw,
  Send,
  ShieldAlert,
  Sparkles,
  Target,
  UserCheck,
  Users,
  Wallet,
  Webhook,
} from "lucide-react";

interface WorkspaceProps {
  moduleNumber: number;
  lakhGrouping: boolean;
  activeCompanyId: string | null;
}

export const ModuleWorkspace: React.FC<WorkspaceProps> = ({
  moduleNumber,
  lakhGrouping,
  activeCompanyId,
}) => {
  const mod =
    ALL_42_MODULES_CATALOG.find((m) => m.number === moduleNumber) ||
    ALL_42_MODULES_CATALOG[0];

  const [loading, setLoading] = useState(false);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [employees, setEmployees] = useState<any[]>([]);
  const [empIndex, setEmpIndex] = useState(0);
  const [companies, setCompanies] = useState<any[]>([]);
  const [branches, setBranches] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [attendanceDays, setAttendanceDays] = useState<any[]>([]);
  const [attendanceSummaries, setAttendanceSummaries] = useState<any[]>([]);
  const [shifts, setShifts] = useState<any[]>([]);
  const [rosterBatches, setRosterBatches] = useState<any[]>([]);
  const [leaveRequests, setLeaveRequests] = useState<any[]>([]);
  const [leaveLedger, setLeaveLedger] = useState<any[]>([]);
  const [holidays, setHolidays] = useState<any[]>([]);
  const [overtimeList, setOvertimeList] = useState<any[]>([]);
  const [fieldMovements, setFieldMovements] = useState<any[]>([]);
  const [salaryStructures, setSalaryStructures] = useState<any[]>([]);
  const [payrollRuns, setPayrollRuns] = useState<any[]>([]);
  const [payslips, setPayslips] = useState<any[]>([]);
  const [selectedPayslip, setSelectedPayslip] = useState<any | null>(null);
  const [statutorySchemes, setStatutorySchemes] = useState<any[]>([]);
  const [taxSlabs, setTaxSlabs] = useState<any[]>([]);
  const [bonuses, setBonuses] = useState<any[]>([]);
  const [expenses, setExpenses] = useState<any[]>([]);
  const [loans, setLoans] = useState<any[]>([]);
  const [pfLedger, setPfLedger] = useState<any[]>([]);
  const [paymentBatches, setPaymentBatches] = useState<any[]>([]);
  const [manpowerPlans, setManpowerPlans] = useState<any[]>([]);
  const [applicants, setApplicants] = useState<any[]>([]);
  const [onboardingList, setOnboardingList] = useState<any[]>([]);
  const [probationList, setProbationList] = useState<any[]>([]);
  const [appraisals, setAppraisals] = useState<any[]>([]);
  const [careerMovements, setCareerMovements] = useState<any[]>([]);
  const [trainings, setTrainings] = useState<any[]>([]);
  const [grievances, setGrievances] = useState<any[]>([]);
  const [disciplinaryList, setDisciplinaryList] = useState<any[]>([]);
  const [assets, setAssets] = useState<any[]>([]);
  const [healthRecords, setHealthRecords] = useState<any[]>([]);
  const [resignations, setResignations] = useState<any[]>([]);
  const [settlements, setSettlements] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [policies, setPolicies] = useState<any[]>([]);
  const [letters, setLetters] = useState<any[]>([]);
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [approvals, setApprovals] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [usersList, setUsersList] = useState<any[]>([]);
  const [rolesList, setRolesList] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [newRawKey, setNewRawKey] = useState<string | null>(null);
  const [webhooks, setWebhooks] = useState<any[]>([]);
  const [connectors, setConnectors] = useState<any[]>([]);
  const [tenantSettings, setTenantSettings] = useState<any[]>([]);
  const [numberSequences, setNumberSequences] = useState<any[]>([]);
  const [emergencyContacts, setEmergencyContacts] = useState<any[]>([]);
  const [familyMembers, setFamilyMembers] = useState<any[]>([]);
  const [qualifications, setQualifications] = useState<any[]>([]);
  const [experiences, setExperiences] = useState<any[]>([]);
  const [employmentRecords, setEmploymentRecords] = useState<any[]>([]);
  const [employeeDocuments, setEmployeeDocuments] = useState<any[]>([]);
  const [undoAction, setUndoAction] = useState<(() => void) | null>(null);

  // Interactive modals / drawers
  const [activeTab, setActiveTab] = useState("primary");
  const [rejectModalApproval, setRejectModalApproval] = useState<any | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const notify = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const unwrap = (res: any) => (Array.isArray(res) ? res : res?.results || []);

  const loadModuleData = async () => {
    setLoading(true);
    try {
      if (moduleNumber === 1) {
        const [dash, appr] = await Promise.all([
          apiFetch("/dashboard/summary/"),
          apiFetch("/workflows/approvals/"),
        ]);
        setDashboardData(dash);
        setApprovals(unwrap(appr));
      } else if (moduleNumber === 2) {
        const [c, b, d, e] = await Promise.all([
          apiFetch("/organization/companies/"),
          apiFetch("/organization/branches/"),
          apiFetch("/organization/departments/"),
          apiFetch("/employees/"),
        ]);
        setCompanies(unwrap(c));
        setBranches(unwrap(b));
        setDepartments(unwrap(d));
        setEmployees(unwrap(e));
      } else if (moduleNumber === 3 || moduleNumber === 32 || moduleNumber === 33) {
        const [e, l, p, a, ec, fm, eq, ex, er, ed] = await Promise.all([
          apiFetch("/employees/"),
          apiFetch("/time/leave-requests/"),
          apiFetch("/payroll/payslips/"),
          apiFetch("/time/attendance-days/"),
          apiFetch("/employees/emergency-contacts/"),
          apiFetch("/employees/family-members/"),
          apiFetch("/employees/qualifications/"),
          apiFetch("/employees/experiences/"),
          apiFetch("/employees/employment-records/"),
          apiFetch("/employees/documents/"),
        ]);
        setEmployees(unwrap(e));
        setLeaveRequests(unwrap(l));
        setPayslips(unwrap(p));
        setAttendanceDays(unwrap(a));
        setEmergencyContacts(unwrap(ec));
        setFamilyMembers(unwrap(fm));
        setQualifications(unwrap(eq));
        setExperiences(unwrap(ex));
        setEmploymentRecords(unwrap(er));
        setEmployeeDocuments(unwrap(ed));
      } else if (moduleNumber === 4) {
        setManpowerPlans(unwrap(await apiFetch("/talent/manpower-plans/")));
      } else if (moduleNumber === 5) {
        setApplicants(unwrap(await apiFetch("/talent/applicants/")));
      } else if (moduleNumber === 6) {
        setOnboardingList(unwrap(await apiFetch("/talent/onboarding/")));
      } else if (moduleNumber === 7) {
        setProbationList(unwrap(await apiFetch("/talent/probation-reviews/")));
      } else if (moduleNumber === 8) {
        const [days, sums] = await Promise.all([
          apiFetch("/time/attendance-days/"),
          apiFetch("/time/attendance-summaries/"),
        ]);
        setAttendanceDays(unwrap(days));
        setAttendanceSummaries(unwrap(sums));
      } else if (moduleNumber === 9) {
        const [sh, rb] = await Promise.all([
          apiFetch("/time/shifts/"),
          apiFetch("/time/roster-batches/"),
        ]);
        setShifts(unwrap(sh));
        setRosterBatches(unwrap(rb));
      } else if (moduleNumber === 10) {
        const [reqs, led] = await Promise.all([
          apiFetch("/time/leave-requests/"),
          apiFetch("/time/leave-ledger/"),
        ]);
        setLeaveRequests(unwrap(reqs));
        setLeaveLedger(unwrap(led));
      } else if (moduleNumber === 11) {
        setHolidays(unwrap(await apiFetch("/time/holidays/")));
      } else if (moduleNumber === 12) {
        setOvertimeList(unwrap(await apiFetch("/time/overtime-requests/")));
      } else if (moduleNumber === 13) {
        setFieldMovements(unwrap(await apiFetch("/time/field-duty/")));
      } else if (moduleNumber === 14) {
        setSalaryStructures(unwrap(await apiFetch("/payroll/salary-structures/")));
      } else if (moduleNumber === 15 || moduleNumber === 22) {
        const [runs, slips] = await Promise.all([
          apiFetch("/payroll/runs/"),
          apiFetch("/payroll/payslips/"),
        ]);
        setPayrollRuns(unwrap(runs));
        setPayslips(unwrap(slips));
      } else if (moduleNumber === 16) {
        setBonuses(unwrap(await apiFetch("/payroll/bonuses/")));
      } else if (moduleNumber === 17) {
        setExpenses(unwrap(await apiFetch("/payroll/expense-claims/")));
      } else if (moduleNumber === 18) {
        setLoans(unwrap(await apiFetch("/payroll/loans/")));
      } else if (moduleNumber === 19) {
        setPfLedger(unwrap(await apiFetch("/payroll/pf-ledger/")));
      } else if (moduleNumber === 20) {
        const [sch, slabs] = await Promise.all([
          apiFetch("/payroll/statutory-schemes/"),
          apiFetch("/payroll/tax-slabs/"),
        ]);
        setStatutorySchemes(unwrap(sch));
        setTaxSlabs(unwrap(slabs));
      } else if (moduleNumber === 21) {
        setPaymentBatches(unwrap(await apiFetch("/payroll/payment-batches/")));
      } else if (moduleNumber === 23) {
        setAppraisals(unwrap(await apiFetch("/talent/appraisals/")));
      } else if (moduleNumber === 24) {
        setCareerMovements(unwrap(await apiFetch("/talent/career-movements/")));
      } else if (moduleNumber === 25) {
        setTrainings(unwrap(await apiFetch("/talent/trainings/")));
      } else if (moduleNumber === 26) {
        setGrievances(unwrap(await apiFetch("/relations/grievances/")));
      } else if (moduleNumber === 27) {
        setDisciplinaryList(unwrap(await apiFetch("/relations/disciplinary/")));
      } else if (moduleNumber === 28) {
        setAssets(unwrap(await apiFetch("/relations/assets/")));
      } else if (moduleNumber === 29) {
        setHealthRecords(unwrap(await apiFetch("/relations/health-safety/")));
      } else if (moduleNumber === 30) {
        setResignations(unwrap(await apiFetch("/relations/resignations/")));
      } else if (moduleNumber === 31) {
        setSettlements(unwrap(await apiFetch("/relations/final-settlements/")));
      } else if (moduleNumber === 34) {
        setTickets(unwrap(await apiFetch("/helpdesk/tickets/")));
      } else if (moduleNumber === 35) {
        const [pol, ltr] = await Promise.all([
          apiFetch("/policies/documents/"),
          apiFetch("/policies/generated-letters/"),
        ]);
        setPolicies(unwrap(pol));
        setLetters(unwrap(ltr));
      } else if (moduleNumber === 36) {
        setAnnouncements(unwrap(await apiFetch("/communications/announcements/")));
      } else if (moduleNumber === 37) {
        setApprovals(unwrap(await apiFetch("/workflows/approvals/")));
      } else if (moduleNumber === 38) {
        const [rep, dash] = await Promise.all([
          apiFetch("/reports/definitions/"),
          apiFetch("/dashboard/summary/"),
        ]);
        setReports(unwrap(rep));
        setDashboardData(dash);
      } else if (moduleNumber === 39) {
        const [u, r] = await Promise.all([
          apiFetch("/accounts/users/"),
          apiFetch("/accounts/roles/"),
        ]);
        setUsersList(unwrap(u));
        setRolesList(unwrap(r));
      } else if (moduleNumber === 40) {
        setAuditLogs(unwrap(await apiFetch("/security/audit-logs/")));
      } else if (moduleNumber === 41) {
        const [k, w, c] = await Promise.all([
          apiFetch("/integrations/api-keys/"),
          apiFetch("/integrations/webhooks/"),
          apiFetch("/integrations/connectors/"),
        ]);
        setApiKeys(unwrap(k));
        setWebhooks(unwrap(w));
        setConnectors(unwrap(c));
      } else if (moduleNumber === 42) {
        const [cfg, seq] = await Promise.all([
          apiFetch("/settings/tenant-config/"),
          apiFetch("/settings/number-sequences/"),
        ]);
        setTenantSettings(unwrap(cfg));
        setNumberSequences(unwrap(seq));
      }
    } catch (err: any) {
      notify(`Notice: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setActiveTab("primary");
    loadModuleData();
  }, [moduleNumber, activeCompanyId]);

  const handleMobileCheckIn = async (punchType: "IN" | "OUT") => {
    try {
      await apiFetch("/time/attendance-days/mobile-punch/", {
        method: "POST",
        body: JSON.stringify({
          punch_type: punchType,
          latitude: 23.7925,
          longitude: 90.4078,
          within_geofence: true,
        }),
      });
      notify(`Mobile Check-${punchType} recorded inside Gulshan HQ geofence!`);
      loadModuleData();
    } catch (err: any) {
      notify(err.message);
    }
  };

  const handleAdvanceAttendanceSummary = async (summaryId: string, nisDays: number) => {
    try {
      await apiFetch(`/time/attendance-summaries/${summaryId}/advance-status/`, {
        method: "POST",
        body: JSON.stringify({ nis_days: nisDays }),
      });
      notify("Monthly Attendance Summary & NIS Days advanced!");
      loadModuleData();
    } catch (err: any) {
      notify(err.message);
    }
  };

  const handleApproveLeave = async (leaveId: string) => {
    try {
      await apiFetch(`/time/leave-requests/${leaveId}/approve/`, { method: "POST" });
      notify("Leave approved and deducted from append-only LeaveLedger!");
      loadModuleData();
    } catch (err: any) {
      notify(err.message);
    }
  };

  const handleLockPayrollRun = async (runId: string) => {
    try {
      await apiFetch(`/payroll/runs/${runId}/lock/`, { method: "POST" });
      notify("Payroll Run & Period permanently locked (immutable)!");
      loadModuleData();
    } catch (err: any) {
      notify(err.message);
    }
  };

  const handleWorkflowDecision = async (
    reqId: string,
    decision: "APPROVED" | "REJECTED",
    comments: string
  ) => {
    try {
      await apiFetch(`/workflows/approvals/${reqId}/decide/`, {
        method: "POST",
        body: JSON.stringify({ decision, comments }),
      });
      notify(`Workflow request ${decision.toLowerCase()} & logged in AuditLog!`);
      setRejectModalApproval(null);
      setRejectReason("");
      loadModuleData();
    } catch (err: any) {
      notify(err.message);
    }
  };

  const handleGenerateApiKey = async () => {
    try {
      const created = await apiFetch("/integrations/api-keys/", {
        method: "POST",
        idempotencyKey: `idem-${Date.now()}`,
        body: JSON.stringify({
          name: `ERP Sync Key (${new Date().toLocaleTimeString()})`,
          scopes: ["employees:read", "attendance:write", "payroll:read"],
        }),
      });
      setNewRawKey(created.raw_key);
      notify("Scoped API Key generated (shown once)!");
      loadModuleData();
    } catch (err: any) {
      notify(err.message);
    }
  };

  const currentEmp = employees[empIndex] || employees[0];

  return (
    <div className="h-full flex flex-col gap-3 overflow-y-auto pr-0.5">
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 glass-strong px-4 py-3 border-l-4 border-l-primary text-xs font-semibold text-ink shadow-xl flex items-center gap-3">
          <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
          <span>{toastMessage}</span>
          {undoAction && (
            <button
              onClick={() => {
                undoAction();
                setUndoAction(null);
                setToastMessage(null);
              }}
              className="px-2 py-0.5 rounded bg-indigo-500/15 text-primary font-bold hover:bg-indigo-500/25"
            >
              Undo
            </button>
          )}
        </div>
      )}

      {/* Module Header Banner */}
      <GlassCard className="shrink-0 py-2.5 px-4 flex flex-wrap items-center justify-between gap-2">
        <div className="space-y-0.5 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2 py-0.5 text-[11px] font-bold rounded-pill bg-primary text-white">
              Module #{mod.number}
            </span>
            <span className="px-2 py-0.5 text-[11px] font-semibold rounded-pill bg-indigo-500/10 text-primary">
              {mod.group} • Phase {mod.phase}
            </span>
            <h1 className="text-base font-bold text-ink">{mod.name}</h1>
            <span className="text-xs text-ink-2 hidden xl:inline">— {mod.key_rules}</span>
          </div>
          <div className="flex flex-wrap gap-1 pt-0.5">
            {mod.submodules.map((sub) => (
              <span
                key={sub}
                className="px-1.5 py-0.2 text-[10px] font-medium rounded bg-white/70 border border-white/90 text-ink-2"
              >
                {sub}
              </span>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="sm" onClick={loadModuleData}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
          <Button size="sm" onClick={() => setDrawerOpen(true)}>
            <Plus className="w-3.5 h-3.5" />
            <span>New Record</span>
          </Button>
        </div>
      </GlassCard>

      {/* MODULE 1: MANAGEMENT DASHBOARD */}
      {moduleNumber === 1 && dashboardData && (
        <div className="flex-1 min-h-0 flex flex-col gap-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 shrink-0">
            <KPITile
              label="Total Workforce"
              value={dashboardData.kpis.total_employees}
              subtitle={`${dashboardData.kpis.probation_employees} on probation`}
              badge="ACTIVE"
              icon={<Users className="w-3.5 h-3.5" />}
            />
            <KPITile
              label="Today Present / Late"
              value={`${dashboardData.kpis.present_records} (${dashboardData.kpis.late_arrivals} Late)`}
              subtitle="Biometric + Mobile Geofence"
              badge="PRESENT"
              icon={<UserCheck className="w-3.5 h-3.5" />}
            />
            <KPITile
              label="Pending Approvals"
              value={dashboardData.kpis.pending_approvals}
              subtitle="Workflow Engine (Module 37)"
              badge="PENDING"
              icon={<Sparkles className="w-3.5 h-3.5" />}
            />
            <KPITile
              label="Annualized Turnover"
              value={`${dashboardData.kpis.turnover_rate_pct}%`}
              subtitle={`Avg tenure: ${dashboardData.kpis.avg_tenure_months} mos`}
              badge="APPROVED"
              icon={<Target className="w-3.5 h-3.5" />}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 shrink-0">
            <GlassCard className="space-y-1.5 py-2.5 px-3.5">
              <h3 className="text-xs font-bold text-ink">
                Workforce Headcount Variation by Month
              </h3>
              <div className="h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dashboardData.monthly_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                    <XAxis dataKey="month" fontSize={11} />
                    <YAxis fontSize={11} />
                    <Tooltip />
                    <Bar dataKey="headcount" fill="#4F46E5" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>

            <GlassCard className="space-y-1.5 py-2.5 px-3.5">
              <h3 className="text-xs font-bold text-ink">
                Monthly Attendance Compliance (%)
              </h3>
              <div className="h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={dashboardData.monthly_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                    <XAxis dataKey="month" fontSize={11} />
                    <YAxis domain={[85, 100]} fontSize={11} />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="attendance_pct"
                      stroke="#0EA5E9"
                      fill="rgba(14, 165, 233, 0.25)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>
          </div>

          <DataTable
            columns={[
              { key: "department", header: "Department" },
              { key: "approved_headcount", header: "Approved Manpower" },
              { key: "actual_headcount", header: "Actual Employees" },
              {
                key: "vacancy",
                header: "Vacancy / Utilization",
                render: (r) => (
                  <StatusPill
                    status={`${Math.max(0, r.approved_headcount - r.actual_headcount)} Open`}
                    tone="info"
                  />
                ),
              },
            ]}
            data={dashboardData.department_breakdown || []}
          />
        </div>
      )}

      {/* MODULE 2: COMPANY & ORGANIZATION (Interactive Org Chart + Hierarchy) */}
      {moduleNumber === 2 && (
        <div className="space-y-6">
          <Tabs
            tabs={[
              { id: "primary", label: "Interactive Org Chart", count: employees.length },
              { id: "companies", label: "Legal Entities", count: companies.length },
              { id: "branches", label: "Branches & Geofences", count: branches.length },
              { id: "departments", label: "Departments", count: departments.length },
            ]}
            activeTab={activeTab}
            onChange={setActiveTab}
          />

          {activeTab === "primary" && (
            <GlassPanel className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-ink flex items-center gap-2">
                    <Network className="w-4 h-4 text-primary" />
                    <span>Effective-Dated Organizational Reporting Hierarchy</span>
                  </h3>
                  <p className="text-xs text-muted">
                    Reporting lines are effective-dated; revisions create a new row without overwriting history.
                  </p>
                </div>
                <StatusPill status="Effective: Oct 2026" />
              </div>

              {employees.length > 0 && (
                <div className="flex flex-col items-center gap-6 py-4 overflow-x-auto">
                  <OrgChartNode
                    name={employees[0].full_name}
                    nameBn={employees[0].full_name_bn}
                    title={employees[0].designation_title}
                    department={employees[0].department_name}
                    code={employees[0].employee_code}
                  />
                  <div className="w-0.5 h-6 bg-indigo-400" />
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {employees.slice(1, 7).map((emp) => (
                      <OrgChartNode
                        key={emp.id}
                        name={emp.full_name}
                        nameBn={emp.full_name_bn}
                        title={emp.designation_title}
                        department={emp.department_name}
                        code={emp.employee_code}
                      />
                    ))}
                  </div>
                </div>
              )}
            </GlassPanel>
          )}

          {activeTab === "companies" && (
            <DataTable
              columns={[
                { key: "code", header: "Entity Code" },
                {
                  key: "name",
                  header: "Company Name (EN / BN)",
                  render: (r) => (
                    <div>
                      <div className="font-semibold">{r.name}</div>
                      <div className="text-xs text-muted">{r.name_bn}</div>
                    </div>
                  ),
                },
                { key: "registration_no", header: "RJSC Reg No" },
                { key: "currency", header: "Currency" },
                { key: "timezone", header: "Timezone" },
                { key: "branch_count", header: "Branches" },
                { key: "employee_count", header: "Employees" },
              ]}
              data={companies}
            />
          )}

          {activeTab === "branches" && (
            <DataTable
              columns={[
                { key: "code", header: "Branch Code" },
                {
                  key: "name",
                  header: "Branch (EN / BN)",
                  render: (r) => (
                    <div>
                      <div className="font-semibold">{r.name}</div>
                      <div className="text-xs text-muted">{r.name_bn}</div>
                    </div>
                  ),
                },
                { key: "company_name", header: "Legal Entity" },
                { key: "city", header: "City" },
                {
                  key: "geofence",
                  header: "Geofence Coordinates",
                  render: (r) => (
                    <span className="text-xs font-mono text-ink-2">
                      {r.latitude}, {r.longitude} ({r.geofence_radius_meters}m)
                    </span>
                  ),
                },
              ]}
              data={branches}
            />
          )}

          {activeTab === "departments" && (
            <DataTable
              columns={[
                { key: "code", header: "Code" },
                {
                  key: "name",
                  header: "Department (EN / BN)",
                  render: (r) => (
                    <div>
                      <div className="font-semibold">{r.name}</div>
                      <div className="text-xs text-muted">{r.name_bn}</div>
                    </div>
                  ),
                },
                { key: "branch_name", header: "Branch" },
                { key: "approved_headcount", header: "Approved Headcount" },
                { key: "actual_headcount", header: "Actual Employees" },
              ]}
              data={departments}
            />
          )}
        </div>
      )}

      {/* MODULE 3: EMPLOYEE INFORMATION (Reference Screen Form + Smart Buttons + Pager + Directory) */}
      {moduleNumber === 3 && (
        <div className="space-y-6">
          {currentEmp && (
            <GlassPanel className="space-y-5">
              {/* Top Bar with Smart Buttons and Record Pager (81/168 reference pattern) */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-200/80">
                <div className="flex flex-wrap items-center gap-2">
                  {[
                    { label: "Documents", val: "4 Files" },
                    { label: "In Contract Since", val: currentEmp.joining_date },
                    { label: "Goals & KPIs", val: "92% Score" },
                    { label: "Org Chart", val: currentEmp.department_name },
                  ].map((sb) => (
                    <div
                      key={sb.label}
                      className="px-3 py-1.5 rounded-control bg-indigo-50/90 border border-indigo-200/80 text-xs"
                    >
                      <span className="text-muted block text-[10px] uppercase font-bold">
                        {sb.label}
                      </span>
                      <span className="font-bold text-primary">{sb.val}</span>
                    </div>
                  ))}
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-ink-2">
                    Record {empIndex + 1} / {employees.length}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      setEmpIndex((i) => (i > 0 ? i - 1 : Math.max(0, employees.length - 1)))
                    }
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      setEmpIndex((i) => (i + 1) % Math.max(1, employees.length))
                    }
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Employee Form Header Card */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
                <div className="flex items-center gap-4">
                  <Avatar name={currentEmp.full_name} size="lg" />
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-bold text-ink">
                        {currentEmp.full_name}
                      </h2>
                      <StatusPill status={currentEmp.employment_status} />
                    </div>
                    <p className="text-sm font-medium text-ink-2">
                      {currentEmp.full_name_bn}
                    </p>
                    <p className="text-xs text-primary font-semibold mt-0.5">
                      {currentEmp.employee_code} • {currentEmp.designation_title}
                    </p>
                  </div>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div>
                    <span className="text-muted">Work Email:</span>{" "}
                    <strong className="text-ink">{currentEmp.work_email}</strong>
                  </div>
                  <div>
                    <span className="text-muted">Mobile (BD):</span>{" "}
                    <strong className="text-ink">{currentEmp.phone}</strong>
                  </div>
                  <div>
                    <span className="text-muted">Company & Branch:</span>{" "}
                    <strong className="text-ink">
                      {currentEmp.company_name} ({currentEmp.branch_name})
                    </strong>
                  </div>
                  <div>
                    <span className="text-muted">Department & Manager:</span>{" "}
                    <strong className="text-ink">
                      {currentEmp.department_name} • {currentEmp.manager_name || "MD"}
                    </strong>
                  </div>
                </div>

                <div className="p-3.5 rounded-control bg-amber-50/70 border border-amber-200/80 space-y-1.5 text-xs">
                  <div className="font-bold text-amber-900 flex items-center gap-1.5">
                    <Lock className="w-3.5 h-3.5" />
                    <span>Restricted & Encrypted Fields (AGENTS.md Sec 7)</span>
                  </div>
                  <div>
                    <span className="text-muted">National ID (Encrypted):</span>{" "}
                    <code className="font-mono font-bold">
                      {currentEmp.national_id_masked}
                    </code>
                  </div>
                  <div>
                    <span className="text-muted">Bank Account ({currentEmp.bank_name}):</span>{" "}
                    <code className="font-mono font-bold">
                      {currentEmp.bank_account_masked}
                    </code>
                  </div>
                  <div>
                    <span className="text-muted">Monthly Gross Salary:</span>{" "}
                    <strong className="text-primary">
                      {formatBDT(currentEmp.gross_salary_display, lakhGrouping)}
                    </strong>
                  </div>
                </div>
              </div>
            </GlassPanel>
          )}

          <Tabs
            tabs={[
              { id: "primary", label: "Employee Directory", count: employees.length },
              {
                id: "family",
                label: "Family & Emergency",
                count: familyMembers.length + emergencyContacts.length,
              },
              {
                id: "qualifications",
                label: "Qualifications & Experience",
                count: qualifications.length + experiences.length,
              },
              {
                id: "contracts",
                label: "Contracts & Transfers",
                count: employmentRecords.length,
              },
              {
                id: "documents",
                label: "Verified Documents",
                count: employeeDocuments.length,
              },
            ]}
            activeTab={activeTab}
            onChange={setActiveTab}
          />

          {activeTab === "primary" && (
            <DataTable
              columns={[
                { key: "employee_code", header: "Emp ID" },
                {
                  key: "full_name",
                  header: "Name (English & বাংলা)",
                  render: (r) => (
                    <div>
                      <div className="font-semibold">{r.full_name}</div>
                      <div className="text-xs text-muted">{r.full_name_bn}</div>
                    </div>
                  ),
                },
                { key: "company_name", header: "Company" },
                { key: "department_name", header: "Department" },
                { key: "designation_title", header: "Designation" },
                { key: "national_id_masked", header: "NID (Masked)" },
                {
                  key: "gross_salary_display",
                  header: "Gross Salary",
                  render: (r) => (
                    <span className="font-semibold">
                      {formatBDT(r.gross_salary_display, lakhGrouping)}
                    </span>
                  ),
                },
                {
                  key: "employment_status",
                  header: "Status",
                  render: (r) => <StatusPill status={r.employment_status} />,
                },
              ]}
              data={employees}
              searchPlaceholder="Search employees by ID, English/Bangla name, or department..."
            />
          )}

          {activeTab === "family" && (
            <div className="space-y-6">
              <DataTable
                columns={[
                  { key: "employee_name", header: "Employee" },
                  { key: "full_name", header: "Family Member" },
                  { key: "relationship", header: "Relationship" },
                  { key: "date_of_birth", header: "DOB" },
                  { key: "nominee_share_pct", header: "PF/Gratuity Nominee Share (%)" },
                ]}
                data={familyMembers}
              />
              <DataTable
                columns={[
                  { key: "employee_name", header: "Employee" },
                  { key: "name", header: "Emergency Contact" },
                  { key: "relationship", header: "Relationship" },
                  { key: "phone", header: "Phone (BD)" },
                  { key: "address", header: "Address" },
                ]}
                data={emergencyContacts}
              />
            </div>
          )}

          {activeTab === "qualifications" && (
            <div className="space-y-6">
              <DataTable
                columns={[
                  { key: "employee_name", header: "Employee" },
                  { key: "degree_or_certification", header: "Degree / Certification" },
                  { key: "institution", header: "University / Institute" },
                  { key: "passing_year", header: "Year" },
                  { key: "result_or_cgpa", header: "Result / CGPA" },
                ]}
                data={qualifications}
              />
              <DataTable
                columns={[
                  { key: "employee_name", header: "Employee" },
                  { key: "employer_name", header: "Previous Employer" },
                  { key: "designation_held", header: "Designation" },
                  { key: "start_date", header: "From" },
                  { key: "end_date", header: "To" },
                  { key: "responsibilities", header: "Key Responsibilities" },
                ]}
                data={experiences}
              />
            </div>
          )}

          {activeTab === "contracts" && (
            <DataTable
              columns={[
                { key: "contract_reference", header: "Contract Ref" },
                { key: "employee_name", header: "Employee" },
                { key: "company_name", header: "Company" },
                { key: "department_name", header: "Department" },
                { key: "designation_title", header: "Designation" },
                { key: "contract_type", header: "Type" },
                { key: "effective_from", header: "Effective From" },
                {
                  key: "effective_to",
                  header: "Effective To",
                  render: (r) => r.effective_to || "Current (Open)",
                },
                {
                  key: "status",
                  header: "Status",
                  render: (r) => <StatusPill status={r.status} />,
                },
              ]}
              data={employmentRecords}
            />
          )}

          {activeTab === "documents" && (
            <DataTable
              columns={[
                { key: "employee_name", header: "Employee" },
                { key: "document_type", header: "Doc Type" },
                { key: "title", header: "Document Title" },
                { key: "issue_date", header: "Issued" },
                { key: "expiry_date", header: "Expires" },
                { key: "storage_key", header: "S3/MinIO Private Key" },
                {
                  key: "is_verified",
                  header: "Verification",
                  render: (r) => (
                    <StatusPill status={r.is_verified ? "VERIFIED" : "PENDING"} />
                  ),
                },
              ]}
              data={employeeDocuments}
            />
          )}
        </div>
      )}

      {/* MODULE 8: ATTENDANCE & MONTHLY SUMMARY WITH NIS DAYS COLUMN */}
      {moduleNumber === 8 && (
        <div className="space-y-6">
          <Tabs
            tabs={[
              {
                id: "primary",
                label: "Monthly Attendance Summary (with NIS Days)",
                count: attendanceSummaries.length,
              },
              {
                id: "daily",
                label: "Daily Biometric & Mobile Punches",
                count: attendanceDays.length,
              },
            ]}
            activeTab={activeTab}
            onChange={setActiveTab}
          />

          {activeTab === "primary" && (
            <div className="space-y-4">
              <GlassCard className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-bold text-ink">
                    October 2026 Monthly Attendance Summary (Feeds Payroll & Statutory NIS)
                  </h3>
                  <p className="text-xs text-muted">
                    NIS Days = insurable days completed in the pay period (Present + Paid Leave + Paid Holidays; Unpaid/Absent excluded).
                  </p>
                </div>
                <Stepper
                  steps={["DRAFT", "CONFIRMED", "APPROVED"]}
                  currentStep={attendanceSummaries[0]?.status || "CONFIRMED"}
                />
              </GlassCard>

              <DataTable
                columns={[
                  { key: "employee_code", header: "Emp ID" },
                  { key: "employee_name", header: "Employee" },
                  { key: "department_name", header: "Department" },
                  { key: "salary_days", header: "Salary Days" },
                  { key: "present_days", header: "Present" },
                  { key: "weekend_days", header: "Weekend" },
                  { key: "absent_days", header: "Absent" },
                  { key: "late_days", header: "Late" },
                  { key: "paid_holidays", header: "Paid Holidays" },
                  { key: "paid_leave_days", header: "Paid Leave" },
                  {
                    key: "nis_days",
                    header: "NIS Days (Insurable)",
                    render: (r) => (
                      <span className="px-2.5 py-1 rounded-pill bg-indigo-600 text-white text-xs font-bold">
                        {r.nis_days} Days
                      </span>
                    ),
                  },
                  {
                    key: "status",
                    header: "Stage",
                    render: (r) => <StatusPill status={r.status} />,
                  },
                  {
                    key: "actions",
                    header: "Action",
                    render: (r) =>
                      r.status !== "APPROVED" ? (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() =>
                            handleAdvanceAttendanceSummary(r.id, r.nis_days)
                          }
                        >
                          Confirm & Approve
                        </Button>
                      ) : (
                        <span className="text-xs text-emerald-700 font-semibold">
                          Locked for Payroll
                        </span>
                      ),
                  },
                ]}
                data={attendanceSummaries}
              />
            </div>
          )}

          {activeTab === "daily" && (
            <DataTable
              columns={[
                { key: "work_date", header: "Date" },
                { key: "employee_code", header: "Emp ID" },
                { key: "employee_name", header: "Employee" },
                { key: "department_name", header: "Department" },
                { key: "shift_name", header: "Shift" },
                { key: "worked_hours", header: "Worked Hrs" },
                { key: "extra_hours", header: "OT Hrs" },
                { key: "source", header: "Source" },
                {
                  key: "within_geofence",
                  header: "Geofence",
                  render: (r) => (
                    <StatusPill
                      status={r.within_geofence ? "Within Geofence" : "Outside"}
                      tone={r.within_geofence ? "success" : "warning"}
                    />
                  ),
                },
                {
                  key: "status",
                  header: "Status",
                  render: (r) => <StatusPill status={r.status} />,
                },
              ]}
              data={attendanceDays}
            />
          )}
        </div>
      )}

      {/* MODULE 9: SHIFT & ROSTER */}
      {moduleNumber === 9 && (
        <div className="space-y-6">
          <DataTable
            columns={[
              { key: "code", header: "Shift Code" },
              { key: "name", header: "Shift Name" },
              { key: "start_time", header: "Start Time" },
              { key: "end_time", header: "End Time" },
              {
                key: "crosses_midnight",
                header: "Overnight Shift",
                render: (r) => (
                  <StatusPill
                    status={r.crosses_midnight ? "Crosses Midnight" : "Same Day"}
                    tone={r.crosses_midnight ? "warning" : "info"}
                  />
                ),
              },
              { key: "grace_minutes_late", header: "Late Grace (Mins)" },
            ]}
            data={shifts}
          />

          <DataTable
            columns={[
              { key: "name", header: "Roster Batch Name" },
              { key: "company_name", header: "Company" },
              { key: "shift_name", header: "Assigned Shift" },
              { key: "start_date", header: "Period Start" },
              { key: "end_date", header: "Period End" },
              { key: "employee_count", header: "Assigned Employees" },
              {
                key: "status",
                header: "Status",
                render: (r) => <StatusPill status={r.status} />,
              },
            ]}
            data={rosterBatches}
          />
        </div>
      )}

      {/* MODULE 10: LEAVE & APPEND-ONLY LEAVE LEDGER */}
      {moduleNumber === 10 && (
        <div className="space-y-6">
          <Tabs
            tabs={[
              { id: "primary", label: "List View", count: leaveRequests.length },
              { id: "kanban", label: "Kanban Board", count: leaveRequests.length },
              { id: "calendar", label: "Calendar View" },
              { id: "pivot", label: "Pivot Matrix" },
              { id: "ledger", label: "Append-Only Leave Balance Ledger", count: leaveLedger.length },
            ]}
            activeTab={activeTab}
            onChange={setActiveTab}
          />

          {activeTab === "kanban" && (
            <KanbanBoard
              columns={["SUBMITTED", "APPROVED", "REJECTED", "DRAFT"].map((st) => ({
                id: st,
                title: st,
                cards: leaveRequests
                  .filter((lr) => lr.status === st)
                  .map((lr) => ({
                    id: lr.id,
                    title: `${lr.employee_name} (${lr.leave_type_name})`,
                    subtitle: `${lr.start_date} → ${lr.end_date} (${lr.days_requested}d)`,
                    badge: lr.status,
                    meta: lr.reference_no,
                  })),
              }))}
            />
          )}

          {activeTab === "calendar" && (
            <CalendarGrid
              monthLabel="November 2026 Leave & Holiday Schedule"
              events={leaveRequests.map((lr, idx) => ({
                day: ((idx * 3 + 2) % 28) + 1,
                title: `${lr.employee_name} (${lr.leave_type_name})`,
                status: lr.status,
              }))}
            />
          )}

          {activeTab === "pivot" && (
            <PivotTable
              title="Leave Days Requested by Department × Leave Type"
              rowLabel="Department"
              columns={["Casual Leave", "Sick / Medical Leave", "Earned / Annual Leave", "Total Days"]}
              rows={Array.from(
                new Set(leaveRequests.map((r) => r.department_name || "General"))
              ).map((dept) => {
                const deptRows = leaveRequests.filter(
                  (r) => (r.department_name || "General") === dept
                );
                const sumByType = (tName: string) =>
                  deptRows
                    .filter((r) => r.leave_type_name === tName)
                    .reduce((acc, r) => acc + parseFloat(r.days_requested || "0"), 0);
                const c = sumByType("Casual Leave");
                const s = sumByType("Sick / Medical Leave");
                const e = sumByType("Earned / Annual Leave");
                return {
                  rowKey: dept,
                  values: {
                    "Casual Leave": c,
                    "Sick / Medical Leave": s,
                    "Earned / Annual Leave": e,
                    "Total Days": c + s + e,
                  },
                };
              })}
            />
          )}

          {activeTab === "primary" && (
            <DataTable
              columns={[
                { key: "reference_no", header: "Ref No" },
                { key: "employee_name", header: "Employee" },
                { key: "department_name", header: "Department" },
                { key: "leave_type_name", header: "Leave Type" },
                { key: "start_date", header: "From" },
                { key: "end_date", header: "To" },
                { key: "days_requested", header: "Days" },
                { key: "current_balance", header: "Ledger Balance" },
                {
                  key: "status",
                  header: "Status",
                  render: (r) => <StatusPill status={r.status} />,
                },
                {
                  key: "action",
                  header: "Manager Action",
                  render: (r) =>
                    r.status !== "APPROVED" ? (
                      <Button size="sm" onClick={() => handleApproveLeave(r.id)}>
                        Approve Leave
                      </Button>
                    ) : (
                      <span className="text-xs text-emerald-700 font-semibold">
                        Posted to Ledger
                      </span>
                    ),
                },
              ]}
              data={leaveRequests}
            />
          )}

          {activeTab === "ledger" && (
            <DataTable
              columns={[
                { key: "posted_on", header: "Posted Date" },
                { key: "employee_name", header: "Employee" },
                { key: "leave_type_name", header: "Leave Type" },
                { key: "source_type", header: "Ledger Entry Type" },
                {
                  key: "quantity",
                  header: "Days (+ Accrual / - Taken)",
                  render: (r) => (
                    <span
                      className={`font-bold ${
                        parseFloat(r.quantity) >= 0 ? "text-emerald-700" : "text-danger"
                      }`}
                    >
                      {r.quantity} d
                    </span>
                  ),
                },
                { key: "reason", header: "Reason (Immutable Entry)" },
              ]}
              data={leaveLedger}
            />
          )}
        </div>
      )}

      {/* MODULE 11, 12, 13: HOLIDAY CALENDAR, OVERTIME, FIELD DUTY */}
      {moduleNumber === 11 && (
        <DataTable
          columns={[
            { key: "date", header: "Date" },
            {
              key: "name",
              header: "Holiday Name (English & বাংলা)",
              render: (r) => (
                <div>
                  <div className="font-semibold">{r.name}</div>
                  <div className="text-xs text-muted">{r.name_bn}</div>
                </div>
              ),
            },
            {
              key: "holiday_type",
              header: "Category",
              render: (r) => <StatusPill status={r.holiday_type} />,
            },
            {
              key: "is_paid",
              header: "Payroll Impact",
              render: (r) => (
                <StatusPill status={r.is_paid ? "Paid Holiday (Counts in NIS)" : "Unpaid"} />
              ),
            },
          ]}
          data={holidays}
        />
      )}

      {moduleNumber === 12 && (
        <DataTable
          columns={[
            { key: "work_date", header: "Work Date" },
            { key: "employee_name", header: "Employee" },
            { key: "requested_hours", header: "Requested Hrs" },
            { key: "approved_hours", header: "Approved Hrs" },
            { key: "rate_multiplier", header: "Rate Multiplier" },
            { key: "reason", header: "Reason" },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={overtimeList}
        />
      )}

      {moduleNumber === 13 && (
        <DataTable
          columns={[
            { key: "work_date", header: "Date" },
            { key: "employee_name", header: "Employee" },
            { key: "movement_type", header: "Movement Type" },
            { key: "client_or_location", header: "Client / Field Location" },
            {
              key: "gps",
              header: "Check-In Coordinates",
              render: (r) => (
                <span className="text-xs font-mono">
                  {r.latitude}, {r.longitude}
                </span>
              ),
            },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={fieldMovements}
        />
      )}

      {/* MODULE 14: SALARY STRUCTURE */}
      {moduleNumber === 14 && (
        <div className="space-y-4">
          <StatutoryDisclaimerBanner text="Standard Bangladesh Salary Breakdown: Basic 50%, House Rent 25%, Medical 10%, Conveyance 10%, Entertainment 5% of Gross. Effective-dated: revisions add a new row." />
          <DataTable
            columns={[
              { key: "employee_code", header: "Emp ID" },
              { key: "employee_name", header: "Employee" },
              { key: "effective_from", header: "Effective From" },
              {
                key: "gross_amount",
                header: "Gross (100%)",
                render: (r) => <strong>{formatBDT(r.gross_amount, lakhGrouping)}</strong>,
              },
              {
                key: "basic_amount",
                header: "Basic (50%)",
                render: (r) => formatBDT(r.basic_amount, lakhGrouping),
              },
              {
                key: "house_rent_amount",
                header: "House Rent (25%)",
                render: (r) => formatBDT(r.house_rent_amount, lakhGrouping),
              },
              {
                key: "medical_amount",
                header: "Medical (10%)",
                render: (r) => formatBDT(r.medical_amount, lakhGrouping),
              },
              {
                key: "conveyance_amount",
                header: "Conveyance (10%)",
                render: (r) => formatBDT(r.conveyance_amount, lakhGrouping),
              },
              {
                key: "entertainment_amount",
                header: "Entertainment (5%)",
                render: (r) => formatBDT(r.entertainment_amount, lakhGrouping),
              },
            ]}
            data={salaryStructures}
          />
        </div>
      )}

      {/* MODULE 15 & 22: MONTHLY PAYROLL, PAYSLIPS & MONTHLY SALARY SHEET WITH TAKA IN WORDS */}
      {(moduleNumber === 15 || moduleNumber === 22) && (
        <div className="space-y-6">
          {payrollRuns[0] && (
            <GlassPanel className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-base font-bold text-ink">
                    Payroll Run: {payrollRuns[0].run_number} ({payrollRuns[0].period_name})
                  </h3>
                  <p className="text-xs text-ink-2">
                    Total Net Disbursement:{" "}
                    <strong className="text-primary">
                      {formatBDT(payrollRuns[0].total_net_bdt, lakhGrouping)}
                    </strong>{" "}
                    — <em>"{payrollRuns[0].total_net_in_words}"</em>
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Stepper
                    steps={["DRAFT", "VALIDATED", "APPROVED", "LOCKED"]}
                    currentStep={payrollRuns[0].status}
                  />
                  {payrollRuns[0].status !== "LOCKED" && (
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => handleLockPayrollRun(payrollRuns[0].id)}
                    >
                      <Lock className="w-3.5 h-3.5" />
                      <span>Lock Period</span>
                    </Button>
                  )}
                </div>
              </div>
            </GlassPanel>
          )}

          <GlassPanel className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-ink">
                Monthly Salary Sheet (Grouped by Department with NIS Days & Signature Blocks)
              </h3>
              <Button variant="ghost" size="sm" onClick={() => window.print()}>
                <Printer className="w-3.5 h-3.5" />
                <span>Print Salary Sheet / PDF</span>
              </Button>
            </div>

            <DataTable
              columns={[
                { key: "payslip_number", header: "Payslip No" },
                { key: "employee_code", header: "Emp ID" },
                { key: "employee_name", header: "Employee" },
                { key: "department_name", header: "Department" },
                { key: "nis_days", header: "NIS Days" },
                {
                  key: "basic_bdt",
                  header: "Basic",
                  render: (r) => formatBDT(r.basic_bdt, lakhGrouping),
                },
                {
                  key: "house_rent_bdt",
                  header: "House Rent",
                  render: (r) => formatBDT(r.house_rent_bdt, lakhGrouping),
                },
                {
                  key: "gross_bdt",
                  header: "Gross",
                  render: (r) => formatBDT(r.gross_bdt, lakhGrouping),
                },
                {
                  key: "pf_employee_bdt",
                  header: "PF (2.5%)",
                  render: (r) => formatBDT(r.pf_employee_bdt, lakhGrouping),
                },
                {
                  key: "nis_employee_bdt",
                  header: "NIS Ded.",
                  render: (r) => formatBDT(r.nis_employee_bdt, lakhGrouping),
                },
                {
                  key: "ait_tax_bdt",
                  header: "AIT Tax",
                  render: (r) => formatBDT(r.ait_tax_bdt, lakhGrouping),
                },
                {
                  key: "revenue_stamp_bdt",
                  header: "Stamp",
                  render: (r) => formatBDT(r.revenue_stamp_bdt, lakhGrouping),
                },
                {
                  key: "net_bdt",
                  header: "Net Payable",
                  render: (r) => (
                    <strong className="text-primary">
                      {formatBDT(r.net_bdt, lakhGrouping)}
                    </strong>
                  ),
                },
                {
                  key: "view",
                  header: "Payslip",
                  render: (r) => (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setSelectedPayslip(r)}
                    >
                      View PDF
                    </Button>
                  ),
                },
              ]}
              data={payslips}
            />

            {payrollRuns[0] && (
              <div className="p-4 rounded-control bg-indigo-50/80 border border-indigo-200 text-xs font-semibold text-ink">
                Total Net Payable in Words (Taka):{" "}
                <span className="text-primary">{payrollRuns[0].total_net_in_words}</span>
              </div>
            )}

            <SignatureBlock />
          </GlassPanel>
        </div>
      )}

      {/* MODULE 16, 17, 18, 19, 20, 21 */}
      {moduleNumber === 16 && (
        <DataTable
          columns={[
            { key: "name", header: "Bonus Batch Name" },
            { key: "bonus_type", header: "Type" },
            { key: "effective_date", header: "Payout Date" },
            { key: "pct_of_basic", header: "% of Basic" },
            {
              key: "total_amount_bdt",
              header: "Total Bonus Pool",
              render: (r) => formatBDT(r.total_amount_bdt, lakhGrouping),
            },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={bonuses}
        />
      )}

      {moduleNumber === 17 && (
        <DataTable
          columns={[
            { key: "reference_no", header: "Claim Ref" },
            { key: "employee_name", header: "Employee" },
            { key: "category", header: "Category" },
            { key: "claim_date", header: "Claim Date" },
            {
              key: "amount_bdt",
              header: "Amount",
              render: (r) => formatBDT(r.amount_bdt, lakhGrouping),
            },
            { key: "description", header: "Description" },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={expenses}
        />
      )}

      {moduleNumber === 18 && (
        <DataTable
          columns={[
            { key: "loan_number", header: "Loan No" },
            { key: "employee_name", header: "Employee" },
            { key: "loan_type", header: "Type" },
            {
              key: "principal_bdt",
              header: "Principal",
              render: (r) => formatBDT(r.principal_bdt, lakhGrouping),
            },
            {
              key: "monthly_installment_bdt",
              header: "Monthly Installment",
              render: (r) => formatBDT(r.monthly_installment_bdt, lakhGrouping),
            },
            {
              key: "outstanding_balance_bdt",
              header: "Ledger Balance",
              render: (r) => (
                <strong className="text-primary">
                  {formatBDT(r.outstanding_balance_bdt, lakhGrouping)}
                </strong>
              ),
            },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={loans}
        />
      )}

      {moduleNumber === 19 && (
        <DataTable
          columns={[
            { key: "posted_on", header: "Posted Date" },
            { key: "employee_name", header: "Employee" },
            { key: "contribution_type", header: "Contribution Type" },
            {
              key: "amount",
              header: "Amount (BDT)",
              render: (r) => formatBDT(r.amount, lakhGrouping),
            },
            { key: "reason", header: "Ledger Narrative" },
          ]}
          data={pfLedger}
        />
      )}

      {moduleNumber === 20 && (
        <div className="space-y-6">
          <StatutoryDisclaimerBanner />
          <DataTable
            columns={[
              { key: "code", header: "Scheme Code" },
              { key: "name", header: "Statutory Social Security Scheme" },
              { key: "employee_rate_pct", header: "Employee Rate (%)" },
              { key: "employer_rate_pct", header: "Employer Rate (%)" },
              {
                key: "wage_ceiling_bdt",
                header: "Wage Ceiling",
                render: (r) => formatBDT(r.wage_ceiling_bdt, lakhGrouping),
              },
              { key: "review_flag", header: "Compliance Flag" },
            ]}
            data={statutorySchemes}
          />
          <DataTable
            columns={[
              { key: "income_year", header: "Income Year" },
              { key: "slab_order", header: "Slab Order" },
              {
                key: "threshold_amount_bdt",
                header: "Threshold (BDT)",
                render: (r) => formatBDT(r.threshold_amount_bdt, lakhGrouping),
              },
              { key: "tax_rate_pct", header: "Tax Rate (%)" },
              { key: "review_flag", header: "Compliance Notice" },
            ]}
            data={taxSlabs}
          />
        </div>
      )}

      {moduleNumber === 21 && (
        <DataTable
          columns={[
            { key: "batch_number", header: "Batch No" },
            { key: "run_number", header: "Payroll Run" },
            { key: "payout_channel", header: "Payout Format (BEFTN / bKash / Nagad)" },
            { key: "bank_or_mfs_name", header: "Bank / MFS Institution" },
            { key: "record_count", header: "Payees" },
            {
              key: "total_amount_bdt",
              header: "Total Disbursement",
              render: (r) => formatBDT(r.total_amount_bdt, lakhGrouping),
            },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={paymentBatches}
        />
      )}

      {/* MODULE 4, 5, 6, 7, 23, 24, 25: TALENT LIFECYCLE */}
      {moduleNumber === 4 && (
        <DataTable
          columns={[
            { key: "department_name", header: "Department" },
            { key: "fiscal_year", header: "Fiscal Year" },
            { key: "approved_headcount", header: "Approved Headcount" },
            { key: "current_headcount", header: "Current Headcount" },
            { key: "open_vacancies", header: "Open Vacancies" },
            {
              key: "annual_budget_bdt",
              header: "Staffing Budget",
              render: (r) => formatBDT(r.annual_budget_bdt, lakhGrouping),
            },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={manpowerPlans}
        />
      )}

      {moduleNumber === 5 && (
        <KanbanBoard
          columns={["APPLIED", "SCREENING", "INTERVIEW", "OFFERED"].map((stage) => ({
            id: stage,
            title: stage,
            cards: applicants
              .filter((a) => a.stage === stage)
              .map((a) => ({
                id: a.id,
                title: `${a.full_name} (${a.full_name_bn})`,
                subtitle: a.requisition_title,
                badge: a.stage,
                meta: `Score: ${a.evaluation_score}% • ${formatBDT(a.expected_salary_bdt, lakhGrouping)}`,
              })),
          }))}
        />
      )}

      {moduleNumber === 6 && (
        <DataTable
          columns={[
            { key: "employee_name", header: "New Joiner" },
            { key: "template_name", header: "Checklist Template" },
            {
              key: "completion_pct",
              header: "Readiness",
              render: (r) => <strong>{r.completion_pct}% Completed</strong>,
            },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={onboardingList}
        />
      )}

      {moduleNumber === 7 && (
        <DataTable
          columns={[
            { key: "employee_name", header: "Employee" },
            { key: "probation_end_date", header: "Probation End Date" },
            { key: "supervisor_rating", header: "Supervisor Score (Out of 5)" },
            { key: "recommendation", header: "Recommendation" },
            { key: "remarks", header: "Evaluation Notes" },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={probationList}
        />
      )}

      {moduleNumber === 23 && (
        <div className="space-y-4">
          <GlassCard className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase text-ink-2">
              Performance Appraisal & 360° Feedback Cycle
            </span>
            <Stepper
              steps={["TO_CONFIRM", "CONFIRMED", "DONE"]}
              currentStep={appraisals[0]?.stage || "CONFIRMED"}
            />
          </GlassCard>
          <DataTable
            columns={[
              { key: "employee_name", header: "Employee" },
              { key: "department_name", header: "Department" },
              { key: "review_cycle", header: "Review Cycle" },
              { key: "self_score", header: "Self Score" },
              { key: "manager_score", header: "Manager Score" },
              { key: "peer_360_score", header: "360° Peer Score" },
              { key: "final_rating", header: "Final Rating" },
              { key: "stage", header: "Stage", render: (r) => <StatusPill status={r.stage} /> },
            ]}
            data={appraisals}
          />
        </div>
      )}

      {moduleNumber === 24 && (
        <DataTable
          columns={[
            { key: "employee_name", header: "Employee" },
            { key: "movement_type", header: "Movement Type" },
            { key: "new_designation_title", header: "New Designation" },
            { key: "effective_from", header: "Effective Date" },
            {
              key: "previous_gross_bdt",
              header: "Previous Gross",
              render: (r) => formatBDT(r.previous_gross_bdt, lakhGrouping),
            },
            {
              key: "revised_gross_bdt",
              header: "Revised Gross",
              render: (r) => (
                <strong className="text-primary">
                  {formatBDT(r.revised_gross_bdt, lakhGrouping)}
                </strong>
              ),
            },
            { key: "change_reason", header: "Reason" },
          ]}
          data={careerMovements}
        />
      )}

      {moduleNumber === 25 && (
        <DataTable
          columns={[
            { key: "title", header: "Training Program" },
            { key: "category", header: "Category" },
            { key: "trainer_or_institute", header: "Institute" },
            { key: "start_date", header: "Start Date" },
            { key: "enrolled_count", header: "Nominees" },
            {
              key: "cost_bdt",
              header: "Budget",
              render: (r) => formatBDT(r.cost_bdt, lakhGrouping),
            },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={trainings}
        />
      )}

      {/* MODULE 26, 27, 28, 29, 30, 31, 34: RELATIONS, ASSETS, EXIT & HELPDESK */}
      {moduleNumber === 26 && (
        <DataTable
          columns={[
            { key: "case_number", header: "Case No" },
            { key: "complainant_name", header: "Complainant" },
            { key: "handler_name", header: "Assigned Handler (Confidential)" },
            { key: "category", header: "Category" },
            { key: "resolution_summary", header: "Resolution Notes" },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={grievances}
        />
      )}

      {moduleNumber === 27 && (
        <DataTable
          columns={[
            { key: "case_number", header: "Case No (Restricted)" },
            { key: "employee_name", header: "Employee" },
            { key: "incident_date", header: "Incident Date" },
            { key: "allegation_summary", header: "Allegation / Show-Cause" },
            { key: "action_taken", header: "Decision" },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={disciplinaryList}
        />
      )}

      {moduleNumber === 28 && (
        <DataTable
          columns={[
            { key: "asset_tag", header: "Asset Tag" },
            { key: "name", header: "Asset Name" },
            { key: "category", header: "Category" },
            { key: "serial_number", header: "Serial No" },
            { key: "assigned_to_name", header: "Custodian Employee" },
            {
              key: "value_bdt",
              header: "Book Value",
              render: (r) => formatBDT(r.value_bdt, lakhGrouping),
            },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={assets}
        />
      )}

      {moduleNumber === 29 && (
        <DataTable
          columns={[
            { key: "employee_name", header: "Employee" },
            { key: "record_type", header: "Checkup / Safety Event" },
            { key: "incident_or_checkup_date", header: "Date" },
            {
              key: "medical_notes_display",
              header: "Restricted Medical Notes (Encrypted)",
            },
            { key: "corrective_action", header: "Corrective / Welfare Action" },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={healthRecords}
        />
      )}

      {moduleNumber === 30 && (
        <DataTable
          columns={[
            { key: "employee_name", header: "Employee" },
            { key: "notice_given_date", header: "Notice Date" },
            { key: "last_working_day", header: "Last Working Day" },
            { key: "notice_period_days", header: "Notice Period (Days)" },
            { key: "reason", header: "Exit Reason" },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={resignations}
        />
      )}

      {moduleNumber === 31 && (
        <DataTable
          columns={[
            { key: "employee_name", header: "Separating Employee" },
            {
              key: "unpaid_salary_bdt",
              header: "Unpaid Salary",
              render: (r) => formatBDT(r.unpaid_salary_bdt, lakhGrouping),
            },
            {
              key: "leave_encashment_bdt",
              header: "Leave Encashment",
              render: (r) => formatBDT(r.leave_encashment_bdt, lakhGrouping),
            },
            {
              key: "pf_and_gratuity_bdt",
              header: "PF & Gratuity",
              render: (r) => formatBDT(r.pf_and_gratuity_bdt, lakhGrouping),
            },
            {
              key: "net_settlement_bdt",
              header: "Net Final Settlement",
              render: (r) => (
                <strong className="text-primary">
                  {formatBDT(r.net_settlement_bdt, lakhGrouping)}
                </strong>
              ),
            },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={settlements}
        />
      )}

      {moduleNumber === 34 && (
        <DataTable
          columns={[
            { key: "ticket_number", header: "Ticket No" },
            { key: "requester_name", header: "Requester" },
            { key: "category", header: "Category" },
            { key: "subject", header: "Subject" },
            { key: "priority", header: "Priority" },
            { key: "sla_hours", header: "SLA Target (Hrs)" },
            { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
          data={tickets}
        />
      )}

      {/* MODULE 32 & 33: EMPLOYEE SELF-SERVICE (MOBILE PWA) & MANAGER SELF-SERVICE */}
      {(moduleNumber === 32 || moduleNumber === 33) && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <GlassCard className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase text-ink-2">
                  Mobile Geofence Check-In / Out
                </span>
                <StatusPill status="Inside Office Area" tone="success" />
              </div>
              <p className="text-xs text-ink-2 flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-primary" />
                <span>Gulshan Corporate HQ (9:00 AM - 6:00 PM Shift)</span>
              </p>
              <div className="flex items-center gap-2 pt-1">
                <Button
                  className="flex-1"
                  onClick={() => handleMobileCheckIn("IN")}
                >
                  Check In Now
                </Button>
                <Button
                  variant="secondary"
                  className="flex-1"
                  onClick={() => handleMobileCheckIn("OUT")}
                >
                  Check Out
                </Button>
              </div>
            </GlassCard>

            <GlassCard className="space-y-2">
              <span className="text-xs font-bold uppercase text-ink-2">
                Leave Balance Utilization
              </span>
              <div className="text-2xl font-bold text-ink">
                16 / 18 Days Available
              </div>
              <div className="w-full h-2.5 rounded-pill bg-slate-200 overflow-hidden">
                <div className="h-full bg-primary w-4/5 rounded-pill" />
              </div>
              <p className="text-xs text-muted">
                Casual: 8d left • Sick: 14d left • Earned: 18d left
              </p>
            </GlassCard>

            <GlassCard className="space-y-2">
              <span className="text-xs font-bold uppercase text-ink-2">
                Latest Payslip & PF Statement
              </span>
              <div className="text-2xl font-bold text-primary">
                {payslips[0]
                  ? formatBDT(payslips[0].net_bdt, lakhGrouping)
                  : "৳ 42,500.00"}
              </div>
              <p className="text-xs text-muted">
                October 2026 • Paid via BRAC Bank BEFTN
              </p>
              {payslips[0] && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setSelectedPayslip(payslips[0])}
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Payslip PDF</span>
                </Button>
              )}
            </GlassCard>
          </div>

          <DataTable
            columns={[
              { key: "work_date", header: "Date" },
              { key: "employee_name", header: "Employee" },
              { key: "worked_hours", header: "Worked Hrs" },
              { key: "source", header: "Source" },
              {
                key: "within_geofence",
                header: "Geofence Badge",
                render: (r) => (
                  <StatusPill
                    status={r.within_geofence ? "Within Geofence" : "Remote"}
                  />
                ),
              },
              { key: "status", header: "Status", render: (r) => <StatusPill status={r.status} /> },
            ]}
            data={attendanceDays}
          />
        </div>
      )}

      {/* MODULE 35, 36, 37, 38, 39, 40, 41, 42 */}
      {moduleNumber === 35 && (
        <div className="space-y-6">
          <DataTable
            columns={[
              { key: "title", header: "Policy Title" },
              { key: "title_bn", header: "বাংলা শিরোনাম" },
              { key: "category", header: "Category" },
              { key: "version", header: "Version" },
              { key: "effective_date", header: "Effective Date" },
              { key: "acknowledged_count", header: "Employee Acknowledgments" },
            ]}
            data={policies}
          />
          <DataTable
            columns={[
              { key: "reference_no", header: "Letter Ref No" },
              { key: "employee_name", header: "Employee" },
              { key: "template_name", header: "Template" },
              { key: "template_version", header: "Template Version" },
              { key: "rendered_html", header: "Rendered Letter Snapshot" },
            ]}
            data={letters}
          />
        </div>
      )}

      {moduleNumber === 36 && (
        <DataTable
          columns={[
            { key: "title", header: "Announcement Title" },
            { key: "title_bn", header: "বাংলা শিরোনাম" },
            { key: "category", header: "Category" },
            { key: "body", header: "Notice Content" },
            { key: "published_at", header: "Published At" },
          ]}
          data={announcements}
        />
      )}

      {moduleNumber === 37 && (
        <DataTable
          columns={[
            { key: "title", header: "Approval Subject" },
            { key: "subject_type", header: "Entity Type" },
            { key: "requester_name", header: "Requester" },
            {
              key: "step",
              header: "Workflow Step",
              render: (r) => `Step ${r.current_step} of ${r.total_steps}`,
            },
            {
              key: "status",
              header: "Status",
              render: (r) => <StatusPill status={r.status} />,
            },
            {
              key: "actions",
              header: "Decision (Mandatory Rejection Reason)",
              render: (r) =>
                r.status !== "APPROVED" && r.status !== "REJECTED" ? (
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      onClick={() =>
                        handleWorkflowDecision(
                          r.id,
                          "APPROVED",
                          "Approved via Workflow Inbox"
                        )
                      }
                    >
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => setRejectModalApproval(r)}
                    >
                      Reject
                    </Button>
                  </div>
                ) : (
                  <span className="text-xs text-muted">
                    {r.rejection_reason || "Completed"}
                  </span>
                ),
            },
          ]}
          data={approvals}
        />
      )}

      {moduleNumber === 38 && (
        <DataTable
          columns={[
            { key: "code", header: "Report Code" },
            { key: "name", header: "Report Definition" },
            { key: "category", header: "Category" },
            { key: "schedule_cron", header: "Scheduled Email Cron" },
            {
              key: "export",
              header: "Export Formats",
              render: (r) => (
                <div className="flex gap-2">
                  <Button size="sm" variant="ghost" onClick={() => window.print()}>
                    PDF
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={async () => {
                      try {
                        await apiDownloadFile(
                          `/reports/definitions/${r.id}/export-xlsx/`,
                          `${r.code || "report"}.xlsx`
                        );
                        notify("Excel (.xlsx) report downloaded via openpyxl!");
                      } catch (err: any) {
                        notify(err.message);
                      }
                    }}
                  >
                    Excel (.xlsx)
                  </Button>
                </div>
              ),
            },
          ]}
          data={reports}
        />
      )}

      {moduleNumber === 39 && (
        <div className="space-y-6">
          <DataTable
            columns={[
              { key: "name", header: "Role Name" },
              { key: "code", header: "Role Code" },
              { key: "description", header: "Description" },
              {
                key: "can_view_confidential_salary",
                header: "Salary Confidentiality",
                render: (r) => (
                  <StatusPill
                    status={r.can_view_confidential_salary ? "Permitted" : "Masked"}
                  />
                ),
              },
              {
                key: "has_approval_authority",
                header: "Approval Authority (Separate)",
                render: (r) => (
                  <StatusPill
                    status={r.has_approval_authority ? "Approver" : "View/Edit Only"}
                  />
                ),
              },
            ]}
            data={rolesList}
          />
          <DataTable
            columns={[
              { key: "full_name", header: "User Name" },
              { key: "email", header: "Email" },
              { key: "experience_mode", header: "Experience Mode" },
              { key: "default_company_name", header: "Default Company" },
              {
                key: "can_view_salary",
                header: "Salary Access",
                render: (r) => (
                  <StatusPill status={r.can_view_salary ? "Allowed" : "Masked"} />
                ),
              },
            ]}
            data={usersList}
          />
        </div>
      )}

      {moduleNumber === 40 && (
        <DataTable
          columns={[
            { key: "created_at", header: "Timestamp (UTC)" },
            { key: "actor_email", header: "Actor" },
            { key: "action", header: "Action" },
            { key: "entity", header: "Entity" },
            { key: "entity_id", header: "Entity UUID" },
            {
              key: "new_values",
              header: "Immutable Snapshot",
              render: (r) => (
                <code className="text-[11px] font-mono text-ink-2">
                  {JSON.stringify(r.new_values)}
                </code>
              ),
            },
          ]}
          data={auditLogs}
        />
      )}

      {moduleNumber === 41 && (
        <div className="space-y-6">
          <GlassCard className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-ink flex items-center gap-2">
                <Key className="w-4 h-4 text-primary" />
                <span>External Software API Keys & Outbound HMAC-SHA256 Webhooks</span>
              </h3>
              <p className="text-xs text-muted">
                Keys are SHA-256 hashed at rest, scoped by module, and shown only once upon creation.
              </p>
            </div>
            <Button size="sm" onClick={handleGenerateApiKey}>
              Generate Scoped API Key
            </Button>
          </GlassCard>

          {newRawKey && (
            <div className="p-4 rounded-card bg-emerald-500/15 border border-emerald-500/40 text-xs space-y-1">
              <div className="font-bold text-emerald-950">
                Copy your new API key now — it will never be shown again:
              </div>
              <code className="block p-2 bg-white rounded font-mono text-sm font-bold text-primary select-all">
                {newRawKey}
              </code>
            </div>
          )}

          <DataTable
            columns={[
              { key: "name", header: "API Key Name" },
              { key: "key_prefix", header: "Prefix" },
              {
                key: "scopes",
                header: "Scopes",
                render: (r) => (r.scopes || []).join(", "),
              },
              {
                key: "is_active",
                header: "Status",
                render: (r) => (
                  <StatusPill status={r.is_active ? "ACTIVE" : "REVOKED"} />
                ),
              },
            ]}
            data={apiKeys}
          />

          <DataTable
            columns={[
              { key: "name", header: "Webhook Endpoint" },
              { key: "target_url", header: "HTTPS Target URL (SSRF Protected)" },
              {
                key: "events",
                header: "Subscribed Events",
                render: (r) => (r.events || []).join(", "),
              },
              {
                key: "is_active",
                header: "Status",
                render: (r) => <StatusPill status={r.is_active ? "ACTIVE" : "DISABLED"} />,
              },
            ]}
            data={webhooks}
          />

          <DataTable
            columns={[
              { key: "connector_code", header: "Adapter Code" },
              { key: "name", header: "Connector Name" },
              { key: "schedule_cron", header: "Schedule" },
              { key: "last_run_status", header: "Last Status", render: (r) => <StatusPill status={r.last_run_status} /> },
            ]}
            data={connectors}
          />
        </div>
      )}

      {moduleNumber === 42 && (
        <div className="space-y-6">
          <StatutoryDisclaimerBanner />
          <DataTable
            columns={[
              { key: "pf_employee_rate_pct", header: "PF Employee (%)" },
              { key: "pf_employer_rate_pct", header: "PF Employer (%)" },
              { key: "revenue_stamp_bdt", header: "Revenue Stamp (BDT)" },
              { key: "audit_retention_days", header: "Audit Retention (Days)" },
              { key: "statutory_disclaimer", header: "Statutory Review Flag" },
            ]}
            data={tenantSettings}
          />
          <DataTable
            columns={[
              { key: "company_name", header: "Company" },
              { key: "code", header: "Sequence Type" },
              { key: "prefix", header: "Prefix" },
              { key: "padding", header: "Zero Padding" },
              { key: "next_val", header: "Next Sequence Number" },
            ]}
            data={numberSequences}
          />
        </div>
      )}

      {/* Mandatory Rejection Reason Modal (Module 37) */}
      <Modal
        open={Boolean(rejectModalApproval)}
        title="Reject Approval Request (Mandatory Reason)"
        onClose={() => setRejectModalApproval(null)}
      >
        <div className="space-y-4">
          <p className="text-xs text-ink-2">
            Per <code>docs/02-architecture-and-database.md</code>, rejecting a workflow request requires a mandatory reason recorded in the append-only decision log.
          </p>
          <Input
            label="Rejection Reason"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Explain why this request is being declined..."
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setRejectModalApproval(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              disabled={!rejectReason.trim()}
              onClick={() =>
                handleWorkflowDecision(
                  rejectModalApproval.id,
                  "REJECTED",
                  rejectReason
                )
              }
            >
              Confirm Rejection
            </Button>
          </div>
        </div>
      </Modal>

      {/* Printable Payslip Modal (Module 22 & 32) */}
      <Modal
        open={Boolean(selectedPayslip)}
        title={`Payslip ${selectedPayslip?.payslip_number || ""}`}
        onClose={() => setSelectedPayslip(null)}
      >
        {selectedPayslip && (
          <div className="space-y-4 text-xs">
            <div className="flex justify-between border-b border-slate-200 pb-3">
              <div>
                <div className="font-bold text-sm text-ink">
                  {selectedPayslip.employee_name} ({selectedPayslip.employee_code})
                </div>
                <div className="text-muted">
                  {selectedPayslip.designation_title} • {selectedPayslip.department_name}
                </div>
              </div>
              <StatusPill status={selectedPayslip.status} />
            </div>

            <div className="grid grid-cols-2 gap-3 bg-white/80 p-3 rounded-control border border-slate-200">
              <div>
                <div className="font-bold text-ink mb-1">Earnings</div>
                <div className="flex justify-between">
                  <span>Basic (50%):</span>
                  <span>{formatBDT(selectedPayslip.basic_bdt, lakhGrouping)}</span>
                </div>
                <div className="flex justify-between">
                  <span>House Rent (25%):</span>
                  <span>{formatBDT(selectedPayslip.house_rent_bdt, lakhGrouping)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Medical (10%):</span>
                  <span>{formatBDT(selectedPayslip.medical_bdt, lakhGrouping)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Conveyance (10%):</span>
                  <span>{formatBDT(selectedPayslip.conveyance_bdt, lakhGrouping)}</span>
                </div>
                <div className="flex justify-between font-bold border-t mt-1 pt-1">
                  <span>Gross Salary:</span>
                  <span>{formatBDT(selectedPayslip.gross_bdt, lakhGrouping)}</span>
                </div>
              </div>

              <div>
                <div className="font-bold text-ink mb-1">
                  Deductions (NIS Days: {selectedPayslip.nis_days})
                </div>
                <div className="flex justify-between">
                  <span>Provident Fund (2.5%):</span>
                  <span>{formatBDT(selectedPayslip.pf_employee_bdt, lakhGrouping)}</span>
                </div>
                <div className="flex justify-between">
                  <span>NIS Contribution:</span>
                  <span>{formatBDT(selectedPayslip.nis_employee_bdt, lakhGrouping)}</span>
                </div>
                <div className="flex justify-between">
                  <span>AIT Tax Withholding:</span>
                  <span>{formatBDT(selectedPayslip.ait_tax_bdt, lakhGrouping)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Revenue Stamp:</span>
                  <span>{formatBDT(selectedPayslip.revenue_stamp_bdt, lakhGrouping)}</span>
                </div>
                <div className="flex justify-between font-bold border-t mt-1 pt-1">
                  <span>Total Deductions:</span>
                  <span>{formatBDT(selectedPayslip.total_deductions_bdt, lakhGrouping)}</span>
                </div>
              </div>
            </div>

            <div className="p-3 rounded-control bg-indigo-50 border border-indigo-200">
              <div className="flex justify-between text-sm font-bold text-primary">
                <span>Net Payable Salary:</span>
                <span>{formatBDT(selectedPayslip.net_bdt, lakhGrouping)}</span>
              </div>
              <div className="text-[11px] text-ink-2 mt-1">
                In Words: <strong>{selectedPayslip.net_in_words}</strong>
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button
                variant="secondary"
                onClick={async () => {
                  try {
                    await apiDownloadFile(
                      `/payroll/payslips/${selectedPayslip.id}/pdf/`,
                      `${selectedPayslip.payslip_number}.pdf`
                    );
                    notify("Payslip PDF downloaded via ReportLab!");
                  } catch (err: any) {
                    notify(err.message);
                  }
                }}
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download PDF</span>
              </Button>
              <Button variant="ghost" onClick={() => window.print()}>
                <Printer className="w-3.5 h-3.5" />
                <span>Print</span>
              </Button>
              <Button onClick={() => setSelectedPayslip(null)}>Done</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Module-Aware Create Drawer */}
      <ModuleCreateDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        moduleNumber={moduleNumber}
        moduleName={mod.name}
        activeTab={activeTab}
        activeCompanyId={activeCompanyId}
        employees={employees}
        companies={companies}
        branches={branches}
        departments={departments}
        onSuccess={(message, undoDeleteUrl) => {
          if (undoDeleteUrl) {
            setUndoAction(() => async () => {
              await apiFetch(undoDeleteUrl, { method: "DELETE" });
              loadModuleData();
            });
          } else {
            setUndoAction(null);
          }
          notify(message);
          loadModuleData();
        }}
      />
    </div>
  );
};
