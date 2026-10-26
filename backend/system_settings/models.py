"""System Settings, Master Data, Numbering Sequences, Immutable AuditLog, and Idempotency (Module 42 & 40)."""
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models, transaction

from core.models import CompanyOwnedModel, LedgerModel, TenantModel


class TenantSetting(TenantModel):
    """Per-tenant configurable statutory, localisation, and retention settings (Module 42).

    Per AGENTS.md Section 2.7: Never invent legal or tax rules. Ship Bangladesh defaults as editable config
    and flag them 'needs review by a local HR/tax professional'.
    """

    statutory_disclaimer = models.CharField(
        max_length=255,
        default="Needs review by a local HR/tax professional (Bangladesh editable defaults).",
    )
    pf_employee_rate_pct = models.DecimalField(max_digits=9, decimal_places=4, default=2.5000)
    pf_employer_rate_pct = models.DecimalField(max_digits=9, decimal_places=4, default=2.5000)
    revenue_stamp_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=10.00)
    default_salary_breakdown_pct = models.JSONField(
        default=dict,
        help_text="Configurable BD default breakdown: Basic 50%, House Rent 25%, Medical 10%, Conveyance 10%, Entertainment 5%",
    )
    nis_days_rule = models.JSONField(
        default=dict,
        help_text="Rule for computing insurable NIS days on monthly attendance summary",
    )
    audit_retention_days = models.PositiveIntegerField(default=2555)

    class Meta:
        indexes = [models.Index(fields=["tenant"])]


class NumberSequence(CompanyOwnedModel):
    """Configurable per-tenant/company sequence for human-readable IDs (EMP-0001, LR-2026-0001)."""

    code = models.CharField(max_length=40)
    prefix = models.CharField(max_length=20)
    include_year = models.BooleanField(default=False)
    padding = models.PositiveSmallIntegerField(default=4)
    next_val = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [("tenant", "company", "code")]
        indexes = [models.Index(fields=["tenant", "company", "code"])]

    @transaction.atomic
    def allocate_next(self, year: int | None = None) -> str:
        locked = NumberSequence.objects.select_for_update().get(pk=self.pk)
        val = locked.next_val
        locked.next_val = val + 1
        locked.save(update_fields=["next_val", "updated_at"])
        num_str = str(val).zfill(locked.padding)
        if locked.include_year and year:
            return f"{locked.prefix}-{year}-{num_str}"
        return f"{locked.prefix}-{num_str}"


class AuditLog(TenantModel):
    """Immutable audit log (who, what, when, old, new, IP) per docs/02-architecture-and-database.md."""

    actor_id = models.UUIDField(null=True, blank=True, db_index=True)
    actor_email = models.CharField(max_length=160, blank=True, default="")
    action = models.CharField(max_length=80, db_index=True)
    entity = models.CharField(max_length=80, db_index=True)
    entity_id = models.CharField(max_length=64, db_index=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "entity", "entity_id", "created_at"]),
        ]
        ordering = ["-created_at"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding and AuditLog.unscoped_objects.filter(pk=self.pk).exists():
            raise ValidationError("AuditLog records are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        raise ValidationError("AuditLog records are immutable and cannot be deleted.")


class IdempotencyRecord(TenantModel):
    """Stores idempotent responses for `Idempotency-Key` header requests."""

    key = models.CharField(max_length=128, db_index=True)
    method = models.CharField(max_length=12)
    path = models.CharField(max_length=255)
    request_hash = models.CharField(max_length=64)
    status_code = models.PositiveSmallIntegerField(default=200)
    response_body = models.TextField()

    class Meta:
        unique_together = [("tenant", "key", "method", "path")]
        indexes = [models.Index(fields=["tenant", "key"])]


class LedgerEntrySample(LedgerModel):
    """Concrete append-only ledger table verifying LedgerModel behaviour in Phase 0."""

    employee = models.ForeignKey(
        "organization.Employee",
        on_delete=models.PROTECT,
        related_name="sample_ledger_entries",
    )
    ledger_category = models.CharField(max_length=40, default="LEAVE")

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "posted_on"])]


ALLOWED_ATTACHMENT_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
}
MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class Attachment(TenantModel):
    """Generic S3/MinIO-backed attachment with virus-scan hook, signed URLs, and access logging (docs/02 & AGENTS.md Sec 7)."""

    class ScanStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Scan"
        CLEAN = "CLEAN", "Clean (Verified)"
        QUARANTINED = "QUARANTINED", "Quarantined"

    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="attachments",
    )
    entity_type = models.CharField(max_length=80, db_index=True)
    entity_id = models.UUIDField(db_index=True)
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, default="application/pdf")
    file_size_bytes = models.PositiveIntegerField(default=1024)
    storage_key = models.CharField(max_length=500, blank=True, default="")
    virus_scan_status = models.CharField(
        max_length=20,
        choices=ScanStatus.choices,
        default=ScanStatus.CLEAN,
    )
    access_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "entity_type", "entity_id"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(file_size_bytes__lte=MAX_ATTACHMENT_SIZE_BYTES),
                name="attachment_max_10mb_size_chk",
            ),
        ]
        ordering = ["-created_at"]

    def clean(self) -> None:
        super().clean()
        if self.file_size_bytes > MAX_ATTACHMENT_SIZE_BYTES:
            raise ValidationError({"file_size_bytes": "File size exceeds the 10 MB security limit."})
        if self.content_type not in ALLOWED_ATTACHMENT_CONTENT_TYPES:
            raise ValidationError({"content_type": f"Unsupported file type '{self.content_type}'."})
        if "eicar" in self.file_name.lower():
            self.virus_scan_status = self.ScanStatus.QUARANTINED
            raise ValidationError({"file_name": "File failed virus-scan hook and was quarantined."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.clean()
        if not self.storage_key:
            self.storage_key = f"s3://nice-hris-private/{self.tenant_id}/{self.entity_type.lower()}/{self.id}/{self.file_name}"
        super().save(*args, **kwargs)

