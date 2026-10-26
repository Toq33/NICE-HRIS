import React, { useEffect, useState } from "react";
import { Button, Drawer, Input, Select } from "./glass";
import { apiFetch } from "../lib/api";

interface FieldDef {
  key: string;
  label: string;
  type?: "text" | "number" | "date" | "time" | "email" | "select";
  placeholder?: string;
  defaultValue?: string;
  options?: { value: string; label: string }[];
  required?: boolean;
}

interface ModuleCreateDrawerProps {
  open: boolean;
  onClose: () => void;
  moduleNumber: number;
  moduleName: string;
  activeTab: string;
  activeCompanyId: string | null;
  employees: any[];
  companies: any[];
  branches: any[];
  departments: any[];
  onSuccess: (message: string, undoDeleteUrl?: string) => void;
}

export const ModuleCreateDrawer: React.FC<ModuleCreateDrawerProps> = ({
  open,
  onClose,
  moduleNumber,
  moduleName,
  activeTab,
  activeCompanyId,
  employees,
  companies,
  branches,
  departments,
  onSuccess,
}) => {
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [auxData, setAuxData] = useState<{
    employees: any[];
    companies: any[];
    branches: any[];
    departments: any[];
    leaveTypes: any[];
    designations: any[];
    calendars: any[];
    requisitions: any[];
    payrollRuns: any[];
    workflows: any[];
  }>({
    employees: [],
    companies: [],
    branches: [],
    departments: [],
    leaveTypes: [],
    designations: [],
    calendars: [],
    requisitions: [],
    payrollRuns: [],
    workflows: [],
  });

  const unwrap = (res: any) => (Array.isArray(res) ? res : res?.results || []);

  useEffect(() => {
    if (!open) return;
    setError(null);
    (async () => {
      try {
        const [emps, comps, brs, depts, lt, des, cal, reqs, runs, wfs] =
          await Promise.all([
            employees.length > 0
              ? Promise.resolve(employees)
              : apiFetch("/employees/"),
            companies.length > 0
              ? Promise.resolve(companies)
              : apiFetch("/organization/companies/"),
            branches.length > 0
              ? Promise.resolve(branches)
              : apiFetch("/organization/branches/"),
            departments.length > 0
              ? Promise.resolve(departments)
              : apiFetch("/organization/departments/"),
            moduleNumber === 10 || moduleNumber === 32 || moduleNumber === 33
              ? apiFetch("/time/leave-types/")
              : Promise.resolve([]),
            moduleNumber === 3 || moduleNumber === 24
              ? apiFetch("/organization/designations/")
              : Promise.resolve([]),
            moduleNumber === 11
              ? apiFetch("/time/calendars/")
              : Promise.resolve([]),
            moduleNumber === 5
              ? apiFetch("/talent/requisitions/")
              : Promise.resolve([]),
            moduleNumber === 21
              ? apiFetch("/payroll/runs/")
              : Promise.resolve([]),
            moduleNumber === 1 || moduleNumber === 37
              ? apiFetch("/workflows/definitions/")
              : Promise.resolve([]),
          ]);
        setAuxData({
          employees: unwrap(emps),
          companies: unwrap(comps),
          branches: unwrap(brs),
          departments: unwrap(depts),
          leaveTypes: unwrap(lt),
          designations: unwrap(des),
          calendars: unwrap(cal),
          requisitions: unwrap(reqs),
          payrollRuns: unwrap(runs),
          workflows: unwrap(wfs),
        });
      } catch {
        // Ignore auxiliary fetch errors
      }
    })();
  }, [open, moduleNumber]);

  const effectiveEmployees =
    employees.length > 0 ? employees : auxData.employees;
  const effectiveCompanies =
    companies.length > 0 ? companies : auxData.companies;
  const effectiveBranches =
    branches.length > 0 ? branches : auxData.branches;
  const effectiveDepartments =
    departments.length > 0 ? departments : auxData.departments;

  const empOptions = effectiveEmployees.map((e) => ({
    value: String(e.id),
    label: `${e.full_name} (${e.employee_code})`,
  }));
  const deptOptions = effectiveDepartments.map((d) => ({
    value: String(d.id),
    label: `${d.name} (${d.code})`,
  }));
  const branchOptions = effectiveBranches.map((b) => ({
    value: String(b.id),
    label: `${b.name} (${b.code})`,
  }));
  const desigOptions = auxData.designations.map((d) => ({
    value: String(d.id),
    label: `${d.title} (${d.code})`,
  }));
  const leaveTypeOptions = auxData.leaveTypes.map((lt) => ({
    value: String(lt.id),
    label: `${lt.name} (${lt.code})`,
  }));

  const defaultEmpId = effectiveEmployees[0]?.id
    ? String(effectiveEmployees[0].id)
    : "";
  const defaultBranchId =
    effectiveBranches[0]?.id
      ? String(effectiveBranches[0].id)
      : effectiveEmployees[0]?.branch
      ? String(effectiveEmployees[0].branch)
      : "";
  const defaultDeptId =
    effectiveDepartments[0]?.id
      ? String(effectiveDepartments[0].id)
      : effectiveEmployees[0]?.department
      ? String(effectiveEmployees[0].department)
      : "";
  const defaultDesigId =
    auxData.designations[0]?.id
      ? String(auxData.designations[0].id)
      : effectiveEmployees[0]?.designation
      ? String(effectiveEmployees[0].designation)
      : "";
  const defaultCompanyId =
    activeCompanyId ||
    (effectiveCompanies[0]?.id ? String(effectiveCompanies[0].id) : "") ||
    (effectiveEmployees[0]?.company ? String(effectiveEmployees[0].company) : "");

  const getSchema = (): {
    title: string;
    endpoint: string;
    fields: FieldDef[];
    buildPayload: (v: Record<string, string>) => Record<string, any>;
  } => {
    // MODULE 2: COMPANY & ORGANIZATION
    if (moduleNumber === 2) {
      if (activeTab === "companies") {
        return {
          title: "Add Legal Entity / Company (Module 2)",
          endpoint: "/organization/companies/",
          fields: [
            { key: "code", label: "Entity Code", placeholder: "e.g. JACL", required: true },
            { key: "name", label: "Company Name (English)", placeholder: "e.g. Jamuna Apparel Co. Ltd.", required: true },
            { key: "name_bn", label: "কোম্পানির নাম (বাংলা)", placeholder: "যমুনা অ্যাপারেল লিমিটেড" },
            { key: "registration_no", label: "RJSC Registration No", placeholder: "C-189201/2026" },
            { key: "tin_number", label: "TIN Number", placeholder: "591827364510" },
            { key: "address", label: "Registered Address", placeholder: "Gulshan-2, Dhaka-1212" },
          ],
          buildPayload: (v) => ({
            code: v.code,
            name: v.name,
            name_bn: v.name_bn || "",
            registration_no: v.registration_no || "C-190000/2026",
            tin_number: v.tin_number || "",
            address: v.address || "Dhaka, Bangladesh",
            currency: "BDT",
            timezone: "Asia/Dhaka",
          }),
        };
      }
      if (activeTab === "branches") {
        return {
          title: "Add Branch & Geofence Location (Module 2)",
          endpoint: "/organization/branches/",
          fields: [
            { key: "code", label: "Branch Code", placeholder: "e.g. DHK-UTT", required: true },
            { key: "name", label: "Branch Name (English)", placeholder: "e.g. Uttara Sector 4 Office", required: true },
            { key: "name_bn", label: "শাখার নাম (বাংলা)", placeholder: "উত্তরা শাখা" },
            { key: "city", label: "City", defaultValue: "Dhaka", required: true },
            { key: "latitude", label: "Geofence Latitude", type: "number", defaultValue: "23.8759" },
            { key: "longitude", label: "Geofence Longitude", type: "number", defaultValue: "90.3795" },
            { key: "geofence_radius_meters", label: "Geofence Radius (Meters)", type: "number", defaultValue: "200" },
          ],
          buildPayload: (v) => ({
            company: defaultCompanyId,
            code: v.code,
            name: v.name,
            name_bn: v.name_bn || "",
            city: v.city || "Dhaka",
            latitude: v.latitude || "23.8759",
            longitude: v.longitude || "90.3795",
            geofence_radius_meters: parseInt(v.geofence_radius_meters || "200", 10),
          }),
        };
      }
      return {
        title: "Add Department (Module 2)",
        endpoint: "/organization/departments/",
        fields: [
          { key: "code", label: "Department Code", placeholder: "e.g. RND", required: true },
          { key: "name", label: "Department Name (English)", placeholder: "e.g. Research & Innovation", required: true },
          { key: "name_bn", label: "বিভাগের নাম (বাংলা)", placeholder: "গবেষণা ও উদ্ভাবন" },
          ...(branchOptions.length
            ? [{ key: "branch", label: "Branch", type: "select" as const, options: branchOptions, defaultValue: defaultBranchId }]
            : []),
          { key: "approved_headcount", label: "Approved Manpower Headcount", type: "number", defaultValue: "12", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          branch: v.branch || defaultBranchId,
          code: v.code,
          name: v.name,
          name_bn: v.name_bn || "",
          approved_headcount: parseInt(v.approved_headcount || "12", 10),
        }),
      };
    }

    // MODULE 3: EMPLOYEE INFORMATION & CHILD TABS
    if (moduleNumber === 3) {
      if (activeTab === "family") {
        return {
          title: "Add Family Member & PF Nominee (Module 3)",
          endpoint: "/employees/family-members/",
          fields: [
            { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
            { key: "full_name", label: "Family Member Full Name", placeholder: "e.g. Tahmina Akter", required: true },
            {
              key: "relationship",
              label: "Relationship",
              type: "select",
              defaultValue: "SPOUSE",
              options: [
                { value: "SPOUSE", label: "Spouse" },
                { value: "CHILD", label: "Child" },
                { value: "PARENT", label: "Parent" },
                { value: "SIBLING", label: "Sibling" },
              ],
            },
            { key: "date_of_birth", label: "Date of Birth", type: "date", defaultValue: "1995-06-15" },
            { key: "nominee_share_pct", label: "Nominee Share (%)", type: "number", defaultValue: "100.0000" },
          ],
          buildPayload: (v) => ({
            employee: v.employee || defaultEmpId,
            full_name: v.full_name,
            relationship: v.relationship || "SPOUSE",
            date_of_birth: v.date_of_birth || "1995-06-15",
            is_nominee: true,
            nominee_share_pct: v.nominee_share_pct || "100.0000",
          }),
        };
      }
      if (activeTab === "qualifications") {
        return {
          title: "Add Academic Qualification / Certification (Module 3)",
          endpoint: "/employees/qualifications/",
          fields: [
            { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
            { key: "degree_or_certification", label: "Degree / Certification", placeholder: "e.g. MBA in Finance", required: true },
            { key: "institution", label: "University / Institute", placeholder: "e.g. North South University", required: true },
            { key: "passing_year", label: "Passing Year", type: "number", defaultValue: "2022" },
            { key: "result_or_cgpa", label: "Result / CGPA", placeholder: "e.g. CGPA 3.85 / 4.00", defaultValue: "CGPA 3.80 / 4.00" },
          ],
          buildPayload: (v) => ({
            employee: v.employee || defaultEmpId,
            degree_or_certification: v.degree_or_certification,
            institution: v.institution,
            passing_year: parseInt(v.passing_year || "2022", 10),
            result_or_cgpa: v.result_or_cgpa || "CGPA 3.80 / 4.00",
          }),
        };
      }
      if (activeTab === "contracts") {
        return {
          title: "Add Employment Contract Record (Module 3)",
          endpoint: "/employees/employment-records/",
          fields: [
            { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
            { key: "contract_reference", label: "Contract Reference No", placeholder: "e.g. CNT-2026-088", required: true },
            {
              key: "contract_type",
              label: "Contract Type",
              type: "select",
              defaultValue: "PERMANENT",
              options: [
                { value: "PERMANENT", label: "Permanent" },
                { value: "PROBATION", label: "Probation" },
                { value: "CONTRACT", label: "Fixed-Term Contract" },
              ],
            },
            { key: "effective_from", label: "Effective From Date", type: "date", defaultValue: "2026-10-01", required: true },
            { key: "change_reason", label: "Contract / Revision Reason", placeholder: "e.g. Confirmation after probation" },
          ],
          buildPayload: (v) => ({
            company: defaultCompanyId,
            employee: v.employee || defaultEmpId,
            branch: defaultBranchId,
            department: defaultDeptId,
            designation: defaultDesigId,
            contract_reference: v.contract_reference,
            contract_type: v.contract_type || "PERMANENT",
            effective_from: v.effective_from || "2026-10-01",
            change_reason: v.change_reason || "Contract issued",
            status: "RUNNING",
          }),
        };
      }
      if (activeTab === "documents") {
        return {
          title: "Add Verified Employee Document Metadata (Module 3)",
          endpoint: "/employees/documents/",
          fields: [
            { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
            {
              key: "document_type",
              label: "Document Type",
              type: "select",
              defaultValue: "NATIONAL_ID",
              options: [
                { value: "NATIONAL_ID", label: "National ID (NID)" },
                { value: "PASSPORT", label: "Passport" },
                { value: "TIN_CERTIFICATE", label: "TIN Certificate" },
                { value: "ACADEMIC_CERTIFICATE", label: "Academic Certificate" },
              ],
            },
            { key: "title", label: "Document Title", placeholder: "e.g. Smart National ID Card", required: true },
            { key: "issue_date", label: "Issue Date", type: "date", defaultValue: "2021-01-15" },
            { key: "expiry_date", label: "Expiry Date", type: "date", defaultValue: "2031-01-15" },
          ],
          buildPayload: (v) => ({
            employee: v.employee || defaultEmpId,
            document_type: v.document_type || "NATIONAL_ID",
            title: v.title,
            issue_date: v.issue_date || "2021-01-15",
            expiry_date: v.expiry_date || "2031-01-15",
            storage_key: `private/employees/${v.employee || defaultEmpId}/${(v.document_type || "nid").toLowerCase()}.pdf`,
            is_verified: true,
          }),
        };
      }
      return {
        title: "Onboard New Employee (Module 3)",
        endpoint: "/employees/",
        fields: [
          { key: "employee_code", label: "Employee ID / Code", placeholder: "e.g. EMP-0098", required: true },
          { key: "full_name", label: "Full Name (English)", placeholder: "e.g. Tariqul Hasan", required: true },
          { key: "full_name_bn", label: "কর্মীর নাম (বাংলা)", placeholder: "তারিকুল হাসান" },
          { key: "work_email", label: "Work Email", type: "email", placeholder: "tariqul@company.bd", required: true },
          { key: "phone", label: "Mobile Phone (BD)", placeholder: "+8801711009988", defaultValue: "+8801711009988", required: true },
          { key: "joining_date", label: "Joining Date", type: "date", defaultValue: "2026-10-26", required: true },
          {
            key: "employment_status",
            label: "Employment Status",
            type: "select",
            defaultValue: "PERMANENT",
            options: [
              { value: "PERMANENT", label: "Permanent" },
              { value: "PROBATION", label: "Probation" },
              { value: "CONTRACT", label: "Contractual" },
            ],
          },
          ...(deptOptions.length
            ? [{ key: "department", label: "Department", type: "select" as const, options: deptOptions, defaultValue: defaultDeptId }]
            : []),
          ...(desigOptions.length
            ? [{ key: "designation", label: "Designation", type: "select" as const, options: desigOptions, defaultValue: defaultDesigId }]
            : []),
          { key: "gross_salary_bdt", label: "Monthly Gross Salary (BDT)", type: "number", defaultValue: "60000", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          employee_code: v.employee_code,
          full_name: v.full_name,
          full_name_bn: v.full_name_bn || "",
          work_email: v.work_email,
          phone: v.phone || "+8801711009988",
          joining_date: v.joining_date || "2026-10-26",
          employment_status: v.employment_status || "PERMANENT",
          branch: defaultBranchId,
          department: v.department || defaultDeptId,
          designation: v.designation || defaultDesigId,
          gross_salary_bdt: v.gross_salary_bdt || "60000.00",
        }),
      };
    }

    // MODULE 4: MANPOWER PLANNING
    if (moduleNumber === 4) {
      return {
        title: "Create Departmental Manpower Plan (Module 4)",
        endpoint: "/talent/manpower-plans/",
        fields: [
          ...(deptOptions.length
            ? [{ key: "department", label: "Department", type: "select" as const, options: deptOptions, defaultValue: defaultDeptId, required: true }]
            : []),
          { key: "fiscal_year", label: "Fiscal Year", defaultValue: "2026-2027", required: true },
          { key: "approved_headcount", label: "Approved Headcount", type: "number", defaultValue: "25", required: true },
          { key: "current_headcount", label: "Current Headcount", type: "number", defaultValue: "20", required: true },
          { key: "open_vacancies", label: "Open Vacancies", type: "number", defaultValue: "5", required: true },
          { key: "annual_budget_bdt", label: "Annual Staffing Budget (BDT)", type: "number", defaultValue: "12000000", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          department: v.department || defaultDeptId,
          fiscal_year: v.fiscal_year || "2026-2027",
          approved_headcount: parseInt(v.approved_headcount || "25", 10),
          current_headcount: parseInt(v.current_headcount || "20", 10),
          open_vacancies: parseInt(v.open_vacancies || "5", 10),
          annual_budget_bdt: v.annual_budget_bdt || "12000000.00",
          status: "APPROVED",
        }),
      };
    }

    // MODULE 5: RECRUITMENT & ATS
    if (moduleNumber === 5) {
      const defaultReqId = auxData.requisitions[0]?.id ? String(auxData.requisitions[0].id) : "";
      return {
        title: "Add Job Applicant to Recruitment Pipeline (Module 5)",
        endpoint: "/talent/applicants/",
        fields: [
          { key: "full_name", label: "Candidate Full Name (English)", placeholder: "e.g. Salman Farsi", required: true },
          { key: "full_name_bn", label: "প্রার্থীর নাম (বাংলা)", placeholder: "সালমান ফারসি" },
          { key: "email", label: "Candidate Email", type: "email", placeholder: "salman@candidate.bd", required: true },
          { key: "phone", label: "Candidate Phone", defaultValue: "+8801755112233", required: true },
          {
            key: "stage",
            label: "Pipeline Stage",
            type: "select",
            defaultValue: "APPLIED",
            options: [
              { value: "APPLIED", label: "Applied" },
              { value: "SCREENING", label: "Screening" },
              { value: "INTERVIEW", label: "Interview" },
              { value: "OFFERED", label: "Offered" },
            ],
          },
          { key: "evaluation_score", label: "Evaluation Score (%)", type: "number", defaultValue: "88" },
          { key: "expected_salary_bdt", label: "Expected Monthly Salary (BDT)", type: "number", defaultValue: "65000" },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          requisition: defaultReqId,
          full_name: v.full_name,
          full_name_bn: v.full_name_bn || "",
          email: v.email,
          phone: v.phone || "+8801755112233",
          stage: v.stage || "APPLIED",
          evaluation_score: v.evaluation_score || "88.00",
          expected_salary_bdt: v.expected_salary_bdt || "65000.00",
        }),
      };
    }

    // MODULE 6: ONBOARDING
    if (moduleNumber === 6) {
      return {
        title: "Assign Onboarding Checklist (Module 6)",
        endpoint: "/talent/onboarding/",
        fields: [
          { key: "employee", label: "New Joiner Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "template_name", label: "Onboarding Template Name", defaultValue: "Standard Bangladesh HQ Onboarding", required: true },
          { key: "completion_pct", label: "Readiness Completion (%)", type: "number", defaultValue: "50" },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          employee: v.employee || defaultEmpId,
          template_name: v.template_name || "Standard Bangladesh HQ Onboarding",
          tasks_json: [
            { task: "NID & TIN Verification", done: true },
            { task: "Bank Salary Account Setup", done: false },
          ],
          completion_pct: parseInt(v.completion_pct || "50", 10),
          status: "IN_PROGRESS",
        }),
      };
    }

    // MODULE 7: CONFIRMATION & PROBATION
    if (moduleNumber === 7) {
      return {
        title: "Create Probation Confirmation Review (Module 7)",
        endpoint: "/talent/probation-reviews/",
        fields: [
          { key: "employee", label: "Employee on Probation", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "probation_end_date", label: "Probation End Date", type: "date", defaultValue: "2026-11-30", required: true },
          { key: "supervisor_rating", label: "Supervisor Rating (Out of 5.00)", type: "number", defaultValue: "4.50", required: true },
          {
            key: "recommendation",
            label: "Recommendation",
            type: "select",
            defaultValue: "CONFIRM",
            options: [
              { value: "CONFIRM", label: "Confirm Permanent Employment" },
              { value: "EXTEND", label: "Extend Probation Period" },
            ],
          },
          { key: "remarks", label: "Evaluation Remarks", placeholder: "Strong technical & cultural fit", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          employee: v.employee || defaultEmpId,
          probation_end_date: v.probation_end_date || "2026-11-30",
          supervisor_rating: v.supervisor_rating || "4.50",
          recommendation: v.recommendation || "CONFIRM",
          remarks: v.remarks,
          status: "SUBMITTED",
        }),
      };
    }

    // MODULE 8: ATTENDANCE
    if (moduleNumber === 8) {
      return {
        title: "Log Daily Attendance Record (Module 8)",
        endpoint: "/time/attendance-days/",
        fields: [
          { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "work_date", label: "Attendance Date", type: "date", defaultValue: "2026-10-27", required: true },
          {
            key: "status",
            label: "Attendance Status",
            type: "select",
            defaultValue: "PRESENT",
            options: [
              { value: "PRESENT", label: "Present" },
              { value: "LATE", label: "Late" },
              { value: "ABSENT", label: "Absent" },
            ],
          },
          { key: "worked_hours", label: "Worked Hours", type: "number", defaultValue: "8.00" },
          { key: "extra_hours", label: "Overtime / Extra Hours", type: "number", defaultValue: "0.00" },
          { key: "late_minutes", label: "Late Arrival (Minutes)", type: "number", defaultValue: "0" },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          employee: v.employee || defaultEmpId,
          work_date: v.work_date || "2026-10-27",
          status: v.status || "PRESENT",
          worked_hours: v.worked_hours || "8.00",
          extra_hours: v.extra_hours || "0.00",
          late_minutes: parseInt(v.late_minutes || "0", 10),
          source: "MANUAL",
          within_geofence: true,
        }),
      };
    }

    // MODULE 9: SHIFT & ROSTER
    if (moduleNumber === 9) {
      return {
        title: "Create Work Shift Definition (Module 9)",
        endpoint: "/time/shifts/",
        fields: [
          { key: "code", label: "Shift Code", placeholder: "e.g. SH-EVE", required: true },
          { key: "name", label: "Shift Name", placeholder: "e.g. Evening Shift (14:00 - 22:00)", required: true },
          { key: "start_time", label: "Start Time", type: "time", defaultValue: "14:00", required: true },
          { key: "end_time", label: "End Time", type: "time", defaultValue: "22:00", required: true },
          { key: "grace_minutes_late", label: "Late Grace Period (Minutes)", type: "number", defaultValue: "15" },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          code: v.code,
          name: v.name,
          start_time: v.start_time || "14:00",
          end_time: v.end_time || "22:00",
          crosses_midnight: false,
          grace_minutes_late: parseInt(v.grace_minutes_late || "15", 10),
          grace_minutes_early: 10,
        }),
      };
    }

    // MODULE 10, 32, 33: LEAVE REQUEST
    if (moduleNumber === 10 || moduleNumber === 32 || moduleNumber === 33) {
      const defaultLtId = leaveTypeOptions[0]?.value || "";
      return {
        title: "Submit Leave Application (Module 10)",
        endpoint: "/time/leave-requests/",
        fields: [
          { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          ...(leaveTypeOptions.length
            ? [{ key: "leave_type", label: "Leave Type", type: "select" as const, options: leaveTypeOptions, defaultValue: defaultLtId, required: true }]
            : []),
          { key: "start_date", label: "Start Date", type: "date", defaultValue: "2026-11-10", required: true },
          { key: "end_date", label: "End Date", type: "date", defaultValue: "2026-11-11", required: true },
          { key: "days_requested", label: "Total Days Requested", type: "number", defaultValue: "2", required: true },
          { key: "reason", label: "Reason for Leave", placeholder: "e.g. Family function in Sylhet", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          reference_no: `LR-2026-${Math.floor(1000 + Math.random() * 9000)}`,
          employee: v.employee || defaultEmpId,
          leave_type: v.leave_type || defaultLtId,
          start_date: v.start_date || "2026-11-10",
          end_date: v.end_date || "2026-11-11",
          days_requested: v.days_requested || "2.00",
          reason: v.reason,
          status: "SUBMITTED",
        }),
      };
    }

    // MODULE 11: HOLIDAY & WORK CALENDAR
    if (moduleNumber === 11) {
      const defaultCalId = auxData.calendars[0]?.id ? String(auxData.calendars[0].id) : "";
      return {
        title: "Add Public / Festival Holiday (Module 11)",
        endpoint: "/time/holidays/",
        fields: [
          { key: "name", label: "Holiday Name (English)", placeholder: "e.g. Eid-ul-Adha Holiday", required: true },
          { key: "name_bn", label: "ছুটির নাম (বাংলা)", placeholder: "ঈদুল আযহা ছুটি" },
          { key: "date", label: "Holiday Date", type: "date", defaultValue: "2026-05-28", required: true },
          {
            key: "holiday_type",
            label: "Holiday Category",
            type: "select",
            defaultValue: "FESTIVAL",
            options: [
              { value: "PUBLIC", label: "Public / National Holiday" },
              { value: "FESTIVAL", label: "Festival Holiday" },
              { value: "COMPANY", label: "Company Holiday" },
            ],
          },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          calendar: defaultCalId,
          name: v.name,
          name_bn: v.name_bn || "",
          date: v.date || "2026-05-28",
          holiday_type: v.holiday_type || "FESTIVAL",
          is_paid: true,
        }),
      };
    }

    // MODULE 12: OVERTIME
    if (moduleNumber === 12) {
      return {
        title: "Submit Overtime Request (Module 12)",
        endpoint: "/time/overtime-requests/",
        fields: [
          { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "work_date", label: "Overtime Work Date", type: "date", defaultValue: "2026-10-26", required: true },
          { key: "requested_hours", label: "Requested Overtime Hours", type: "number", defaultValue: "3.00", required: true },
          { key: "rate_multiplier", label: "OT Rate Multiplier (2.0x Standard)", type: "number", defaultValue: "2.0000" },
          { key: "reason", label: "Justification / Reason", placeholder: "e.g. Urgent export shipment loading", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          employee: v.employee || defaultEmpId,
          work_date: v.work_date || "2026-10-26",
          requested_hours: v.requested_hours || "3.00",
          approved_hours: v.requested_hours || "3.00",
          rate_multiplier: v.rate_multiplier || "2.0000",
          reason: v.reason,
          status: "SUBMITTED",
        }),
      };
    }

    // MODULE 13: FIELD DUTY / MOVEMENT
    if (moduleNumber === 13) {
      return {
        title: "Log Field Duty / Outside Movement (Module 13)",
        endpoint: "/time/field-duty/",
        fields: [
          { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          {
            key: "movement_type",
            label: "Movement Type",
            type: "select",
            defaultValue: "CLIENT_VISIT",
            options: [
              { value: "CLIENT_VISIT", label: "Client / Bank Visit" },
              { value: "FACTORY_INSPECTION", label: "Factory / Port Inspection" },
              { value: "GOVERNMENT_OFFICE", label: "RJSC / NBR / Govt Duty" },
            ],
          },
          { key: "work_date", label: "Movement Date", type: "date", defaultValue: "2026-10-26", required: true },
          { key: "client_or_location", label: "Client / Destination Location", placeholder: "e.g. Chattogram Port Custom House", required: true },
          { key: "latitude", label: "Check-In Latitude", type: "number", defaultValue: "22.3264" },
          { key: "longitude", label: "Check-In Longitude", type: "number", defaultValue: "91.8123" },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          employee: v.employee || defaultEmpId,
          movement_type: v.movement_type || "CLIENT_VISIT",
          work_date: v.work_date || "2026-10-26",
          client_or_location: v.client_or_location,
          latitude: v.latitude || "22.3264",
          longitude: v.longitude || "91.8123",
          status: "APPROVED",
        }),
      };
    }

    // MODULE 14: SALARY STRUCTURE
    if (moduleNumber === 14) {
      return {
        title: "Assign Effective-Dated Salary Structure (Module 14)",
        endpoint: "/payroll/salary-structures/",
        fields: [
          { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "effective_from", label: "Effective From Date", type: "date", defaultValue: "2026-11-01", required: true },
          { key: "gross_amount", label: "Monthly Gross Salary (BDT — Auto 50/25/10/10/5% Split)", type: "number", defaultValue: "70000", required: true },
          { key: "change_reason", label: "Revision Reason", placeholder: "e.g. Annual salary revision", required: true },
        ],
        buildPayload: (v) => {
          const gross = parseFloat(v.gross_amount || "70000");
          return {
            company: defaultCompanyId,
            employee: v.employee || defaultEmpId,
            effective_from: v.effective_from || "2026-11-01",
            gross_amount: gross.toFixed(2),
            basic_amount: (gross * 0.5).toFixed(2),
            house_rent_amount: (gross * 0.25).toFixed(2),
            medical_amount: (gross * 0.1).toFixed(2),
            conveyance_amount: (gross * 0.1).toFixed(2),
            entertainment_amount: (gross * 0.05).toFixed(2),
            change_reason: v.change_reason || "Salary structure assigned",
          };
        },
      };
    }

    // MODULE 15 & 22: PAYROLL PERIOD
    if (moduleNumber === 15 || moduleNumber === 22) {
      return {
        title: "Open New Monthly Payroll Period (Module 15)",
        endpoint: "/payroll/periods/",
        fields: [
          { key: "name", label: "Payroll Period Name", placeholder: "e.g. November 2026", required: true },
          { key: "year", label: "Year", type: "number", defaultValue: "2026", required: true },
          { key: "month", label: "Month (1-12)", type: "number", defaultValue: "11", required: true },
          { key: "start_date", label: "Period Start Date", type: "date", defaultValue: "2026-11-01", required: true },
          { key: "end_date", label: "Period End Date", type: "date", defaultValue: "2026-11-30", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          name: v.name,
          year: parseInt(v.year || "2026", 10),
          month: parseInt(v.month || "11", 10),
          start_date: v.start_date || "2026-11-01",
          end_date: v.end_date || "2026-11-30",
        }),
      };
    }

    // MODULE 16: BONUS & INCENTIVE
    if (moduleNumber === 16) {
      return {
        title: "Create Festival / Performance Bonus Run (Module 16)",
        endpoint: "/payroll/bonuses/",
        fields: [
          { key: "name", label: "Bonus Batch Name", placeholder: "e.g. Eid-ul-Adha Festival Bonus 2026", required: true },
          {
            key: "bonus_type",
            label: "Bonus Type",
            type: "select",
            defaultValue: "FESTIVAL_EID",
            options: [
              { value: "FESTIVAL_EID", label: "Eid Festival Bonus" },
              { value: "BOISHAKHI", label: "Pohela Boishakh Allowance" },
              { value: "PERFORMANCE", label: "Annual Performance Bonus" },
            ],
          },
          { key: "effective_date", label: "Payout Date", type: "date", defaultValue: "2026-11-15", required: true },
          { key: "pct_of_basic", label: "Percentage of Basic Salary (%)", type: "number", defaultValue: "100" },
          { key: "total_amount_bdt", label: "Total Bonus Pool (BDT)", type: "number", defaultValue: "850000", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          name: v.name,
          bonus_type: v.bonus_type || "FESTIVAL_EID",
          effective_date: v.effective_date || "2026-11-15",
          pct_of_basic: v.pct_of_basic || "100.0000",
          total_amount_bdt: v.total_amount_bdt || "850000.00",
          status: "APPROVED",
        }),
      };
    }

    // MODULE 17: EXPENSE CLAIM
    if (moduleNumber === 17) {
      return {
        title: "Submit Expense Reimbursement Claim (Module 17)",
        endpoint: "/payroll/expense-claims/",
        fields: [
          { key: "employee", label: "Claimant Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          {
            key: "category",
            label: "Expense Category",
            type: "select",
            defaultValue: "TRANSPORT",
            options: [
              { value: "TRANSPORT", label: "Transport & Conveyance" },
              { value: "ACCOMMODATION", label: "Hotel & Travel" },
              { value: "MEDICAL", label: "Medical Reimbursement" },
              { value: "CLIENT_HOSPITALITY", label: "Client Hospitality" },
            ],
          },
          { key: "claim_date", label: "Expense Date", type: "date", defaultValue: "2026-10-26", required: true },
          { key: "amount_bdt", label: "Claim Amount (BDT)", type: "number", defaultValue: "3200", required: true },
          { key: "description", label: "Expense Particulars", placeholder: "e.g. Gazipur plant inspection transport", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          reference_no: `EXP-${Math.floor(1000 + Math.random() * 9000)}`,
          employee: v.employee || defaultEmpId,
          category: v.category || "TRANSPORT",
          claim_date: v.claim_date || "2026-10-26",
          amount_bdt: v.amount_bdt || "3200.00",
          description: v.description,
          status: "SUBMITTED",
        }),
      };
    }

    // MODULE 18: LOANS & ADVANCES
    if (moduleNumber === 18) {
      return {
        title: "Issue Employee Loan / Salary Advance (Module 18)",
        endpoint: "/payroll/loans/",
        fields: [
          { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          {
            key: "loan_type",
            label: "Loan / Advance Type",
            type: "select",
            defaultValue: "SALARY_ADVANCE",
            options: [
              { value: "SALARY_ADVANCE", label: "Salary Advance" },
              { value: "PF_LOAN", label: "Provident Fund Loan" },
              { value: "EMERGENCY_LOAN", label: "Emergency Medical Loan" },
            ],
          },
          { key: "principal_bdt", label: "Principal Amount (BDT)", type: "number", defaultValue: "30000", required: true },
          { key: "monthly_installment_bdt", label: "Monthly Deduction Installment (BDT)", type: "number", defaultValue: "5000", required: true },
          { key: "total_installments", label: "Number of Installments", type: "number", defaultValue: "6", required: true },
          { key: "disbursed_on", label: "Disbursement Date", type: "date", defaultValue: "2026-10-26" },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          loan_number: `LN-${Math.floor(1000 + Math.random() * 9000)}`,
          employee: v.employee || defaultEmpId,
          loan_type: v.loan_type || "SALARY_ADVANCE",
          principal_bdt: v.principal_bdt || "30000.00",
          monthly_installment_bdt: v.monthly_installment_bdt || "5000.00",
          total_installments: parseInt(v.total_installments || "6", 10),
          disbursed_on: v.disbursed_on || "2026-10-26",
          status: "APPROVED",
        }),
      };
    }

    // MODULE 20: TAX & STATUTORY NIS
    if (moduleNumber === 20) {
      return {
        title: "Add Statutory Tax Slab (Module 20)",
        endpoint: "/payroll/tax-slabs/",
        fields: [
          { key: "income_year", label: "Income Year", defaultValue: "2026-2027", required: true },
          { key: "slab_order", label: "Slab Order", type: "number", defaultValue: "5", required: true },
          { key: "threshold_amount_bdt", label: "Slab Threshold Amount (BDT)", type: "number", defaultValue: "1850000", required: true },
          { key: "tax_rate_pct", label: "Marginal Tax Rate (%)", type: "number", defaultValue: "20", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          income_year: v.income_year || "2026-2027",
          slab_order: parseInt(v.slab_order || "5", 10),
          threshold_amount_bdt: v.threshold_amount_bdt || "1850000.00",
          tax_rate_pct: v.tax_rate_pct || "20.0000",
          review_flag: "Needs review by a local HR/tax professional",
        }),
      };
    }

    // MODULE 21: BANK & MFS DISBURSEMENT
    if (moduleNumber === 21) {
      const defaultRunId = auxData.payrollRuns[0]?.id ? String(auxData.payrollRuns[0].id) : "";
      return {
        title: "Generate Bank / MFS Disbursement Batch (Module 21)",
        endpoint: "/payroll/payment-batches/",
        fields: [
          {
            key: "payout_channel",
            label: "Disbursement Channel",
            type: "select",
            defaultValue: "BEFTN",
            options: [
              { value: "BEFTN", label: "Bangladesh Bank BEFTN Advice" },
              { value: "BKASH", label: "bKash Corporate MFS Bulk" },
              { value: "NAGAD", label: "Nagad Corporate Disbursement" },
            ],
          },
          { key: "bank_or_mfs_name", label: "Bank / MFS Institution Name", defaultValue: "BRAC Bank PLC", required: true },
          { key: "record_count", label: "Total Payees", type: "number", defaultValue: "32", required: true },
          { key: "total_amount_bdt", label: "Total Net Disbursement (BDT)", type: "number", defaultValue: "1450000", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          payroll_run: defaultRunId,
          batch_number: `BAT-${Math.floor(1000 + Math.random() * 9000)}`,
          payout_channel: v.payout_channel || "BEFTN",
          bank_or_mfs_name: v.bank_or_mfs_name || "BRAC Bank PLC",
          record_count: parseInt(v.record_count || "32", 10),
          total_amount_bdt: v.total_amount_bdt || "1450000.00",
          status: "GENERATED",
        }),
      };
    }

    // MODULE 23: PERFORMANCE APPRAISAL
    if (moduleNumber === 23) {
      return {
        title: "Create Employee Performance Appraisal (Module 23)",
        endpoint: "/talent/appraisals/",
        fields: [
          { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "review_cycle", label: "Review Cycle", defaultValue: "Annual Appraisal 2026", required: true },
          { key: "self_score", label: "Self Assessment Score (%)", type: "number", defaultValue: "90" },
          { key: "manager_score", label: "Manager Evaluation Score (%)", type: "number", defaultValue: "92" },
          { key: "peer_360_score", label: "360° Peer Feedback Score (%)", type: "number", defaultValue: "91" },
          { key: "final_rating", label: "Final Performance Band", defaultValue: "Outstanding (Band A)", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          employee: v.employee || defaultEmpId,
          review_cycle: v.review_cycle || "Annual Appraisal 2026",
          stage: "CONFIRMED",
          self_score: v.self_score || "90.00",
          manager_score: v.manager_score || "92.00",
          peer_360_score: v.peer_360_score || "91.00",
          final_rating: v.final_rating || "Outstanding (Band A)",
        }),
      };
    }

    // MODULE 24: CAREER MOVEMENT (INCREMENT / PROMOTION)
    if (moduleNumber === 24) {
      return {
        title: "Record Increment / Promotion / Transfer (Module 24)",
        endpoint: "/talent/career-movements/",
        fields: [
          { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          {
            key: "movement_type",
            label: "Movement Type",
            type: "select",
            defaultValue: "INCREMENT_AND_PROMOTION",
            options: [
              { value: "INCREMENT_AND_PROMOTION", label: "Increment & Promotion" },
              { value: "ANNUAL_INCREMENT", label: "Annual Merit Increment" },
              { value: "PROMOTION", label: "Grade / Designation Promotion" },
            ],
          },
          ...(desigOptions.length
            ? [{ key: "new_designation", label: "New Designation", type: "select" as const, options: desigOptions, defaultValue: defaultDesigId }]
            : []),
          { key: "effective_from", label: "Effective Date", type: "date", defaultValue: "2026-11-01", required: true },
          { key: "previous_gross_bdt", label: "Previous Gross Salary (BDT)", type: "number", defaultValue: "55000", required: true },
          { key: "revised_gross_bdt", label: "Revised Gross Salary (BDT)", type: "number", defaultValue: "65000", required: true },
          { key: "change_reason", label: "Justification / Reason", placeholder: "e.g. Annual performance promotion", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          employee: v.employee || defaultEmpId,
          movement_type: v.movement_type || "INCREMENT_AND_PROMOTION",
          new_designation: v.new_designation || defaultDesigId,
          effective_from: v.effective_from || "2026-11-01",
          previous_gross_bdt: v.previous_gross_bdt || "55000.00",
          revised_gross_bdt: v.revised_gross_bdt || "65000.00",
          change_reason: v.change_reason,
          status: "APPROVED",
        }),
      };
    }

    // MODULE 25: TRAINING PROGRAM
    if (moduleNumber === 25) {
      return {
        title: "Schedule Training Program (Module 25)",
        endpoint: "/talent/trainings/",
        fields: [
          { key: "title", label: "Training Program Title", placeholder: "e.g. Fire Safety & Accord Compliance Drill", required: true },
          { key: "category", label: "Category", defaultValue: "Compliance & EHS", required: true },
          { key: "trainer_or_institute", label: "Trainer / Institute", defaultValue: "BD Institute of Management (BIM)" },
          { key: "start_date", label: "Start Date", type: "date", defaultValue: "2026-11-15", required: true },
          { key: "end_date", label: "End Date", type: "date", defaultValue: "2026-11-17", required: true },
          { key: "enrolled_count", label: "Target Nominees Count", type: "number", defaultValue: "20" },
          { key: "cost_bdt", label: "Training Budget (BDT)", type: "number", defaultValue: "45000" },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          title: v.title,
          category: v.category || "Compliance & EHS",
          trainer_or_institute: v.trainer_or_institute || "BIM Dhaka",
          start_date: v.start_date || "2026-11-15",
          end_date: v.end_date || "2026-11-17",
          enrolled_count: parseInt(v.enrolled_count || "20", 10),
          cost_bdt: v.cost_bdt || "45000.00",
          status: "SCHEDULED",
        }),
      };
    }

    // MODULE 26: GRIEVANCE CASE
    if (moduleNumber === 26) {
      return {
        title: "Register Confidential Grievance Case (Module 26)",
        endpoint: "/relations/grievances/",
        fields: [
          { key: "complainant", label: "Complainant Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "assigned_handler", label: "Assigned HR Handler", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "category", label: "Grievance Category", placeholder: "e.g. Workplace Environment / Roster", required: true },
          { key: "resolution_summary", label: "Initial Case Notes", placeholder: "Confidential intake summary", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          case_number: `GRV-${Math.floor(100 + Math.random() * 900)}`,
          complainant: v.complainant || defaultEmpId,
          assigned_handler: v.assigned_handler || defaultEmpId,
          category: v.category,
          is_confidential: true,
          resolution_summary: v.resolution_summary,
          status: "OPEN",
        }),
      };
    }

    // MODULE 27: DISCIPLINARY CASE
    if (moduleNumber === 27) {
      return {
        title: "Open Disciplinary / Show-Cause Case (Module 27)",
        endpoint: "/relations/disciplinary/",
        fields: [
          { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "incident_date", label: "Incident Date", type: "date", defaultValue: "2026-10-25", required: true },
          { key: "allegation_summary", label: "Allegation / Show-Cause Notice Details", placeholder: "Describe policy violation...", required: true },
          { key: "action_taken", label: "Action / Stage", defaultValue: "SHOW_CAUSE_ISSUED", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          case_number: `DSC-${Math.floor(100 + Math.random() * 900)}`,
          employee: v.employee || defaultEmpId,
          incident_date: v.incident_date || "2026-10-25",
          allegation_summary: v.allegation_summary,
          action_taken: v.action_taken || "SHOW_CAUSE_ISSUED",
          status: "OPEN",
        }),
      };
    }

    // MODULE 28: COMPANY ASSET
    if (moduleNumber === 28) {
      return {
        title: "Register & Assign Company Asset (Module 28)",
        endpoint: "/relations/assets/",
        fields: [
          { key: "asset_tag", label: "Asset Tag", placeholder: "e.g. AST-LPT-042", required: true },
          { key: "name", label: "Asset Name / Model", placeholder: "e.g. Dell Latitude 5440 Laptop", required: true },
          { key: "category", label: "Asset Category", defaultValue: "IT Equipment", required: true },
          { key: "serial_number", label: "Serial Number", placeholder: "e.g. SN-BD-88291", required: true },
          { key: "assigned_to", label: "Custodian Employee", type: "select", options: empOptions, defaultValue: defaultEmpId },
          { key: "value_bdt", label: "Book Value (BDT)", type: "number", defaultValue: "115000", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          asset_tag: v.asset_tag,
          name: v.name,
          category: v.category || "IT Equipment",
          serial_number: v.serial_number,
          assigned_to: v.assigned_to || defaultEmpId,
          value_bdt: v.value_bdt || "115000.00",
          status: "ASSIGNED",
        }),
      };
    }

    // MODULE 29: HEALTH, SAFETY & WELFARE
    if (moduleNumber === 29) {
      return {
        title: "Log Occupational Health / Safety Record (Module 29)",
        endpoint: "/relations/health-safety/",
        fields: [
          { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "record_type", label: "Event / Checkup Type", defaultValue: "OCCUPATIONAL_HEALTH_CHECKUP", required: true },
          { key: "incident_or_checkup_date", label: "Date", type: "date", defaultValue: "2026-10-26", required: true },
          { key: "corrective_action", label: "Corrective / Welfare Action", placeholder: "e.g. Annual fitness clearance completed", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          employee: v.employee || defaultEmpId,
          record_type: v.record_type || "OCCUPATIONAL_HEALTH_CHECKUP",
          incident_or_checkup_date: v.incident_or_checkup_date || "2026-10-26",
          corrective_action: v.corrective_action,
          status: "CLOSED",
        }),
      };
    }

    // MODULE 30: RESIGNATION & SEPARATION
    if (moduleNumber === 30) {
      return {
        title: "Submit Employee Resignation Request (Module 30)",
        endpoint: "/relations/resignations/",
        fields: [
          { key: "employee", label: "Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "notice_given_date", label: "Notice Given Date", type: "date", defaultValue: "2026-10-26", required: true },
          { key: "last_working_day", label: "Last Working Day", type: "date", defaultValue: "2026-12-25", required: true },
          { key: "notice_period_days", label: "Notice Period (Days)", type: "number", defaultValue: "60", required: true },
          { key: "reason", label: "Reason for Separation", placeholder: "e.g. Career transition", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          employee: v.employee || defaultEmpId,
          notice_given_date: v.notice_given_date || "2026-10-26",
          last_working_day: v.last_working_day || "2026-12-25",
          notice_period_days: parseInt(v.notice_period_days || "60", 10),
          reason: v.reason,
          exit_interview_completed: false,
          status: "SUBMITTED",
        }),
      };
    }

    // MODULE 31: FINAL SETTLEMENT
    if (moduleNumber === 31) {
      return {
        title: "Calculate Final Settlement Statement (Module 31)",
        endpoint: "/relations/final-settlements/",
        fields: [
          { key: "employee", label: "Separating Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          { key: "unpaid_salary_bdt", label: "Unpaid Salary Dues (BDT)", type: "number", defaultValue: "55000", required: true },
          { key: "leave_encashment_bdt", label: "Earned Leave Encashment (BDT)", type: "number", defaultValue: "18000", required: true },
          { key: "pf_and_gratuity_bdt", label: "PF & Gratuity Payable (BDT)", type: "number", defaultValue: "65000", required: true },
          { key: "loan_recovery_bdt", label: "Loan / Advance Recovery (BDT)", type: "number", defaultValue: "0" },
        ],
        buildPayload: (v) => {
          const unpaid = parseFloat(v.unpaid_salary_bdt || "55000");
          const leaveEnc = parseFloat(v.leave_encashment_bdt || "18000");
          const pfGrat = parseFloat(v.pf_and_gratuity_bdt || "65000");
          const loanRec = parseFloat(v.loan_recovery_bdt || "0");
          const net = unpaid + leaveEnc + pfGrat - loanRec;
          return {
            company: defaultCompanyId,
            employee: v.employee || defaultEmpId,
            unpaid_salary_bdt: unpaid.toFixed(2),
            leave_encashment_bdt: leaveEnc.toFixed(2),
            pf_and_gratuity_bdt: pfGrat.toFixed(2),
            loan_recovery_bdt: loanRec.toFixed(2),
            asset_deduction_bdt: "0.00",
            net_settlement_bdt: net.toFixed(2),
            all_departments_cleared: true,
            status: "READY_FOR_PAYOUT",
          };
        },
      };
    }

    // MODULE 34: HR HELPDESK
    if (moduleNumber === 34) {
      return {
        title: "Open HR Helpdesk Ticket (Module 34)",
        endpoint: "/helpdesk/tickets/",
        fields: [
          { key: "requester", label: "Requester Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
          {
            key: "category",
            label: "Ticket Category",
            type: "select",
            defaultValue: "Salary & Tax Certificate",
            options: [
              { value: "Salary & Tax Certificate", label: "Salary & Tax Certificate" },
              { value: "Leave & Attendance", label: "Leave & Attendance Correction" },
              { value: "Medical & Insurance", label: "Medical & Insurance Claim" },
              { value: "IT & Access Card", label: "IT & Biometric Access Card" },
            ],
          },
          { key: "subject", label: "Ticket Subject", placeholder: "e.g. Request for Employment NOC Letter", required: true },
          {
            key: "priority",
            label: "Priority",
            type: "select",
            defaultValue: "NORMAL",
            options: [
              { value: "NORMAL", label: "Normal (24h SLA)" },
              { value: "HIGH", label: "High (8h SLA)" },
              { value: "URGENT", label: "Urgent (4h SLA)" },
            ],
          },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          ticket_number: `TKT-2026-${Math.floor(100 + Math.random() * 900)}`,
          requester: v.requester || defaultEmpId,
          category: v.category || "Salary & Tax Certificate",
          subject: v.subject,
          priority: v.priority || "NORMAL",
          sla_hours: v.priority === "URGENT" ? 4 : v.priority === "HIGH" ? 8 : 24,
          status: "OPEN",
        }),
      };
    }

    // MODULE 35: POLICY & LETTER STUDIO
    if (moduleNumber === 35) {
      return {
        title: "Publish HR Policy Document (Module 35)",
        endpoint: "/policies/documents/",
        fields: [
          { key: "title", label: "Policy Title (English)", placeholder: "e.g. Remote Work & Flexible Hours Policy", required: true },
          { key: "title_bn", label: "নীতির শিরোনাম (বাংলা)", placeholder: "রিমোট ওয়ার্ক নীতিমালা" },
          { key: "category", label: "Policy Category", defaultValue: "General HR", required: true },
          { key: "version", label: "Version", defaultValue: "1.0", required: true },
          { key: "effective_date", label: "Effective From Date", type: "date", defaultValue: "2026-11-01", required: true },
          { key: "content_markdown", label: "Policy Summary / Rules", placeholder: "Enter policy clauses...", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          title: v.title,
          title_bn: v.title_bn || "",
          category: v.category || "General HR",
          version: v.version || "1.0",
          effective_date: v.effective_date || "2026-11-01",
          content_markdown: v.content_markdown,
          requires_acknowledgment: true,
        }),
      };
    }

    // MODULE 36: ANNOUNCEMENTS
    if (moduleNumber === 36) {
      return {
        title: "Publish Company Announcement (Module 36)",
        endpoint: "/communications/announcements/",
        fields: [
          { key: "title", label: "Announcement Title (English)", placeholder: "e.g. Winter Office Timing Notice", required: true },
          { key: "title_bn", label: "বিজ্ঞপ্তির শিরোনাম (বাংলা)", placeholder: "শীতকালীন অফিস সময়সূচি" },
          {
            key: "category",
            label: "Category",
            type: "select",
            defaultValue: "NOTICE",
            options: [
              { value: "NOTICE", label: "Official Notice" },
              { value: "EVENT", label: "Company Event" },
              { value: "HOLIDAY", label: "Holiday Circular" },
            ],
          },
          { key: "body", label: "Notice Content", placeholder: "Write the full announcement...", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          title: v.title,
          title_bn: v.title_bn || "",
          category: v.category || "NOTICE",
          body: v.body,
          is_pinned: true,
        }),
      };
    }

    // MODULE 38: REPORTS & ANALYTICS
    if (moduleNumber === 38) {
      return {
        title: "Create Custom Report Definition (Module 38)",
        endpoint: "/reports/definitions/",
        fields: [
          { key: "code", label: "Report Code", placeholder: "e.g. dept-overtime-cost", required: true },
          { key: "name", label: "Report Name", placeholder: "e.g. Monthly Overtime Cost by Department", required: true },
          { key: "category", label: "Report Category", defaultValue: "Payroll & Finance", required: true },
          { key: "schedule_cron", label: "Scheduled Email Cron", defaultValue: "0 8 1 * *" },
        ],
        buildPayload: (v) => ({
          code: v.code,
          name: v.name,
          module_number: 38,
          category: v.category || "Payroll & Finance",
          columns_config: ["department", "headcount", "gross_bdt", "net_bdt"],
          schedule_cron: v.schedule_cron || "0 8 1 * *",
        }),
      };
    }

    // MODULE 39: USERS, ROLES & PERMISSIONS
    if (moduleNumber === 39) {
      return {
        title: "Create Security Role (Module 39)",
        endpoint: "/accounts/roles/",
        fields: [
          { key: "code", label: "Role Code", placeholder: "e.g. branch-hr-officer", required: true },
          { key: "name", label: "Role Name", placeholder: "e.g. Branch HR Officer", required: true },
          { key: "description", label: "Role Responsibilities & Scope", placeholder: "Branch-level employee & attendance access", required: true },
        ],
        buildPayload: (v) => ({
          code: v.code,
          name: v.name,
          description: v.description,
          can_view_confidential_salary: false,
          has_approval_authority: true,
        }),
      };
    }

    // MODULE 41: INTEGRATIONS & WEBHOOKS
    if (moduleNumber === 41) {
      return {
        title: "Register Outbound HTTPS Webhook (Module 41)",
        endpoint: "/integrations/webhooks/",
        fields: [
          { key: "name", label: "Webhook Subscription Name", placeholder: "e.g. SAP ERP Payroll Sync", required: true },
          { key: "target_url", label: "HTTPS Target URL (SSRF-Protected)", placeholder: "https://hooks.erp.example.com/hrm", required: true },
          { key: "events", label: "Subscribed Events (Comma-Separated)", defaultValue: "employee.created,payroll.run.approved", required: true },
        ],
        buildPayload: (v) => ({
          name: v.name,
          target_url: v.target_url,
          events: (v.events || "employee.created")
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
        }),
      };
    }

    // MODULE 42: SYSTEM SETTINGS & NUMBER SEQUENCES
    if (moduleNumber === 42) {
      return {
        title: "Create Document Number Sequence (Module 42)",
        endpoint: "/settings/number-sequences/",
        fields: [
          { key: "code", label: "Sequence Type Code", placeholder: "e.g. TRANSFER_ORDER", required: true },
          { key: "prefix", label: "Document Prefix", placeholder: "e.g. TRF-", required: true },
          { key: "padding", label: "Zero Padding Digits", type: "number", defaultValue: "4", required: true },
          { key: "next_val", label: "Starting Number", type: "number", defaultValue: "1", required: true },
        ],
        buildPayload: (v) => ({
          company: defaultCompanyId,
          code: v.code,
          prefix: v.prefix,
          padding: parseInt(v.padding || "4", 10),
          next_val: parseInt(v.next_val || "1", 10),
        }),
      };
    }

    // DEFAULT (MODULE 1 / 37 WORKFLOW APPROVAL REQUEST)
    const defaultWfId = auxData.workflows[0]?.id ? String(auxData.workflows[0].id) : "";
    return {
      title: `Create Approval Request (${moduleName})`,
      endpoint: "/workflows/approvals/",
      fields: [
        { key: "title", label: "Request Subject / Title", placeholder: "e.g. Special Budget / Policy Approval", required: true },
        { key: "subject_type", label: "Entity Type", defaultValue: "GeneralRequest", required: true },
        { key: "requester_employee", label: "Requester Employee", type: "select", options: empOptions, defaultValue: defaultEmpId, required: true },
        { key: "amount", label: "Amount (BDT — Optional)", type: "number", defaultValue: "0" },
      ],
      buildPayload: (v) => ({
        company: defaultCompanyId,
        workflow: defaultWfId,
        module_number: moduleNumber,
        subject_type: v.subject_type || "GeneralRequest",
        subject_id: v.requester_employee || defaultEmpId,
        title: v.title,
        requester_employee: v.requester_employee || defaultEmpId,
        current_step: 1,
        total_steps: 2,
        amount: v.amount || "0.00",
        status: "PENDING",
      }),
    };
  };

  const schema = getSchema();

  useEffect(() => {
    if (!open) return;
    const initial: Record<string, string> = {};
    schema.fields.forEach((f) => {
      initial[f.key] = f.defaultValue || (f.options?.[0]?.value ?? "");
    });
    setValues(initial);
  }, [
    open,
    moduleNumber,
    activeTab,
    effectiveEmployees.length,
    effectiveDepartments.length,
    effectiveBranches.length,
    auxData.leaveTypes.length,
    auxData.designations.length,
  ]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    for (const field of schema.fields) {
      if (field.required && !(values[field.key] || "").trim()) {
        setError(`${field.label} is required.`);
        return;
      }
    }

    setSubmitting(true);
    try {
      const payload = schema.buildPayload(values);
      const created = await apiFetch(schema.endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const undoUrl = created?.id ? `${schema.endpoint}${created.id}/` : undefined;
      onClose();
      onSuccess(`Created new record in ${moduleName}!`, undoUrl);
    } catch (err: any) {
      setError(err.message || "Failed to save record.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Drawer open={open} title={schema.title} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-3.5">
        {schema.fields.map((f) =>
          f.type === "select" && f.options ? (
            <Select
              key={f.key}
              label={`${f.label}${f.required ? " *" : ""}`}
              options={f.options}
              value={values[f.key] ?? f.defaultValue ?? ""}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, [f.key]: e.target.value }))
              }
            />
          ) : (
            <Input
              key={f.key}
              label={`${f.label}${f.required ? " *" : ""}`}
              type={f.type || "text"}
              placeholder={f.placeholder}
              value={values[f.key] ?? ""}
              onChange={(e) => {
                setValues((prev) => ({ ...prev, [f.key]: e.target.value }));
                setError(null);
              }}
            />
          )
        )}

        {error && (
          <div className="p-2.5 rounded-control bg-red-500/15 border border-red-500/30 text-xs font-semibold text-red-800">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" size="sm" disabled={submitting}>
            {submitting ? "Saving..." : "Save Record"}
          </Button>
        </div>
      </form>
    </Drawer>
  );
};
