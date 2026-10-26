"""Phase 3 Payroll & Compensation Models (Modules 14, 15, 16, 17, 18, 19, 20, 21, 22)."""
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models

from core.models import CompanyOwnedModel, EffectiveDatedModel, LedgerModel, RequestModel


class SalaryComponent(CompanyOwnedModel):
    """Configurable earnings, deductions, and employer contribution components (Module 14)."""

    class ComponentType(models.TextChoices):
        EARNING = "EARNING", "Earning"
        DEDUCTION = "DEDUCTION", "Deduction"
        EMPLOYER_CONTRIBUTION = "EMPLOYER_CONTRIBUTION", "Employer Contribution"

    name = models.CharField(max_length=120)
    name_bn = models.CharField(max_length=120, blank=True, default="")
    code = models.CharField(max_length=32)
    component_type = models.CharField(max_length=28, choices=ComponentType.choices, default=ComponentType.EARNING)
    formula_type = models.CharField(
        max_length=28,
        default="PCT_OF_GROSS",
        help_text="PCT_OF_GROSS, PCT_OF_BASIC, FIXED_AMOUNT",
    )
    rate_or_amount = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))
    currency = models.CharField(max_length=3, default="BDT")
    is_taxable = models.BooleanField(default=True)

    class Meta:
        unique_together = [("tenant", "company", "code")]
        indexes = [models.Index(fields=["tenant", "company", "code"])]
        ordering = ["component_type", "code"]


class EmployeeSalaryStructure(EffectiveDatedModel):
    """Effective-dated employee salary assignment. Revisions add a new row; never overwrite old ones (Module 14)."""

    company = models.ForeignKey("organization.Company", on_delete=models.PROTECT, related_name="salary_structures")
    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="salary_history")
    gross_amount = models.DecimalField(max_digits=14, decimal_places=2)
    basic_amount = models.DecimalField(max_digits=14, decimal_places=2)
    house_rent_amount = models.DecimalField(max_digits=14, decimal_places=2)
    medical_amount = models.DecimalField(max_digits=14, decimal_places=2)
    conveyance_amount = models.DecimalField(max_digits=14, decimal_places=2)
    entertainment_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="BDT")

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "employee", "effective_from"]),
            models.Index(
                fields=["tenant", "employee"],
                name="salstruct_current_emp_idx",
                condition=models.Q(effective_to__isnull=True, deleted_at__isnull=True),
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(gross_amount__gte=Decimal("0.00")),
                name="salstruct_non_negative_gross_chk",
            ),
            models.CheckConstraint(
                condition=models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=models.F("effective_from")),
                name="salstruct_valid_effective_range_chk",
            ),
        ]
        ordering = ["-effective_from"]


class StatutoryScheme(EffectiveDatedModel):
    """Configurable Statutory Social Security / NIS scheme (Module 20 & docs/02).

    Flagged 'needs review by a local payroll/legal professional'.
    """

    company = models.ForeignKey("organization.Company", on_delete=models.PROTECT, related_name="statutory_schemes")
    name = models.CharField(max_length=150, default="National Insurance / Social Security Scheme (NIS)")
    code = models.CharField(max_length=32, default="NIS")
    employee_rate_pct = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("1.0000"))
    employer_rate_pct = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("2.0000"))
    wage_ceiling_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("100000.00"))
    wage_floor_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("10000.00"))
    currency = models.CharField(max_length=3, default="BDT")
    review_flag = models.CharField(
        max_length=255,
        default="Needs review by a local payroll/legal professional",
    )

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "code"])]


class TaxSlab(CompanyOwnedModel):
    """Configurable income tax slab table per income year (Module 20)."""

    income_year = models.CharField(max_length=20, default="2026-2027")
    slab_order = models.PositiveSmallIntegerField(default=1)
    threshold_amount_bdt = models.DecimalField(max_digits=14, decimal_places=2)
    tax_rate_pct = models.DecimalField(max_digits=9, decimal_places=4)
    currency = models.CharField(max_length=3, default="BDT")
    review_flag = models.CharField(
        max_length=255,
        default="Needs review by a local HR/tax professional",
    )

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "income_year", "slab_order"])]
        ordering = ["income_year", "slab_order"]


class PayrollPeriod(CompanyOwnedModel):
    """Monthly payroll period. Once locked, immutable (Module 15)."""

    name = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_locked = models.BooleanField(default=False, db_index=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("tenant", "company", "year", "month")]
        indexes = [models.Index(fields=["tenant", "company", "year", "month"])]
        ordering = ["-year", "-month"]


class PayrollRun(CompanyOwnedModel):
    """Batch payroll calculation run with frozen snapshots and period locking (Module 15)."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft / Preview"
        VALIDATED = "VALIDATED", "Validated"
        APPROVED = "APPROVED", "Approved"
        LOCKED = "LOCKED", "Locked & Disbursed"

    period = models.ForeignKey(PayrollPeriod, on_delete=models.PROTECT, related_name="payroll_runs")
    run_number = models.CharField(max_length=40)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    employee_count = models.PositiveIntegerField(default=0)
    total_gross_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_deductions_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_net_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="BDT")
    total_net_in_words = models.CharField(max_length=350, blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "period"])]
        ordering = ["-created_at"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            old = PayrollRun.unscoped_objects.filter(pk=self.pk).first()
            if old and old.status == PayrollRun.Status.LOCKED:
                raise ValidationError("Locked payroll runs are immutable. Post adjustments in a subsequent period.")
        super().save(*args, **kwargs)


class Payslip(CompanyOwnedModel):
    """Individual employee payslip storing frozen input snapshot, earnings, deductions, and NIS days (Module 15 & 22)."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        DONE = "DONE", "Done"
        PAID = "PAID", "Paid"

    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="payslips")
    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="payslips")
    payslip_number = models.CharField(max_length=40, db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DONE)

    # Frozen input snapshot
    salary_days = models.PositiveSmallIntegerField(default=30)
    present_days = models.PositiveSmallIntegerField(default=22)
    absent_days = models.PositiveSmallIntegerField(default=0)
    nis_days = models.PositiveSmallIntegerField(default=26)

    # Earnings NUMERIC(14,2)
    basic_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    house_rent_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    medical_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    conveyance_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    entertainment_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    overtime_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    gross_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    # Deductions NUMERIC(14,2)
    pf_employee_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    pf_employer_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    nis_employee_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    nis_employer_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    ait_tax_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    loan_recovery_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    revenue_stamp_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("10.00"))
    total_deductions_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    net_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="BDT")
    net_in_words = models.CharField(max_length=350, blank=True, default="")
    snapshot_json = models.JSONField(default=dict)

    class Meta:
        unique_together = [("payroll_run", "employee")]
        indexes = [models.Index(fields=["payroll_run", "employee"])]
        ordering = ["employee__employee_code"]


class BonusRun(CompanyOwnedModel):
    """Festival (Eid-ul-Fitr, Eid-ul-Adha), performance, and sales bonus batches (Module 16)."""

    name = models.CharField(max_length=160)
    bonus_type = models.CharField(max_length=40, default="FESTIVAL_EID")
    effective_date = models.DateField()
    pct_of_basic = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("100.0000"))
    total_amount_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="BDT")
    status = models.CharField(max_length=20, default="APPROVED")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "effective_date"])]


class ExpenseClaim(RequestModel):
    """Mobile, transport, meal, travel, and medical reimbursement claims (Module 17)."""

    reference_no = models.CharField(max_length=40, db_index=True)
    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="expense_claims")
    category = models.CharField(max_length=40, default="TRANSPORT")  # MOBILE, TRANSPORT, MEALS, TRAVEL, MEDICAL
    claim_date = models.DateField()
    amount_bdt = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="BDT")
    description = models.TextField()

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "status"])]


class EmployeeLoan(RequestModel):
    """Employee loan or salary advance with installment schedule and append-only ledger balance (Module 18)."""

    loan_number = models.CharField(max_length=40, db_index=True)
    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="loans")
    loan_type = models.CharField(max_length=40, default="SALARY_ADVANCE")
    principal_bdt = models.DecimalField(max_digits=14, decimal_places=2)
    monthly_installment_bdt = models.DecimalField(max_digits=14, decimal_places=2)
    total_installments = models.PositiveSmallIntegerField(default=6)
    disbursed_on = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="BDT")

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "status"])]


class LoanLedger(LedgerModel):
    """Append-only loan balance ledger (DISBURSEMENT +, INSTALLMENT_RECOVERY -, EARLY_SETTLEMENT -) (Module 18)."""

    loan = models.ForeignKey(EmployeeLoan, on_delete=models.PROTECT, related_name="ledger_entries")
    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="loan_ledger_entries")

    class Meta:
        indexes = [models.Index(fields=["tenant", "loan", "posted_on"])]


class ProvidentFundLedger(LedgerModel):
    """Append-only Provident Fund & Gratuity ledger (EMPLOYEE_CONTRIBUTION, EMPLOYER_CONTRIBUTION, PROFIT, SETTLEMENT) (Module 19)."""

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="pf_ledger_entries")
    contribution_type = models.CharField(max_length=40, default="EMPLOYEE_CONTRIBUTION")

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "posted_on"])]


class PaymentBatch(CompanyOwnedModel):
    """Salary disbursement batch for Bank Transfer CSV, Cash sheets, and bKash/Nagad MFS bulk payout (Module 21)."""

    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.PROTECT, related_name="payment_batches")
    batch_number = models.CharField(max_length=40)
    payout_channel = models.CharField(
        max_length=32,
        default="BANK_TRANSFER_BEFTN",
        help_text="BANK_TRANSFER_BEFTN, BKASH_BULK, NAGAD_BULK, CASH_SHEET",
    )
    bank_or_mfs_name = models.CharField(max_length=120, default="BRAC Bank PLC")
    total_amount_bdt = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="BDT")
    record_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=24, default="RECONCILED")

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "payroll_run"])]
