"""Tenant organizational hierarchy and Employee baseline (docs/02-architecture-and-database.md).

Hierarchy: Tenant > Company (legal entity, 1..n) > Branch > Department > Section > Designation / Grade / Cost Center > Employee.
"""
from decimal import Decimal
from typing import Any

from django.db import models

from core.models import CompanyOwnedModel, EffectiveDatedModel, SensitiveFieldMixin, TenantModel


class Company(TenantModel):
    """Legal entity inside a tenant (1 in single-company mode, 1..N in multi-company mode)."""

    name = models.CharField(max_length=200)
    name_bn = models.CharField(max_length=200, blank=True, default="")
    code = models.CharField(max_length=32)
    registration_no = models.CharField(max_length=80, blank=True, default="")
    tin_number = models.CharField(max_length=80, blank=True, default="")
    address = models.TextField(blank=True, default="")
    currency = models.CharField(max_length=3, default="BDT")
    timezone = models.CharField(max_length=64, default="Asia/Dhaka")
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = [("tenant", "code")]
        indexes = [models.Index(fields=["tenant", "code"])]
        ordering = ["-is_primary", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Branch(CompanyOwnedModel):
    """Physical location or office branch belonging to a Company."""

    name = models.CharField(max_length=150)
    name_bn = models.CharField(max_length=150, blank=True, default="")
    code = models.CharField(max_length=32)
    city = models.CharField(max_length=80, default="Dhaka")
    address = models.TextField(blank=True, default="")
    latitude = models.DecimalField(max_digits=9, decimal_places=4, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=4, null=True, blank=True)
    geofence_radius_meters = models.PositiveIntegerField(default=200)

    class Meta:
        unique_together = [("tenant", "company", "code")]
        indexes = [models.Index(fields=["tenant", "company", "code"])]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.city})"


class Department(CompanyOwnedModel):
    """Department inside a Company."""

    name = models.CharField(max_length=150)
    name_bn = models.CharField(max_length=150, blank=True, default="")
    code = models.CharField(max_length=32)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True, blank=True, related_name="departments")
    approved_headcount = models.PositiveIntegerField(default=15)

    class Meta:
        unique_together = [("tenant", "company", "code")]
        indexes = [models.Index(fields=["tenant", "company", "code"])]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Section(CompanyOwnedModel):
    """Sub-unit inside a Department."""

    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="sections")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=32)

    class Meta:
        unique_together = [("tenant", "department", "code")]
        indexes = [models.Index(fields=["tenant", "department"])]
        ordering = ["name"]


class Grade(CompanyOwnedModel):
    """Salary / Job Grade."""

    name = models.CharField(max_length=80)
    code = models.CharField(max_length=32)
    rank_order = models.PositiveSmallIntegerField(default=1)
    min_gross_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    max_gross_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="BDT")

    class Meta:
        unique_together = [("tenant", "company", "code")]
        indexes = [models.Index(fields=["tenant", "company", "rank_order"])]
        ordering = ["rank_order"]


class Designation(CompanyOwnedModel):
    """Job title / Designation."""

    title = models.CharField(max_length=150)
    title_bn = models.CharField(max_length=150, blank=True, default="")
    code = models.CharField(max_length=32)
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True, related_name="designations")

    class Meta:
        unique_together = [("tenant", "company", "code")]
        indexes = [models.Index(fields=["tenant", "company", "code"])]
        ordering = ["title"]


class CostCenter(CompanyOwnedModel):
    """Financial cost center for payroll and expense allocation."""

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=32)
    budget_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="BDT")

    class Meta:
        unique_together = [("tenant", "company", "code")]
        indexes = [models.Index(fields=["tenant", "company", "code"])]
        ordering = ["code"]


class Employee(CompanyOwnedModel, SensitiveFieldMixin):
    """Core Employee record with English and Bangla names, encrypted National ID & Bank Account, and salary masking."""

    class EmploymentStatus(models.TextChoices):
        PROBATION = "PROBATION", "Probation"
        PERMANENT = "PERMANENT", "Permanent"
        CONTRACT = "CONTRACT", "Contract"
        NOTICE_PERIOD = "NOTICE_PERIOD", "On Notice"
        SEPARATED = "SEPARATED", "Separated"

    SENSITIVE_ENCRYPTED_FIELDS = ("national_id_encrypted", "bank_account_encrypted")

    employee_code = models.CharField(max_length=40, db_index=True)
    full_name = models.CharField(max_length=160)
    full_name_bn = models.CharField(max_length=160, blank=True, default="")
    work_email = models.EmailField()
    phone = models.CharField(max_length=32)
    joining_date = models.DateField(db_index=True)
    employment_status = models.CharField(
        max_length=24,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.PERMANENT,
        db_index=True,
    )

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="employees")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="employees")
    designation = models.ForeignKey(Designation, on_delete=models.PROTECT, related_name="employees")
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    cost_center = models.ForeignKey(
        CostCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees"
    )
    manager = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="direct_reports"
    )
    user = models.OneToOneField(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="employee_profile"
    )

    # Restricted / Sensitive fields (AGENTS.md Section 7)
    gross_salary_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="BDT")
    national_id_encrypted = models.CharField(max_length=512, blank=True, default="")
    bank_name = models.CharField(max_length=120, blank=True, default="BRAC Bank PLC")
    bank_account_encrypted = models.CharField(max_length=512, blank=True, default="")
    blood_group = models.CharField(max_length=8, blank=True, default="O+")

    class Meta:
        unique_together = [("tenant", "company", "employee_code")]
        indexes = [
            models.Index(fields=["tenant", "company", "employee_code"]),
            models.Index(fields=["tenant", "department"]),
            models.Index(fields=["tenant", "employment_status"]),
            models.Index(
                fields=["tenant", "company"],
                name="emp_active_tenant_comp_idx",
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(gross_salary_bdt__gte=Decimal("0.00")),
                name="employee_non_negative_gross_salary_chk",
            ),
        ]
        ordering = ["employee_code"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.encrypt_sensitive_fields()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.employee_code} - {self.full_name}"


class ReportingLine(EffectiveDatedModel):
    """Effective-dated reporting line history (docs/02-architecture-and-database.md)."""

    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="reporting_history")
    manager = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="subordinate_history")

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "employee", "effective_from"]),
            models.Index(
                fields=["tenant", "employee"],
                name="repline_current_emp_idx",
                condition=models.Q(effective_to__isnull=True, deleted_at__isnull=True),
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=models.F("effective_from")),
                name="repline_valid_effective_range_chk",
            ),
        ]
        ordering = ["-effective_from"]


class EmergencyContact(TenantModel):
    """Employee emergency contact details (Module 3)."""

    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="emergency_contacts")
    name = models.CharField(max_length=160)
    relationship = models.CharField(max_length=60)
    phone = models.CharField(max_length=32)
    address = models.CharField(max_length=255, blank=True, default="")
    is_primary = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee"])]


class FamilyMember(TenantModel):
    """Employee family dependent and PF/Gratuity/Insurance nominee (Module 3)."""

    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="family_members")
    full_name = models.CharField(max_length=160)
    relationship = models.CharField(max_length=60)
    date_of_birth = models.DateField(null=True, blank=True)
    is_nominee = models.BooleanField(default=True)
    nominee_share_pct = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("100.0000"))

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee"])]


class EmployeeQualification(TenantModel):
    """Academic or professional qualification record (Module 3)."""

    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="qualifications")
    degree_or_certification = models.CharField(max_length=160)
    institution = models.CharField(max_length=200)
    passing_year = models.PositiveSmallIntegerField(default=2020)
    result_or_cgpa = models.CharField(max_length=40, default="CGPA 3.75 / 4.00")

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee"])]


class EmployeeExperience(TenantModel):
    """Prior employment history record (Module 3)."""

    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="experiences")
    employer_name = models.CharField(max_length=200)
    designation_held = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    responsibilities = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee"])]


class EmploymentRecord(EffectiveDatedModel):
    """Effective-dated contract & legal-entity employment record supporting inter-company transfers (Module 2, 3, 24)."""

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="employment_records")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="employment_records")
    contract_reference = models.CharField(max_length=60)
    contract_type = models.CharField(max_length=40, default="PERMANENT")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="employment_records")
    designation = models.ForeignKey(Designation, on_delete=models.PROTECT, related_name="employment_records")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="employment_records")
    status = models.CharField(max_length=24, default="RUNNING")

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "employee", "effective_from"]),
            models.Index(
                fields=["tenant", "employee"],
                name="emprec_current_emp_idx",
                condition=models.Q(effective_to__isnull=True, deleted_at__isnull=True),
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=models.F("effective_from")),
                name="emprec_valid_effective_range_chk",
            ),
        ]
        ordering = ["-effective_from"]


class EmployeeDocument(TenantModel):
    """Employee dossier document metadata (NID copy, TIN certificate, academic certificates, signed contract) (Module 3)."""

    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="documents")
    document_type = models.CharField(max_length=60, default="NATIONAL_ID")
    title = models.CharField(max_length=180)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    storage_key = models.CharField(max_length=500, blank=True, default="")
    is_verified = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "document_type"])]

