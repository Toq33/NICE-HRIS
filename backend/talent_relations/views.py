"""Serializers & ViewSets for Phases 4 & 5: Talent Lifecycle, Relations, Assets, Exit & Helpdesk."""
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from core.permissions import IsTenantMemberAndModuleEnabled
from organization.views import CompanyScopedViewSetMixin

from .models import (
    AppraisalSurvey,
    CareerMovement,
    ClearanceItem,
    CompanyAsset,
    DisciplinaryCase,
    FinalSettlement,
    Goal,
    GrievanceCase,
    HealthSafetyRecord,
    HelpdeskTicket,
    Interview,
    JobApplicant,
    JobRequisition,
    ManpowerPlan,
    Offer,
    OnboardingChecklist,
    PerformanceAppraisal,
    ProbationReview,
    ResignationRequest,
    ReviewCycle,
    TrainingNomination,
    TrainingProgram,
)


class ManpowerPlanSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = ManpowerPlan
        fields = [
            "id",
            "company",
            "department",
            "department_name",
            "fiscal_year",
            "approved_headcount",
            "current_headcount",
            "open_vacancies",
            "annual_budget_bdt",
            "currency",
            "status",
        ]
        read_only_fields = ["id"]


class JobRequisitionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    designation_title = serializers.CharField(source="designation.title", read_only=True)

    class Meta:
        model = JobRequisition
        fields = [
            "id",
            "company",
            "requisition_no",
            "department",
            "department_name",
            "designation",
            "designation_title",
            "title",
            "vacancies_count",
            "employment_type",
            "min_salary_bdt",
            "max_salary_bdt",
            "currency",
            "is_published_on_careers",
            "status",
        ]
        read_only_fields = ["id"]


class JobApplicantSerializer(serializers.ModelSerializer):
    requisition_title = serializers.CharField(source="requisition.title", read_only=True)

    class Meta:
        model = JobApplicant
        fields = [
            "id",
            "company",
            "requisition",
            "requisition_title",
            "full_name",
            "full_name_bn",
            "email",
            "phone",
            "stage",
            "evaluation_score",
            "expected_salary_bdt",
            "currency",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OnboardingChecklistSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = OnboardingChecklist
        fields = [
            "id",
            "company",
            "employee",
            "employee_name",
            "template_name",
            "tasks_json",
            "completion_pct",
            "status",
        ]
        read_only_fields = ["id"]


class ProbationReviewSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = ProbationReview
        fields = [
            "id",
            "company",
            "employee",
            "employee_name",
            "probation_end_date",
            "supervisor_rating",
            "recommendation",
            "remarks",
            "status",
        ]
        read_only_fields = ["id"]


class PerformanceAppraisalSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    department_name = serializers.CharField(source="employee.department.name", read_only=True)

    class Meta:
        model = PerformanceAppraisal
        fields = [
            "id",
            "company",
            "employee",
            "employee_name",
            "department_name",
            "review_cycle",
            "stage",
            "self_score",
            "manager_score",
            "peer_360_score",
            "final_rating",
            "goals_summary",
        ]
        read_only_fields = ["id"]


class CareerMovementSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    new_designation_title = serializers.CharField(source="new_designation.title", read_only=True)

    class Meta:
        model = CareerMovement
        fields = [
            "id",
            "company",
            "employee",
            "employee_name",
            "movement_type",
            "target_company",
            "new_designation",
            "new_designation_title",
            "previous_gross_bdt",
            "revised_gross_bdt",
            "currency",
            "effective_from",
            "effective_to",
            "change_reason",
            "status",
        ]
        read_only_fields = ["id"]


class TrainingProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingProgram
        fields = [
            "id",
            "company",
            "title",
            "category",
            "start_date",
            "end_date",
            "trainer_or_institute",
            "enrolled_count",
            "cost_bdt",
            "currency",
            "status",
        ]
        read_only_fields = ["id"]


class GrievanceCaseSerializer(serializers.ModelSerializer):
    complainant_name = serializers.CharField(source="complainant.full_name", read_only=True)
    handler_name = serializers.CharField(source="assigned_handler.full_name", read_only=True)

    class Meta:
        model = GrievanceCase
        fields = [
            "id",
            "company",
            "case_number",
            "complainant",
            "complainant_name",
            "assigned_handler",
            "handler_name",
            "category",
            "is_confidential",
            "status",
            "resolution_summary",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DisciplinaryCaseSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = DisciplinaryCase
        fields = [
            "id",
            "company",
            "case_number",
            "employee",
            "employee_name",
            "incident_date",
            "allegation_summary",
            "action_taken",
            "status",
        ]
        read_only_fields = ["id"]


class CompanyAssetSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)

    class Meta:
        model = CompanyAsset
        fields = [
            "id",
            "company",
            "asset_tag",
            "name",
            "category",
            "serial_number",
            "assigned_to",
            "assigned_to_name",
            "value_bdt",
            "currency",
            "status",
        ]
        read_only_fields = ["id"]


class HealthSafetyRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    medical_notes_display = serializers.SerializerMethodField()

    class Meta:
        model = HealthSafetyRecord
        fields = [
            "id",
            "company",
            "employee",
            "employee_name",
            "record_type",
            "incident_or_checkup_date",
            "medical_notes_display",
            "corrective_action",
            "status",
        ]
        read_only_fields = ["id"]

    def get_medical_notes_display(self, obj: HealthSafetyRecord) -> str:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and getattr(user, "can_view_medical", False):
            return obj.get_decrypted_field("restricted_medical_notes")
        return "•••••••• (Restricted Medical Data)"


class ResignationRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = ResignationRequest
        fields = [
            "id",
            "company",
            "employee",
            "employee_name",
            "notice_given_date",
            "last_working_day",
            "notice_period_days",
            "reason",
            "exit_interview_completed",
            "status",
        ]
        read_only_fields = ["id"]


class FinalSettlementSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = FinalSettlement
        fields = [
            "id",
            "company",
            "employee",
            "employee_name",
            "unpaid_salary_bdt",
            "leave_encashment_bdt",
            "pf_and_gratuity_bdt",
            "loan_recovery_bdt",
            "asset_deduction_bdt",
            "net_settlement_bdt",
            "currency",
            "all_departments_cleared",
            "status",
        ]
        read_only_fields = ["id"]


class HelpdeskTicketSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source="requester.full_name", read_only=True)

    class Meta:
        model = HelpdeskTicket
        fields = [
            "id",
            "company",
            "ticket_number",
            "requester",
            "requester_name",
            "category",
            "subject",
            "priority",
            "sla_hours",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ManpowerPlanViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ManpowerPlanSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 4

    def get_queryset(self):
        return self.filter_by_company(ManpowerPlan.objects.select_related("department").all())


class JobRequisitionViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = JobRequisitionSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 5

    def get_queryset(self):
        return self.filter_by_company(JobRequisition.objects.select_related("department", "designation").all())


class JobApplicantViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = JobApplicantSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 5
    filterset_fields = ["stage", "requisition"]

    def get_queryset(self):
        return self.filter_by_company(JobApplicant.objects.select_related("requisition").all())


class OnboardingChecklistViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = OnboardingChecklistSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 6

    def get_queryset(self):
        return self.filter_by_company(OnboardingChecklist.objects.select_related("employee").all())


class ProbationReviewViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ProbationReviewSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 7

    def get_queryset(self):
        return self.filter_by_company(ProbationReview.objects.select_related("employee").all())


class PerformanceAppraisalViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = PerformanceAppraisalSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 23

    def get_queryset(self):
        return self.filter_by_company(
            PerformanceAppraisal.objects.select_related("employee", "employee__department").all()
        )


class CareerMovementViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = CareerMovementSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 24

    def get_queryset(self):
        return self.filter_by_company(CareerMovement.objects.select_related("employee", "new_designation").all())


class TrainingProgramViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = TrainingProgramSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 25

    def get_queryset(self):
        return self.filter_by_company(TrainingProgram.objects.all())


class GrievanceCaseViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = GrievanceCaseSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 26

    def get_queryset(self):
        from django.db.models import Q

        qs = self.filter_by_company(
            GrievanceCase.objects.select_related("complainant", "assigned_handler").all()
        )
        user = getattr(self.request, "user", None)
        # Per docs/01 Module 26: Only assigned handlers (or complainant / HR admin with salary/medical clearance) see a confidential case
        if user and not getattr(user, "can_view_salary", False) and not getattr(user, "is_platform_admin", False):
            emp_profile = getattr(user, "employee_profile", None)
            if emp_profile:
                qs = qs.filter(Q(assigned_handler=emp_profile) | Q(complainant=emp_profile))
            else:
                qs = qs.none()
        return qs


class DisciplinaryCaseViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = DisciplinaryCaseSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 27

    def get_queryset(self):
        return self.filter_by_company(DisciplinaryCase.objects.select_related("employee").all())


class CompanyAssetViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = CompanyAssetSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 28

    def get_queryset(self):
        return self.filter_by_company(CompanyAsset.objects.select_related("assigned_to").all())


class HealthSafetyRecordViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = HealthSafetyRecordSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 29

    def get_queryset(self):
        return self.filter_by_company(HealthSafetyRecord.objects.select_related("employee").all())


class ResignationRequestViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ResignationRequestSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 30

    def get_queryset(self):
        return self.filter_by_company(ResignationRequest.objects.select_related("employee").all())


class FinalSettlementViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = FinalSettlementSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 31

    def get_queryset(self):
        return self.filter_by_company(FinalSettlement.objects.select_related("employee").all())


class HelpdeskTicketViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = HelpdeskTicketSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 34

    def get_queryset(self):
        return self.filter_by_company(HelpdeskTicket.objects.select_related("requester").all())


class InterviewSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source="applicant.full_name", read_only=True)

    class Meta:
        model = Interview
        fields = ["id", "company", "applicant", "applicant_name", "interviewer", "scheduled_at", "round_name", "rating_score", "feedback", "status"]
        read_only_fields = ["id"]


class OfferSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source="applicant.full_name", read_only=True)

    class Meta:
        model = Offer
        fields = ["id", "company", "applicant", "applicant_name", "offer_number", "offered_gross_bdt", "currency", "joining_date", "status"]
        read_only_fields = ["id"]


class ReviewCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewCycle
        fields = ["id", "company", "name", "start_date", "end_date", "include_360_survey", "status"]
        read_only_fields = ["id"]


class GoalSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = Goal
        fields = ["id", "company", "employee", "employee_name", "title", "weight_pct", "target_metric", "achievement_pct", "status"]
        read_only_fields = ["id"]


class AppraisalSurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = AppraisalSurvey
        fields = ["id", "company", "appraisal", "reviewer", "relationship_type", "score", "responses_json"]
        read_only_fields = ["id"]


class TrainingNominationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    program_title = serializers.CharField(source="program.title", read_only=True)

    class Meta:
        model = TrainingNomination
        fields = ["id", "company", "program", "program_title", "employee", "employee_name", "attended", "assessment_score", "certificate_issued"]
        read_only_fields = ["id"]


class ClearanceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClearanceItem
        fields = ["id", "company", "settlement", "department_name", "checklist_item", "is_cleared", "cleared_at", "remarks"]
        read_only_fields = ["id"]


class InterviewViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 5

    def get_queryset(self):
        return self.filter_by_company(Interview.objects.select_related("applicant").all())


class OfferViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 5

    def get_queryset(self):
        return self.filter_by_company(Offer.objects.select_related("applicant").all())


class ReviewCycleViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ReviewCycleSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 23

    def get_queryset(self):
        return self.filter_by_company(ReviewCycle.objects.all())


class GoalViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 23
    filterset_fields = ["employee", "status"]

    def get_queryset(self):
        return self.filter_by_company(Goal.objects.select_related("employee").all())


class AppraisalSurveyViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = AppraisalSurveySerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 23

    def get_queryset(self):
        return self.filter_by_company(AppraisalSurvey.objects.all())


class TrainingNominationViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = TrainingNominationSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 25

    def get_queryset(self):
        return self.filter_by_company(TrainingNomination.objects.select_related("program", "employee").all())


class ClearanceItemViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ClearanceItemSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 31

    def get_queryset(self):
        return self.filter_by_company(ClearanceItem.objects.all())

