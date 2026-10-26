"""Phase 4 (Talent Lifecycle: Mod 4-7, 23-25) & Phase 5 (Relations, Assets, Exit & Helpdesk: Mod 26-31, 34)."""
from decimal import Decimal
from typing import Any

from django.db import models

from core.models import (
    CompanyOwnedModel,
    EffectiveDatedModel,
    LedgerModel,
    RequestModel,
    SensitiveFieldMixin,
)


class ManpowerPlan(CompanyOwnedModel):
    """Department manpower plan and staffing budget (Module 4)."""

    department = models.ForeignKey("organization.Department", on_delete=models.PROTECT, related_name="manpower_plans")
    fiscal_year = models.CharField(max_length=20, default="2026-2027")
    approved_headcount = models.PositiveIntegerField(default=15)
    current_headcount = models.PositiveIntegerField(default=12)
    open_vacancies = models.PositiveIntegerField(default=3)
    annual_budget_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("12000000.00"))
    currency = models.CharField(max_length=3, default="BDT")
    status = models.CharField(max_length=20, default="APPROVED")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "department"])]


class JobRequisition(RequestModel):
    """Recruitment job requisition and published vacancy (Module 5)."""

    requisition_no = models.CharField(max_length=40, db_index=True)
    department = models.ForeignKey("organization.Department", on_delete=models.PROTECT, related_name="requisitions")
    designation = models.ForeignKey("organization.Designation", on_delete=models.PROTECT, related_name="requisitions")
    title = models.CharField(max_length=160)
    vacancies_count = models.PositiveSmallIntegerField(default=2)
    employment_type = models.CharField(max_length=32, default="PERMANENT")
    min_salary_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("45000.00"))
    max_salary_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("75000.00"))
    currency = models.CharField(max_length=3, default="BDT")
    is_published_on_careers = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "status"])]


class JobApplicant(CompanyOwnedModel):
    """Recruitment Kanban candidate card (APPLIED > SCREENING > INTERVIEW > OFFERED > HIRED) (Module 5)."""

    class Stage(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        SCREENING = "SCREENING", "Screening"
        INTERVIEW = "INTERVIEW", "Interview"
        OFFERED = "OFFERED", "Offer Extended"
        HIRED = "HIRED", "Hired"
        REJECTED = "REJECTED", "Rejected"

    requisition = models.ForeignKey(JobRequisition, on_delete=models.CASCADE, related_name="applicants")
    full_name = models.CharField(max_length=160)
    full_name_bn = models.CharField(max_length=160, blank=True, default="")
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.APPLIED, db_index=True)
    evaluation_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("82.50"))
    expected_salary_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("55000.00"))
    currency = models.CharField(max_length=3, default="BDT")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "stage"])]


class OnboardingChecklist(CompanyOwnedModel):
    """Pre-joining checklist, appointment letter, IT account & asset readiness (Module 6)."""

    employee = models.ForeignKey("organization.Employee", on_delete=models.CASCADE, related_name="onboarding_checklists")
    template_name = models.CharField(max_length=120, default="Standard Bangladesh Joining Checklist")
    tasks_json = models.JSONField(
        default=list,
        help_text="List of checklist items e.g. NID verified, TIN certificate, Bank account, IT email, ID card",
    )
    completion_pct = models.PositiveSmallIntegerField(default=80)
    status = models.CharField(max_length=24, default="IN_PROGRESS")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "status"])]


class ProbationReview(RequestModel):
    """Probation period tracking, supervisor evaluation, and confirmation approval (Module 7)."""

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="probation_reviews")
    probation_end_date = models.DateField(db_index=True)
    supervisor_rating = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("4.30"))
    recommendation = models.CharField(max_length=32, default="CONFIRM")  # CONFIRM, EXTEND, TERMINATE
    remarks = models.TextField(blank=True, default="Consistently met all KPIs during 6-month probation.")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "probation_end_date"])]


class PerformanceAppraisal(CompanyOwnedModel):
    """Performance cycle review with Stepper (TO_CONFIRM > CONFIRMED > DONE) and 360 feedback (Module 23)."""

    class Stage(models.TextChoices):
        TO_CONFIRM = "TO_CONFIRM", "To Confirm"
        CONFIRMED = "CONFIRMED", "Confirmed"
        DONE = "DONE", "Done"

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="appraisals")
    review_cycle = models.CharField(max_length=60, default="Annual Review 2026")
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.CONFIRMED, db_index=True)
    self_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("88.00"))
    manager_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("91.50"))
    peer_360_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("89.00"))
    final_rating = models.CharField(max_length=40, default="Exceeds Expectations")
    goals_summary = models.TextField(blank=True, default="Delivered Q1-Q3 departmental milestones ahead of schedule.")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "review_cycle"])]


class CareerMovement(EffectiveDatedModel):
    """Effective-dated Promotion, Increment, and Department/Branch/Inter-Company Transfer (Module 24)."""

    company = models.ForeignKey("organization.Company", on_delete=models.PROTECT, related_name="career_movements")
    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="career_movements")
    movement_type = models.CharField(
        max_length=32,
        default="INCREMENT_AND_PROMOTION",
        help_text="PROMOTION, INCREMENT, DEPARTMENT_TRANSFER, INTER_COMPANY_TRANSFER",
    )
    target_company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="incoming_transfers",
    )
    new_designation = models.ForeignKey(
        "organization.Designation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    previous_gross_bdt = models.DecimalField(max_digits=14, decimal_places=2)
    revised_gross_bdt = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="BDT")
    status = models.CharField(max_length=20, default="APPROVED")

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "effective_from"])]


class TrainingProgram(CompanyOwnedModel):
    """Training calendar, nominations, assessments, and skill certification (Module 25)."""

    title = models.CharField(max_length=180)
    category = models.CharField(max_length=80, default="Leadership & Compliance")
    start_date = models.DateField()
    end_date = models.DateField()
    trainer_or_institute = models.CharField(max_length=140, default="Bangladesh Institute of Management (BIM)")
    enrolled_count = models.PositiveSmallIntegerField(default=14)
    cost_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("65000.00"))
    currency = models.CharField(max_length=3, default="BDT")
    status = models.CharField(max_length=24, default="SCHEDULED")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "start_date"])]


class GrievanceCase(CompanyOwnedModel):
    """Confidential grievance case visible only to assigned handlers (Module 26)."""

    case_number = models.CharField(max_length=40, db_index=True)
    complainant = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="grievances_filed")
    assigned_handler = models.ForeignKey(
        "organization.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grievances_assigned",
    )
    category = models.CharField(max_length=80, default="Workplace Environment")
    is_confidential = models.BooleanField(default=True)
    status = models.CharField(max_length=24, default="UNDER_INVESTIGATION")
    resolution_summary = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "status"])]


class DisciplinaryCase(CompanyOwnedModel):
    """Restricted class: Incident report, show-cause notice, response, and decision (Module 27)."""

    case_number = models.CharField(max_length=40, db_index=True)
    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="disciplinary_cases")
    incident_date = models.DateField()
    allegation_summary = models.CharField(max_length=255)
    action_taken = models.CharField(max_length=80, default="SHOW_CAUSE_ISSUED")
    status = models.CharField(max_length=24, default="IN_REVIEW")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "status"])]


class CompanyAsset(CompanyOwnedModel):
    """IT and physical company asset assigned to employees (Module 28)."""

    asset_tag = models.CharField(max_length=40, db_index=True)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=60, default="IT Equipment")
    serial_number = models.CharField(max_length=80, blank=True, default="")
    assigned_to = models.ForeignKey(
        "organization.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_assets",
    )
    value_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("95000.00"))
    currency = models.CharField(max_length=3, default="BDT")
    status = models.CharField(max_length=24, default="ASSIGNED")

    class Meta:
        unique_together = [("tenant", "company", "asset_tag")]
        indexes = [models.Index(fields=["tenant", "company", "asset_tag"])]


class AssetMovementLedger(LedgerModel):
    """Append-only asset assignment, handover acknowledgment, and return ledger (Module 28)."""

    asset = models.ForeignKey(CompanyAsset, on_delete=models.PROTECT, related_name="movements")
    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="asset_movements")

    class Meta:
        indexes = [models.Index(fields=["tenant", "asset", "posted_on"])]


class HealthSafetyRecord(CompanyOwnedModel, SensitiveFieldMixin):
    """Safety incidents, welfare requests, and restricted encrypted medical notes (Module 29)."""

    SENSITIVE_ENCRYPTED_FIELDS = ("restricted_medical_notes",)

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="health_records")
    record_type = models.CharField(max_length=40, default="SAFETY_DRILL_AND_CHECKUP")
    incident_or_checkup_date = models.DateField()
    restricted_medical_notes = models.TextField(blank=True, default="")
    corrective_action = models.CharField(max_length=255, blank=True, default="Annual occupational health clearance passed.")
    status = models.CharField(max_length=24, default="CLOSED")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "incident_or_checkup_date"])]

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.encrypt_sensitive_fields()
        super().save(*args, **kwargs)


class ResignationRequest(RequestModel):
    """Employee resignation, notice period, exit interview, and last working day (Module 30)."""

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="resignations")
    notice_given_date = models.DateField()
    last_working_day = models.DateField()
    notice_period_days = models.PositiveSmallIntegerField(default=60)
    reason = models.TextField()
    exit_interview_completed = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "status"])]


class FinalSettlement(CompanyOwnedModel):
    """Department clearance & full and final settlement pulling from payroll, leave, loans, PF, and assets (Module 31)."""

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="final_settlements")
    resignation = models.ForeignKey(ResignationRequest, on_delete=models.SET_NULL, null=True, blank=True)
    unpaid_salary_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    leave_encashment_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    pf_and_gratuity_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    loan_recovery_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    asset_deduction_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    net_settlement_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="BDT")
    all_departments_cleared = models.BooleanField(default=True)
    status = models.CharField(max_length=24, default="APPROVED")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "status"])]


class HelpdeskTicket(CompanyOwnedModel):
    """HR Helpdesk service request with SLA timers and escalation tracking (Module 34)."""

    ticket_number = models.CharField(max_length=40, db_index=True)
    requester = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="helpdesk_tickets")
    category = models.CharField(max_length=80, default="Salary & Tax Certificate")
    subject = models.CharField(max_length=200)
    priority = models.CharField(max_length=20, default="NORMAL")  # LOW, NORMAL, HIGH, URGENT
    sla_hours = models.PositiveSmallIntegerField(default=24)
    status = models.CharField(max_length=24, default="OPEN", db_index=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "status"])]
        ordering = ["-created_at"]


class Interview(CompanyOwnedModel):
    """Applicant interview schedule and panel evaluation score (Module 5)."""

    applicant = models.ForeignKey(JobApplicant, on_delete=models.CASCADE, related_name="interviews")
    interviewer = models.ForeignKey(
        "organization.Employee", on_delete=models.SET_NULL, null=True, blank=True, related_name="interviews_conducted"
    )
    scheduled_at = models.DateTimeField()
    round_name = models.CharField(max_length=80, default="Technical & Culture Panel")
    rating_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("85.00"))
    feedback = models.TextField(blank=True, default="")
    status = models.CharField(max_length=24, default="COMPLETED")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "applicant"])]


class Offer(CompanyOwnedModel):
    """Job offer letter and compensation package extended to a selected candidate (Module 5)."""

    applicant = models.ForeignKey(JobApplicant, on_delete=models.CASCADE, related_name="offers")
    offer_number = models.CharField(max_length=40)
    offered_gross_bdt = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="BDT")
    joining_date = models.DateField()
    status = models.CharField(max_length=24, default="ACCEPTED")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "status"])]


class ReviewCycle(CompanyOwnedModel):
    """Company performance appraisal review cycle (Module 23)."""

    name = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()
    include_360_survey = models.BooleanField(default=True)
    status = models.CharField(max_length=24, default="ACTIVE")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "status"])]


class Goal(CompanyOwnedModel):
    """Individual or team KPI goal with weightage and achievement tracking (Module 23)."""

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="goals")
    title = models.CharField(max_length=200)
    weight_pct = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("25.0000"))
    target_metric = models.CharField(max_length=120, default="98% On-Time Delivery")
    achievement_pct = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("94.0000"))
    status = models.CharField(max_length=24, default="ON_TRACK")

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "status"])]


class AppraisalSurvey(CompanyOwnedModel):
    """360-degree feedback questionnaire response (Module 23 & docs/06)."""

    appraisal = models.ForeignKey(PerformanceAppraisal, on_delete=models.CASCADE, related_name="surveys")
    reviewer = models.ForeignKey(
        "organization.Employee", on_delete=models.SET_NULL, null=True, blank=True, related_name="peer_surveys"
    )
    relationship_type = models.CharField(max_length=32, default="PEER")  # SELF, MANAGER, PEER, DIRECT_REPORT
    score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("89.50"))
    responses_json = models.JSONField(default=dict)

    class Meta:
        indexes = [models.Index(fields=["tenant", "appraisal"])]


class TrainingNomination(CompanyOwnedModel):
    """Employee nomination, attendance, and certification for a TrainingProgram (Module 25)."""

    program = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE, related_name="nominations")
    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="training_nominations")
    attended = models.BooleanField(default=True)
    assessment_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("90.00"))
    certificate_issued = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "program", "employee"])]


class ClearanceItem(CompanyOwnedModel):
    """Departmental exit clearance checklist item (IT, Finance, Admin, HR, Line Manager) (Module 31)."""

    settlement = models.ForeignKey(FinalSettlement, on_delete=models.CASCADE, related_name="clearance_items")
    department_name = models.CharField(max_length=100)
    checklist_item = models.CharField(max_length=200)
    is_cleared = models.BooleanField(default=True)
    cleared_at = models.DateTimeField(null=True, blank=True)
    remarks = models.CharField(max_length=255, blank=True, default="Handover verified")

    class Meta:
        indexes = [models.Index(fields=["tenant", "settlement"])]

