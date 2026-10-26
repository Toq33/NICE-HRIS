"""Root URL configuration exposing versioned /api/v1/ endpoints for all 42 HRM modules and OpenAPI 3 docs."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from accounts.views import (
    DataScopeViewSet,
    DemoPersonaListView,
    LoginHistoryViewSet,
    LoginView,
    LogoutView,
    MeView,
    RoleViewSet,
    UserViewSet,
)
from integrations.views import (
    APIKeyViewSet,
    IntegrationConnectorViewSet,
    IntegrationRunLogViewSet,
    OAuth2ClientViewSet,
    OAuth2TokenView,
    WebhookDeliveryViewSet,
    WebhookEndpointViewSet,
)
from organization.views import (
    BranchViewSet,
    CompanyViewSet,
    CostCenterViewSet,
    DepartmentViewSet,
    DesignationViewSet,
    EmergencyContactViewSet,
    EmployeeDocumentViewSet,
    EmployeeExperienceViewSet,
    EmployeeQualificationViewSet,
    EmployeeViewSet,
    EmploymentRecordViewSet,
    FamilyMemberViewSet,
    GradeViewSet,
    ReportingLineViewSet,
    SectionViewSet,
)
from payroll.views import (
    BonusRunViewSet,
    EmployeeLoanViewSet,
    EmployeeSalaryStructureViewSet,
    ExpenseClaimViewSet,
    PaymentBatchViewSet,
    PayrollPeriodViewSet,
    PayrollRunViewSet,
    PayslipViewSet,
    ProvidentFundLedgerViewSet,
    SalaryComponentViewSet,
    StatutorySchemeViewSet,
    TaxSlabViewSet,
)
from platform_admin.views import ModuleRegistryView, PlanViewSet, TenantViewSet
from system_settings.views import (
    AttachmentViewSet,
    AuditLogViewSet,
    NumberSequenceViewSet,
    TenantSettingViewSet,
)
from talent_relations.views import (
    AppraisalSurveyViewSet,
    CareerMovementViewSet,
    ClearanceItemViewSet,
    CompanyAssetViewSet,
    DisciplinaryCaseViewSet,
    FinalSettlementViewSet,
    GoalViewSet,
    GrievanceCaseViewSet,
    HealthSafetyRecordViewSet,
    HelpdeskTicketViewSet,
    InterviewViewSet,
    JobApplicantViewSet,
    JobRequisitionViewSet,
    ManpowerPlanViewSet,
    OfferViewSet,
    OnboardingChecklistViewSet,
    PerformanceAppraisalViewSet,
    ProbationReviewViewSet,
    ResignationRequestViewSet,
    ReviewCycleViewSet,
    TrainingNominationViewSet,
    TrainingProgramViewSet,
)
from time_presence.views import (
    AttendanceDayViewSet,
    FieldDutyMovementViewSet,
    HolidayViewSet,
    LeaveLedgerViewSet,
    LeaveRequestViewSet,
    LeaveTypeViewSet,
    ManagementDashboardKPIView,
    MonthlyAttendanceSummaryViewSet,
    OvertimeRequestViewSet,
    RosterBatchViewSet,
    ShiftViewSet,
    WorkCalendarViewSet,
)
from workflows.views import (
    AnnouncementViewSet,
    ApprovalRequestViewSet,
    GeneratedLetterViewSet,
    LetterTemplateViewSet,
    NotificationViewSet,
    PolicyDocumentViewSet,
    ReportDefinitionViewSet,
    WorkflowDefinitionViewSet,
)

router = DefaultRouter()
# Platform Admin (above tenants)
router.register(r"platform/plans", PlanViewSet, basename="platform-plans")
router.register(r"platform/tenants", TenantViewSet, basename="platform-tenants")

# Module 39 & 40: Users, Roles, Permissions & Login History
router.register(r"accounts/users", UserViewSet, basename="users")
router.register(r"accounts/roles", RoleViewSet, basename="roles")
router.register(r"accounts/data-scopes", DataScopeViewSet, basename="data-scopes")
router.register(r"security/login-history", LoginHistoryViewSet, basename="login-history")

# Module 2 & 3: Company, Organization & Employee Information
router.register(r"organization/companies", CompanyViewSet, basename="companies")
router.register(r"organization/branches", BranchViewSet, basename="branches")
router.register(r"organization/departments", DepartmentViewSet, basename="departments")
router.register(r"organization/sections", SectionViewSet, basename="sections")
router.register(r"organization/grades", GradeViewSet, basename="grades")
router.register(r"organization/designations", DesignationViewSet, basename="designations")
router.register(r"organization/cost-centers", CostCenterViewSet, basename="cost-centers")
router.register(r"organization/reporting-lines", ReportingLineViewSet, basename="reporting-lines")
router.register(r"employees/emergency-contacts", EmergencyContactViewSet, basename="emergency-contacts")
router.register(r"employees/family-members", FamilyMemberViewSet, basename="family-members")
router.register(r"employees/qualifications", EmployeeQualificationViewSet, basename="employee-qualifications")
router.register(r"employees/experiences", EmployeeExperienceViewSet, basename="employee-experiences")
router.register(r"employees/employment-records", EmploymentRecordViewSet, basename="employment-records")
router.register(r"employees/documents", EmployeeDocumentViewSet, basename="employee-documents")
router.register(r"employees", EmployeeViewSet, basename="employees")

# Module 35, 36, 37, 38: Workflows, Policies, Letters, Announcements, Notifications, Reports
router.register(r"workflows/definitions", WorkflowDefinitionViewSet, basename="workflow-definitions")
router.register(r"workflows/approvals", ApprovalRequestViewSet, basename="approval-requests")
router.register(r"policies/documents", PolicyDocumentViewSet, basename="policy-documents")
router.register(r"policies/letter-templates", LetterTemplateViewSet, basename="letter-templates")
router.register(r"policies/generated-letters", GeneratedLetterViewSet, basename="generated-letters")
router.register(r"communications/announcements", AnnouncementViewSet, basename="announcements")
router.register(r"communications/notifications", NotificationViewSet, basename="notifications")
router.register(r"reports/definitions", ReportDefinitionViewSet, basename="report-definitions")

# Module 8, 9, 10, 11, 12, 13: Time & Presence
router.register(r"time/calendars", WorkCalendarViewSet, basename="work-calendars")
router.register(r"time/holidays", HolidayViewSet, basename="holidays")
router.register(r"time/shifts", ShiftViewSet, basename="shifts")
router.register(r"time/roster-batches", RosterBatchViewSet, basename="roster-batches")
router.register(r"time/attendance-days", AttendanceDayViewSet, basename="attendance-days")
router.register(r"time/attendance-summaries", MonthlyAttendanceSummaryViewSet, basename="attendance-summaries")
router.register(r"time/leave-types", LeaveTypeViewSet, basename="leave-types")
router.register(r"time/leave-ledger", LeaveLedgerViewSet, basename="leave-ledger")
router.register(r"time/leave-requests", LeaveRequestViewSet, basename="leave-requests")
router.register(r"time/overtime-requests", OvertimeRequestViewSet, basename="overtime-requests")
router.register(r"time/field-duty", FieldDutyMovementViewSet, basename="field-duty")

# Module 14, 15, 16, 17, 18, 19, 20, 21, 22: Payroll & Compensation
router.register(r"payroll/components", SalaryComponentViewSet, basename="salary-components")
router.register(r"payroll/salary-structures", EmployeeSalaryStructureViewSet, basename="salary-structures")
router.register(r"payroll/statutory-schemes", StatutorySchemeViewSet, basename="statutory-schemes")
router.register(r"payroll/tax-slabs", TaxSlabViewSet, basename="tax-slabs")
router.register(r"payroll/periods", PayrollPeriodViewSet, basename="payroll-periods")
router.register(r"payroll/runs", PayrollRunViewSet, basename="payroll-runs")
router.register(r"payroll/payslips", PayslipViewSet, basename="payslips")
router.register(r"payroll/bonuses", BonusRunViewSet, basename="bonus-runs")
router.register(r"payroll/expense-claims", ExpenseClaimViewSet, basename="expense-claims")
router.register(r"payroll/loans", EmployeeLoanViewSet, basename="employee-loans")
router.register(r"payroll/pf-ledger", ProvidentFundLedgerViewSet, basename="pf-ledger")
router.register(r"payroll/payment-batches", PaymentBatchViewSet, basename="payment-batches")

# Module 4-7, 23-25, 26-31, 34: Talent Lifecycle, Relations, Assets, Exit & Helpdesk
router.register(r"talent/manpower-plans", ManpowerPlanViewSet, basename="manpower-plans")
router.register(r"talent/requisitions", JobRequisitionViewSet, basename="job-requisitions")
router.register(r"talent/applicants", JobApplicantViewSet, basename="job-applicants")
router.register(r"talent/interviews", InterviewViewSet, basename="interviews")
router.register(r"talent/offers", OfferViewSet, basename="offers")
router.register(r"talent/onboarding", OnboardingChecklistViewSet, basename="onboarding-checklists")
router.register(r"talent/probation-reviews", ProbationReviewViewSet, basename="probation-reviews")
router.register(r"talent/review-cycles", ReviewCycleViewSet, basename="review-cycles")
router.register(r"talent/goals", GoalViewSet, basename="goals")
router.register(r"talent/appraisals", PerformanceAppraisalViewSet, basename="performance-appraisals")
router.register(r"talent/appraisal-surveys", AppraisalSurveyViewSet, basename="appraisal-surveys")
router.register(r"talent/career-movements", CareerMovementViewSet, basename="career-movements")
router.register(r"talent/trainings", TrainingProgramViewSet, basename="training-programs")
router.register(r"talent/training-nominations", TrainingNominationViewSet, basename="training-nominations")
router.register(r"relations/grievances", GrievanceCaseViewSet, basename="grievance-cases")
router.register(r"relations/disciplinary", DisciplinaryCaseViewSet, basename="disciplinary-cases")
router.register(r"relations/assets", CompanyAssetViewSet, basename="company-assets")
router.register(r"relations/health-safety", HealthSafetyRecordViewSet, basename="health-safety-records")
router.register(r"relations/resignations", ResignationRequestViewSet, basename="resignation-requests")
router.register(r"relations/clearance-items", ClearanceItemViewSet, basename="clearance-items")
router.register(r"relations/final-settlements", FinalSettlementViewSet, basename="final-settlements")
router.register(r"helpdesk/tickets", HelpdeskTicketViewSet, basename="helpdesk-tickets")

# Module 40 & 42: System Settings, Number Sequences, Attachments & Audit Log
router.register(r"settings/tenant-config", TenantSettingViewSet, basename="tenant-config")
router.register(r"settings/number-sequences", NumberSequenceViewSet, basename="number-sequences")
router.register(r"settings/attachments", AttachmentViewSet, basename="attachments")
router.register(r"security/audit-logs", AuditLogViewSet, basename="audit-logs")

# Module 41: API Keys, OAuth2 Clients, Webhooks & Connectors
router.register(r"integrations/api-keys", APIKeyViewSet, basename="api-keys")
router.register(r"integrations/oauth-clients", OAuth2ClientViewSet, basename="oauth-clients")
router.register(r"integrations/webhooks", WebhookEndpointViewSet, basename="webhooks")
router.register(r"integrations/webhook-deliveries", WebhookDeliveryViewSet, basename="webhook-deliveries")
router.register(r"integrations/connectors", IntegrationConnectorViewSet, basename="connectors")
router.register(r"integrations/run-logs", IntegrationRunLogViewSet, basename="connector-run-logs")

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth & Session
    path("api/v1/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/v1/auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("api/v1/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/v1/auth/demo-personas/", DemoPersonaListView.as_view(), name="auth-demo-personas"),
    path("api/v1/auth/oauth2/token/", OAuth2TokenView.as_view(), name="auth-oauth2-token"),
    # Module 1: Management Dashboard KPIs
    path("api/v1/dashboard/summary/", ManagementDashboardKPIView.as_view(), name="dashboard-summary"),
    # 42-Module Catalog & Enablement
    path("api/v1/modules/catalog/", ModuleRegistryView.as_view(), name="modules-catalog"),
    # OpenAPI 3 Schema & Interactive Docs
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # ViewSet Router
    path("api/v1/", include(router.urls)),
]
