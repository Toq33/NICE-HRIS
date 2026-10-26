"""Platform-level models: Plan, Tenant, EnabledModule (docs/01-modules.md & docs/02-architecture-and-database.md)."""
from decimal import Decimal

from django.db import models

from core.uuid7 import uuid7


class Plan(models.Model):
    """SaaS subscription plan managed by Platform Admin."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    max_employees = models.PositiveIntegerField(default=100)
    max_companies = models.PositiveIntegerField(default=1)
    monthly_price_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="BDT")
    default_module_numbers = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["monthly_price_bdt"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Tenant(models.Model):
    """Subscribing client organization.

    Supports both single-company and multi-company mode from the same schema:
    - Single-company tenant (`multi_company_enabled=False`, 1 Company): never sees company switchers/filters.
    - Multi-company tenant (`multi_company_enabled=True`, 1..N Companies): gets company switcher, inter-company transfers, consolidated reports.
    """

    class Status(models.TextChoices):
        TRIAL = "TRIAL", "Trial"
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    name = models.CharField(max_length=200)
    name_bn = models.CharField(max_length=200, blank=True, default="")
    slug = models.SlugField(max_length=80, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="tenants")
    multi_company_enabled = models.BooleanField(default=False)
    employee_limit = models.PositiveIntegerField(default=100)
    primary_domain = models.CharField(max_length=255, blank=True, default="")
    default_currency = models.CharField(max_length=3, default="BDT")
    default_timezone = models.CharField(max_length=64, default="Asia/Dhaka")
    lakh_grouping_enabled = models.BooleanField(default=True)
    weekly_off_days = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


class EnabledModule(models.Model):
    """Controls which of the 42 modules are enabled for a specific tenant."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="enabled_modules")
    module_number = models.PositiveSmallIntegerField(db_index=True)
    module_slug = models.SlugField(max_length=80)
    module_name = models.CharField(max_length=150)
    module_group = models.CharField(max_length=80, default="General")
    phase = models.CharField(max_length=20, default="0")
    is_enabled = models.BooleanField(default=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant", "module_number"), ("tenant", "module_slug")]
        indexes = [
            models.Index(fields=["tenant", "is_enabled"]),
            models.Index(fields=["tenant", "module_number"]),
        ]
        ordering = ["module_number"]

    def __str__(self) -> str:
        state = "ON" if self.is_enabled else "OFF"
        return f"[{self.tenant.slug}] #{self.module_number} {self.module_name}: {state}"
