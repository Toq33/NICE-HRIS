"""Abstract base models per docs/02-architecture-and-database.md."""
from decimal import Decimal
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from django.utils import timezone

from .context import get_current_tenant_id, get_current_user_id
from .encryption import decrypt_value, encrypt_value, mask_sensitive
from .uuid7 import uuid7


class TenantQuerySet(models.QuerySet):
    """QuerySet that enforces soft-delete instead of hard delete on HR records."""

    def delete(self) -> tuple[int, dict[str, int]]:
        now = timezone.now()
        updated = super().update(deleted_at=now, is_active=False, updated_at=now)
        return updated, {self.model._meta.label: updated}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()


class TenantManager(models.Manager):
    """Auto-scopes every query to the active tenant and filters out soft-deleted rows.

    Per AGENTS.md Section 4: Unscoped queries on tenant models are forbidden.
    If no tenant context is active, returns an empty queryset so cross-tenant leaks
    are impossible by default.
    """

    def get_queryset(self) -> TenantQuerySet:
        qs = TenantQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)
        tenant_id = get_current_tenant_id()
        if tenant_id is None:
            return qs.none()
        return qs.filter(tenant_id=tenant_id)


class UnscopedManager(models.Manager):
    """Used ONLY by Platform Admin, system migrations, and tenant provisioning."""

    def get_queryset(self) -> TenantQuerySet:
        return TenantQuerySet(self.model, using=self._db)


class TenantModel(models.Model):
    """Base model for all tenant-owned tables (docs/02-architecture-and-database.md)."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    tenant = models.ForeignKey(
        "platform_admin.Tenant",
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_set",
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    updated_by = models.UUIDField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = TenantManager()
    unscoped_objects = UnscopedManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def clean(self) -> None:
        super().clean()
        active_tenant_id = get_current_tenant_id()
        if not self.tenant_id and active_tenant_id:
            self.tenant_id = active_tenant_id

    def save(self, *args: Any, **kwargs: Any) -> None:
        active_tenant_id = get_current_tenant_id()
        if not self.tenant_id and active_tenant_id:
            self.tenant_id = active_tenant_id
        if not self.tenant_id:
            raise PermissionDenied("Cannot save a TenantModel without an active tenant_id.")
        if active_tenant_id and str(self.tenant_id) != str(active_tenant_id):
            raise PermissionDenied("Cross-tenant write attempt blocked by TenantModel.")

        user_id = get_current_user_id()
        if user_id:
            if not self.created_by:
                self.created_by = user_id
            self.updated_by = user_id
        super().save(*args, **kwargs)

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        """Soft-delete only for HR records (AGENTS.md Section 4)."""
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["deleted_at", "is_active", "updated_at"])
        return 1, {self._meta.label: 1}


class CompanyOwnedModel(TenantModel):
    """Base model for company-owned records inside a tenant (single or multi-company)."""

    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_set",
        db_index=True,
    )

    class Meta:
        abstract = True


class EffectiveDatedModel(TenantModel):
    """Base model for effective-dated records (salary, designation, department, grade, reporting line).

    Revisions add rows; never overwrite historical rows.
    """

    effective_from = models.DateField(db_index=True)
    effective_to = models.DateField(null=True, blank=True, db_index=True)
    change_reason = models.CharField(max_length=255, blank=True, default="")
    approved_by = models.UUIDField(null=True, blank=True)

    class Meta:
        abstract = True

    def clean(self) -> None:
        super().clean()
        if self.effective_to and self.effective_from and self.effective_to < self.effective_from:
            raise ValidationError({"effective_to": "effective_to must be on or after effective_from."})


class LedgerModel(TenantModel):
    """Append-only ledger base model for leave, loan, fund, and asset balances."""

    posted_on = models.DateField(default=timezone.localdate, db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="BDT")
    quantity = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("0.0000"))
    reason = models.CharField(max_length=255)
    source_type = models.CharField(max_length=64, db_index=True)
    source_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ["-posted_on", "-created_at"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding and self.__class__.unscoped_objects.filter(pk=self.pk).exists():
            raise ValidationError("Ledger entries are append-only and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        raise ValidationError("Ledger entries are append-only and cannot be deleted.")


class RequestModel(CompanyOwnedModel):
    """Base model for workflow-routed requests (leave, overtime, claims, transfers)."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        IN_REVIEW = "IN_REVIEW", "In Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    approval_request_id = models.UUIDField(null=True, blank=True, db_index=True)
    rejection_reason = models.TextField(blank=True, default="")

    class Meta:
        abstract = True


class SensitiveFieldMixin:
    """Mixin for models containing encrypted/masked fields (bank account, national ID, salary, medical)."""

    SENSITIVE_ENCRYPTED_FIELDS: tuple[str, ...] = ()

    def encrypt_sensitive_fields(self) -> None:
        for field_name in self.SENSITIVE_ENCRYPTED_FIELDS:
            val = getattr(self, field_name, None)
            if val:
                setattr(self, field_name, encrypt_value(val))

    def get_decrypted_field(self, field_name: str) -> str:
        val = getattr(self, field_name, None)
        return decrypt_value(val) or ""

    def get_masked_field(self, field_name: str, visible_tail: int = 4) -> str:
        val = getattr(self, field_name, None)
        return mask_sensitive(val, visible_tail=visible_tail)
