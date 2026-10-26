"""Shared Engines: Approval Workflow Engine (Mod 37), Policies & Letters (Mod 35), Announcements & Notifications (Mod 36), Reports (Mod 38)."""
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models

from core.models import CompanyOwnedModel, TenantModel


class WorkflowDefinition(TenantModel):
    """Configurable approval chain per module and request type (Module 37)."""

    name = models.CharField(max_length=150)
    code = models.SlugField(max_length=60)
    module_number = models.PositiveSmallIntegerField(db_index=True)
    request_type = models.CharField(max_length=60, db_index=True)
    min_amount_threshold = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    steps_config = models.JSONField(
        default=list,
        help_text="Ordered list of steps e.g. [{'step': 1, 'role': 'line-manager', 'sla_hours': 24}, {'step': 2, 'role': 'hr-director', 'sla_hours': 48}]",
    )

    class Meta:
        unique_together = [("tenant", "code")]
        indexes = [models.Index(fields=["tenant", "module_number", "request_type"])]
        ordering = ["module_number", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.request_type})"


class ApprovalRequest(CompanyOwnedModel):
    """Generic approval request raised by any module (Leave, Overtime, Payroll, Expense, Loan, Promotion, Exit)."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Approval"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        ESCALATED = "ESCALATED", "Escalated"

    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.PROTECT, related_name="requests")
    module_number = models.PositiveSmallIntegerField(db_index=True)
    subject_type = models.CharField(max_length=80, db_index=True)
    subject_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=220)
    requester_employee = models.ForeignKey(
        "organization.Employee",
        on_delete=models.PROTECT,
        related_name="submitted_approvals",
    )
    current_approver = models.ForeignKey(
        "organization.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pending_approvals",
    )
    current_step = models.PositiveSmallIntegerField(default=1)
    total_steps = models.PositiveSmallIntegerField(default=1)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="BDT")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    rejection_reason = models.TextField(blank=True, default="")
    decided_at = models.DateTimeField(null=True, blank=True)
    summary_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "status", "current_approver"]),
            models.Index(fields=["tenant", "subject_type", "subject_id"]),
        ]
        ordering = ["-created_at"]


class ApprovalDecision(TenantModel):
    """Append-only step decision log on an ApprovalRequest (Module 37)."""

    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name="decisions")
    step_number = models.PositiveSmallIntegerField(default=1)
    actor_employee = models.ForeignKey(
        "organization.Employee",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approval_decisions",
    )
    decision = models.CharField(max_length=20)  # APPROVED, REJECTED, DELEGATED
    comments = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["tenant", "approval_request", "step_number"])]
        ordering = ["created_at"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding and ApprovalDecision.unscoped_objects.filter(pk=self.pk).exists():
            raise ValidationError("Approval decisions are append-only and cannot be modified.")
        if self.decision == "REJECTED" and not self.comments.strip():
            raise ValidationError("Rejection reason is mandatory when rejecting an approval request.")
        super().save(*args, **kwargs)


class PolicyDocument(CompanyOwnedModel):
    """Company HR Policy repository with version control and acknowledgment tracking (Module 35)."""

    title = models.CharField(max_length=200)
    title_bn = models.CharField(max_length=200, blank=True, default="")
    category = models.CharField(max_length=80, default="General HR Policy")
    version = models.CharField(max_length=20, default="1.0")
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    content_markdown = models.TextField()
    requires_acknowledgment = models.BooleanField(default=True)
    acknowledged_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "category"])]
        ordering = ["-effective_date"]


class LetterTemplate(CompanyOwnedModel):
    """Merge-field HR letter templates in English and Bangla (Appointment, Confirmation, Increment, Experience, NOC) (Module 35)."""

    name = models.CharField(max_length=150)
    code = models.SlugField(max_length=60)
    letter_type = models.CharField(max_length=60, default="APPOINTMENT")
    version = models.PositiveSmallIntegerField(default=1)
    language = models.CharField(max_length=10, default="EN")  # EN or BN
    body_template = models.TextField(
        help_text="Supports placeholders like {{employee_name}}, {{designation}}, {{joining_date}}, {{gross_salary}}"
    )

    class Meta:
        unique_together = [("tenant", "company", "code", "version")]
        indexes = [models.Index(fields=["tenant", "company", "letter_type"])]


class GeneratedLetter(CompanyOwnedModel):
    """Issued HR letter storing exact merge data and template version snapshot (Module 35)."""

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="issued_letters")
    template = models.ForeignKey(LetterTemplate, on_delete=models.PROTECT, related_name="generated_letters")
    template_version = models.PositiveSmallIntegerField(default=1)
    reference_no = models.CharField(max_length=60)
    merge_data = models.JSONField(default=dict)
    rendered_html = models.TextField()

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "created_at"])]


class Announcement(CompanyOwnedModel):
    """Company & Department notices, events, and celebratory reminders (Module 36)."""

    title = models.CharField(max_length=200)
    title_bn = models.CharField(max_length=200, blank=True, default="")
    category = models.CharField(max_length=40, default="NOTICE")  # NOTICE, EVENT, HOLIDAY, CELEBRATION
    body = models.TextField()
    department = models.ForeignKey(
        "organization.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements",
    )
    is_pinned = models.BooleanField(default=False)
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "published_at"])]
        ordering = ["-is_pinned", "-published_at"]


class Notification(TenantModel):
    """Event-driven user notification (in-app + email) (Module 36)."""

    recipient = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    channel = models.CharField(max_length=20, default="IN_APP")
    action_url = models.CharField(max_length=255, blank=True, default="")
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "recipient", "is_read", "created_at"])]
        ordering = ["-created_at"]


class ReportDefinition(TenantModel):
    """Reusable analytics report definition supporting screen, Excel, and PDF export (Module 38)."""

    name = models.CharField(max_length=160)
    code = models.SlugField(max_length=60)
    module_number = models.PositiveSmallIntegerField(default=38)
    category = models.CharField(max_length=60, default="Workforce")
    columns_config = models.JSONField(default=list)
    default_filters = models.JSONField(default=dict)
    schedule_cron = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        unique_together = [("tenant", "code")]
        indexes = [models.Index(fields=["tenant", "category"])]
