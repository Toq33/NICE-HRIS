"""Service layer for Bangladesh Payroll Calculation, Lakh/Crore Taka-in-Words, and NIS Statutory Deductions."""
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from organization.models import Employee
from system_settings.models import AuditLog, TenantSetting
from time_presence.models import MonthlyAttendanceSummary

from .models import (
    LoanLedger,
    PaymentBatch,
    PayrollPeriod,
    PayrollRun,
    Payslip,
    ProvidentFundLedger,
    StatutoryScheme,
)

_ONES = [
    "",
    "One",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Eleven",
    "Twelve",
    "Thirteen",
    "Fourteen",
    "Fifteen",
    "Sixteen",
    "Seventeen",
    "Eighteen",
    "Nineteen",
]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _two_digit_words(n: int) -> str:
    if n == 0:
        return ""
    if n < 20:
        return _ONES[n]
    ten, one = divmod(n, 10)
    return f"{_TENS[ten]}-{_ONES[one]}" if one else _TENS[ten]


def amount_to_bdt_words(amount: Decimal) -> str:
    """Convert a Decimal BDT amount into Bangladesh Lakh/Crore words (e.g. 'One Lakh, Sixty-Five Thousand Taka Only')."""
    whole = int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if whole <= 0:
        return "Zero Taka Only"

    parts: list[str] = []
    crore, rem = divmod(whole, 10_000_000)
    lakh, rem = divmod(rem, 100_000)
    thousand, rem = divmod(rem, 1_000)
    hundred, two_dig = divmod(rem, 100)

    if crore:
        parts.append(f"{_two_digit_words(crore)} Crore")
    if lakh:
        parts.append(f"{_two_digit_words(lakh)} Lakh")
    if thousand:
        parts.append(f"{_two_digit_words(thousand)} Thousand")
    if hundred:
        parts.append(f"{_ONES[hundred]} Hundred")
    if two_dig:
        parts.append(_two_digit_words(two_dig))

    return f"{', '.join(parts)} Taka Only"


def q2(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@transaction.atomic
def generate_company_payroll_run(
    *,
    company: Any,
    period: PayrollPeriod,
    run_number: str,
) -> PayrollRun:
    """Execute reproducible monthly payroll calculation freezing attendance, NIS days, and salary snapshots."""
    if period.is_locked:
        raise ValidationError("Cannot generate a new payroll run for a locked payroll period.")

    setting = TenantSetting.objects.first()
    pf_emp_pct = (setting.pf_employee_rate_pct if setting else Decimal("2.5000")) / Decimal("100")
    pf_er_pct = (setting.pf_employer_rate_pct if setting else Decimal("2.5000")) / Decimal("100")
    stamp_bdt = setting.revenue_stamp_bdt if setting else Decimal("10.00")

    scheme = StatutoryScheme.objects.filter(company=company).first()
    nis_emp_pct = (scheme.employee_rate_pct if scheme else Decimal("1.0000")) / Decimal("100")
    nis_er_pct = (scheme.employer_rate_pct if scheme else Decimal("2.0000")) / Decimal("100")

    run = PayrollRun.objects.create(
        company=company,
        period=period,
        run_number=run_number,
        status=PayrollRun.Status.VALIDATED,
        currency=company.currency,
    )

    employees = Employee.objects.filter(company=company).exclude(
        employment_status=Employee.EmploymentStatus.SEPARATED
    )

    total_gross = Decimal("0.00")
    total_ded = Decimal("0.00")
    total_net = Decimal("0.00")
    count = 0

    for idx, emp in enumerate(employees, start=1):
        att_sum = MonthlyAttendanceSummary.objects.filter(
            company=company,
            employee=emp,
            year=period.year,
            month=period.month,
        ).first()

        salary_days = att_sum.salary_days if att_sum else 30
        present_days = att_sum.present_days if att_sum else 22
        absent_days = att_sum.absent_days if att_sum else 0
        nis_days = att_sum.nis_days if att_sum else 26

        # Proration for unpaid absence
        payable_ratio = Decimal(str(max(0, salary_days - absent_days))) / Decimal(str(max(1, salary_days)))
        gross = q2(emp.gross_salary_bdt * payable_ratio)

        # Standard BD breakdown: Basic 50%, House Rent 25%, Medical 10%, Conveyance 10%, Entertainment 5%
        basic = q2(gross * Decimal("0.50"))
        house_rent = q2(gross * Decimal("0.25"))
        medical = q2(gross * Decimal("0.10"))
        conveyance = q2(gross * Decimal("0.10"))
        entertainment = q2(gross - (basic + house_rent + medical + conveyance))

        pf_emp = q2(basic * pf_emp_pct)
        pf_er = q2(basic * pf_er_pct)

        # NIS statutory contribution proportional to nis_days / salary_days
        nis_ratio = Decimal(str(min(nis_days, salary_days))) / Decimal(str(max(1, salary_days)))
        insurable_base = min(basic, scheme.wage_ceiling_bdt if scheme else Decimal("100000.00"))
        nis_emp = q2(insurable_base * nis_emp_pct * nis_ratio)
        nis_er = q2(insurable_base * nis_er_pct * nis_ratio)

        # Progressive AIT withholding estimate for higher earners
        ait_tax = q2((gross - Decimal("40000.00")) * Decimal("0.05")) if gross > Decimal("40000.00") else Decimal("0.00")

        deductions = q2(pf_emp + nis_emp + ait_tax + stamp_bdt)
        net = q2(gross - deductions)

        Payslip.objects.create(
            company=company,
            payroll_run=run,
            employee=emp,
            payslip_number=f"PS-{period.year}{str(period.month).zfill(2)}-{str(idx).zfill(4)}",
            status=Payslip.Status.DONE,
            salary_days=salary_days,
            present_days=present_days,
            absent_days=absent_days,
            nis_days=nis_days,
            basic_bdt=basic,
            house_rent_bdt=house_rent,
            medical_bdt=medical,
            conveyance_bdt=conveyance,
            entertainment_bdt=entertainment,
            gross_bdt=gross,
            pf_employee_bdt=pf_emp,
            pf_employer_bdt=pf_er,
            nis_employee_bdt=nis_emp,
            nis_employer_bdt=nis_er,
            ait_tax_bdt=ait_tax,
            revenue_stamp_bdt=stamp_bdt,
            total_deductions_bdt=deductions,
            net_bdt=net,
            currency=company.currency,
            net_in_words=amount_to_bdt_words(net),
            snapshot_json={
                "employee_code": emp.employee_code,
                "full_name": emp.full_name,
                "department": emp.department.name,
                "designation": emp.designation.title,
                "contract_gross_bdt": str(emp.gross_salary_bdt),
                "nis_days": nis_days,
                "present_days": present_days,
                "absent_days": absent_days,
            },
        )

        # Append to ProvidentFundLedger
        ProvidentFundLedger.objects.create(
            employee=emp,
            contribution_type="EMPLOYEE_CONTRIBUTION",
            amount=pf_emp,
            currency="BDT",
            reason=f"PF Employee Contribution ({period.name})",
            source_type="PAYROLL_RUN",
            source_id=run.id,
        )

        total_gross += gross
        total_ded += deductions
        total_net += net
        count += 1

    run.employee_count = count
    run.total_gross_bdt = q2(total_gross)
    run.total_deductions_bdt = q2(total_ded)
    run.total_net_bdt = q2(total_net)
    run.total_net_in_words = amount_to_bdt_words(run.total_net_bdt)
    run.save()

    PaymentBatch.objects.create(
        company=company,
        payroll_run=run,
        batch_number=f"BAT-{run_number}",
        payout_channel="BANK_TRANSFER_BEFTN",
        bank_or_mfs_name="BRAC Bank PLC (BEFTN Corporate)",
        total_amount_bdt=run.total_net_bdt,
        record_count=count,
        status="READY_FOR_DISBURSEMENT",
    )

    AuditLog.objects.create(
        action="PAYROLL_RUN_GENERATED",
        entity="PayrollRun",
        entity_id=str(run.id),
        new_values={
            "run_number": run_number,
            "employees": count,
            "total_net_bdt": str(run.total_net_bdt),
            "total_net_in_words": run.total_net_in_words,
        },
    )
    return run


@transaction.atomic
def lock_payroll_run(run: PayrollRun) -> PayrollRun:
    """Lock a payroll run and its period permanently (AGENTS.md Section 4)."""
    if run.status == PayrollRun.Status.LOCKED:
        raise ValidationError("Payroll run is already locked.")
    run.status = PayrollRun.Status.LOCKED
    run.save()
    run.payslips.update(status=Payslip.Status.PAID)
    period = run.period
    period.is_locked = True
    period.locked_at = timezone.now()
    period.save(update_fields=["is_locked", "locked_at", "updated_at"])
    return run


def get_loan_outstanding_balance(loan: Any) -> Decimal:
    agg = LoanLedger.objects.filter(loan=loan).aggregate(total=Sum("amount"))
    return agg["total"] or Decimal("0.00")


def build_payslip_pdf_bytes(payslip: Payslip) -> bytes:
    """Generates a printable Payslip PDF using ReportLab (Module 22 & 32)."""
    from io import BytesIO

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 800, f"{payslip.company.name} — Payslip ({payslip.payslip_number})")
    c.setFont("Helvetica", 10)
    c.drawString(
        50,
        780,
        f"Employee: {payslip.employee.full_name} ({payslip.employee.employee_code}) | Dept: {payslip.employee.department.name}",
    )
    c.drawString(
        50,
        764,
        f"Period: {payslip.payroll_run.period.name} | Present: {payslip.present_days}d | NIS Insurable Days: {payslip.nis_days}d",
    )
    y = 730
    rows = [
        ("Basic Salary (50%)", f"BDT {payslip.basic_bdt}"),
        ("House Rent Allowance (25%)", f"BDT {payslip.house_rent_bdt}"),
        ("Medical Allowance (10%)", f"BDT {payslip.medical_bdt}"),
        ("Conveyance Allowance (10%)", f"BDT {payslip.conveyance_bdt}"),
        ("Entertainment Allowance (5%)", f"BDT {payslip.entertainment_bdt}"),
        ("Gross Salary", f"BDT {payslip.gross_bdt}"),
        ("Provident Fund Employee (2.5%)", f"- BDT {payslip.pf_employee_bdt}"),
        ("NIS Social Security Deduction", f"- BDT {payslip.nis_employee_bdt}"),
        ("AIT Tax Withholding", f"- BDT {payslip.ait_tax_bdt}"),
        ("Revenue Stamp", f"- BDT {payslip.revenue_stamp_bdt}"),
        ("Net Payable Salary", f"BDT {payslip.net_bdt}"),
    ]
    for label, val in rows:
        c.drawString(50, y, label)
        c.drawRightString(520, y, val)
        y -= 18
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y - 10, f"In Words: {payslip.net_in_words}")
    c.showPage()
    c.save()
    return buf.getvalue()

