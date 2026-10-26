"""Serializers & ViewSets for Modules 35, 36, 37, and 38."""
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from core.permissions import IsTenantMemberAndModuleEnabled
from organization.views import CompanyScopedViewSetMixin

from .models import (
    Announcement,
    ApprovalDecision,
    ApprovalRequest,
    GeneratedLetter,
    LetterTemplate,
    Notification,
    PolicyDocument,
    ReportDefinition,
    WorkflowDefinition,
)
from .services import build_report_excel_bytes, decide_approval_request


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDefinition
        fields = [
            "id",
            "name",
            "code",
            "module_number",
            "request_type",
            "min_amount_threshold",
            "steps_config",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ApprovalDecisionSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor_employee.full_name", read_only=True)

    class Meta:
        model = ApprovalDecision
        fields = ["id", "step_number", "actor_employee", "actor_name", "decision", "comments", "created_at"]


class ApprovalRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source="requester_employee.full_name", read_only=True)
    current_approver_name = serializers.CharField(source="current_approver.full_name", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    decisions = ApprovalDecisionSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = [
            "id",
            "company",
            "company_name",
            "workflow",
            "module_number",
            "subject_type",
            "subject_id",
            "title",
            "requester_employee",
            "requester_name",
            "current_approver",
            "current_approver_name",
            "current_step",
            "total_steps",
            "amount",
            "currency",
            "status",
            "rejection_reason",
            "decided_at",
            "summary_payload",
            "decisions",
            "created_at",
        ]
        read_only_fields = ["id", "decided_at", "created_at"]


class PolicyDocumentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = PolicyDocument
        fields = [
            "id",
            "company",
            "company_name",
            "title",
            "title_bn",
            "category",
            "version",
            "effective_date",
            "expiry_date",
            "content_markdown",
            "requires_acknowledgment",
            "acknowledged_count",
            "created_at",
        ]
        read_only_fields = ["id", "acknowledged_count", "created_at"]


class LetterTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterTemplate
        fields = [
            "id",
            "company",
            "name",
            "code",
            "letter_type",
            "version",
            "language",
            "body_template",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class GeneratedLetterSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)

    class Meta:
        model = GeneratedLetter
        fields = [
            "id",
            "company",
            "employee",
            "employee_name",
            "template",
            "template_name",
            "template_version",
            "reference_no",
            "merge_data",
            "rendered_html",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AnnouncementSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Announcement
        fields = [
            "id",
            "company",
            "company_name",
            "department",
            "department_name",
            "title",
            "title_bn",
            "category",
            "body",
            "is_pinned",
            "published_at",
        ]
        read_only_fields = ["id", "published_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "channel", "action_url", "is_read", "created_at"]
        read_only_fields = ["id", "created_at"]


class ReportDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportDefinition
        fields = [
            "id",
            "name",
            "code",
            "module_number",
            "category",
            "columns_config",
            "default_filters",
            "schedule_cron",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class WorkflowDefinitionViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowDefinitionSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 37

    def get_queryset(self):
        return WorkflowDefinition.objects.all()


class ApprovalRequestViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ApprovalRequestSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 37
    filterset_fields = ["status", "module_number", "subject_type"]

    def get_queryset(self):
        qs = ApprovalRequest.objects.select_related(
            "company", "requester_employee", "current_approver"
        ).prefetch_related("decisions")
        return self.filter_by_company(qs)

    @extend_schema(summary="Approve or Reject an ApprovalRequest (rejection requires reason)")
    @action(detail=True, methods=["post"])
    def decide(self, request: Request, pk: str = None) -> Response:
        req = self.get_object()
        decision = request.data.get("decision", "APPROVED")
        comments = request.data.get("comments", "")
        actor_emp = getattr(request.user, "employee_profile", None)
        updated = decide_approval_request(
            approval_request=req,
            decision=decision,
            comments=comments,
            actor_employee=actor_emp,
        )
        return Response(ApprovalRequestSerializer(updated).data, status=status.HTTP_200_OK)


class PolicyDocumentViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = PolicyDocumentSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 35

    def get_queryset(self):
        return self.filter_by_company(PolicyDocument.objects.select_related("company").all())

    @action(detail=True, methods=["post"])
    def acknowledge(self, request: Request, pk: str = None) -> Response:
        policy = self.get_object()
        policy.acknowledged_count += 1
        policy.save(update_fields=["acknowledged_count", "updated_at"])
        return Response(PolicyDocumentSerializer(policy).data)


class LetterTemplateViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = LetterTemplateSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 35

    def get_queryset(self):
        return self.filter_by_company(LetterTemplate.objects.all())


class GeneratedLetterViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = GeneratedLetterSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 35

    def get_queryset(self):
        return self.filter_by_company(GeneratedLetter.objects.select_related("employee", "template").all())


class AnnouncementViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 36

    def get_queryset(self):
        return self.filter_by_company(Announcement.objects.select_related("company", "department").all())


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request: Request, pk: str = None) -> Response:
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=["is_read", "updated_at"])
        return Response(NotificationSerializer(notif).data)


class ReportDefinitionViewSet(viewsets.ModelViewSet):
    serializer_class = ReportDefinitionSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 38

    def get_queryset(self):
        return ReportDefinition.objects.all()

    @extend_schema(summary="Export report definition as an Excel (.xlsx) file via openpyxl")
    @action(detail=True, methods=["get"], url_path="export-xlsx")
    def export_xlsx(self, request: Request, pk: str = None):
        from django.http import HttpResponse

        report = self.get_object()
        xlsx_bytes = build_report_excel_bytes(report)
        response = HttpResponse(
            xlsx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{report.code}.xlsx"'
        return response
