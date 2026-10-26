"""Phase 2 Models: Attendance (Mod 8), Shift & Roster (Mod 9), Leave & Ledger (Mod 10), Calendar (Mod 11), Overtime (Mod 12), Field Duty (Mod 13)."""
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models

from core.models import CompanyOwnedModel, LedgerModel, RequestModel


class WorkCalendar(CompanyOwnedModel):
    """Company work calendar with Bangladesh Friday default weekly off (Module 11)."""

    name = models.CharField(max_length=150)
    year = models.PositiveSmallIntegerField(default=2026)
    weekly_off_days = models.JSONField(default=list, help_text="Default ['FRI'] or ['FRI', 'SAT']")
    daily_work_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("8.00"))

    class Meta:
        unique_together = [("tenant", "company", "year", "name")]
        indexes = [models.Index(fields=["tenant", "company", "year"])]


class Holiday(CompanyOwnedModel):
    """Public, branch, and optional religious holidays (Module 11)."""

    class HolidayType(models.TextChoices):
        PUBLIC = "PUBLIC", "Public / National Holiday"
        FESTIVAL = "FESTIVAL", "Festival (Eid / Puja)"
        BRANCH = "BRANCH", "Branch Holiday"
        OPTIONAL = "OPTIONAL", "Optional Holiday"

    calendar = models.ForeignKey(WorkCalendar, on_delete=models.CASCADE, related_name="holidays")
    name = models.CharField(max_length=160)
    name_bn = models.CharField(max_length=160, blank=True, default="")
    date = models.DateField(db_index=True)
    holiday_type = models.CharField(max_length=20, choices=HolidayType.choices, default=HolidayType.PUBLIC)
    is_paid = models.BooleanField(default=True)
    branch = models.ForeignKey("organization.Branch", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "date"])]
        ordering = ["date"]


class Shift(CompanyOwnedModel):
    """Shift definition supporting standard, rotating, and overnight shifts crossing midnight (Module 9)."""

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=32)
    start_time = models.TimeField()
    end_time = models.TimeField()
    crosses_midnight = models.BooleanField(default=False)
    grace_minutes_late = models.PositiveSmallIntegerField(default=15)
    grace_minutes_early = models.PositiveSmallIntegerField(default=10)

    class Meta:
        unique_together = [("tenant", "company", "code")]
        indexes = [models.Index(fields=["tenant", "company", "code"])]
        ordering = ["code"]


class RosterBatch(CompanyOwnedModel):
    """Assigns a group of employees to a Shift for a period (Module 9 & docs/06)."""

    name = models.CharField(max_length=160)
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, related_name="roster_batches")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default="APPROVED")
    employee_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["tenant", "company", "start_date"])]
        ordering = ["-start_date"]


class AttendancePunch(CompanyOwnedModel):
    """Immutable raw attendance punch from ZKTeco/Hikvision device, file import, or mobile check-in (Module 8)."""

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="punches")
    punch_time = models.DateTimeField(db_index=True)
    punch_type = models.CharField(max_length=16, default="IN")  # IN, OUT
    source = models.CharField(max_length=32, default="BIOMETRIC")  # BIOMETRIC, MOBILE, IMPORT, MANUAL
    device_id = models.CharField(max_length=64, blank=True, default="")
    latitude = models.DecimalField(max_digits=9, decimal_places=4, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=4, null=True, blank=True)
    within_geofence = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "punch_time"])]
        ordering = ["-punch_time"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding and AttendancePunch.unscoped_objects.filter(pk=self.pk).exists():
            raise ValidationError("Raw attendance punches are immutable.")
        super().save(*args, **kwargs)


class AttendanceDay(CompanyOwnedModel):
    """Computed daily attendance record per employee (safe to recompute from punches + shift + corrections) (Module 8)."""

    class DayStatus(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        LATE = "LATE", "Late"
        ABSENT = "ABSENT", "Absent"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        HOLIDAY = "HOLIDAY", "Holiday"
        WEEKEND = "WEEKEND", "Weekend"

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="attendance_days")
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    work_date = models.DateField(db_index=True)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=DayStatus.choices, default=DayStatus.PRESENT, db_index=True)
    worked_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("8.00"))
    extra_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    late_minutes = models.PositiveSmallIntegerField(default=0)
    source = models.CharField(max_length=32, default="BIOMETRIC")
    within_geofence = models.BooleanField(default=True)

    class Meta:
        unique_together = [("tenant", "employee", "work_date")]
        indexes = [models.Index(fields=["tenant", "employee", "work_date"])]
        ordering = ["-work_date"]


class MonthlyAttendanceSummary(CompanyOwnedModel):
    """Monthly attendance summary feeding Payroll with `nis_days` (Module 8, 20 & docs/06 slide 9)."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CONFIRMED = "CONFIRMED", "Confirmed"
        APPROVED = "APPROVED", "Approved"

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="attendance_summaries")
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    salary_days = models.PositiveSmallIntegerField(default=30)
    present_days = models.PositiveSmallIntegerField(default=22)
    weekend_days = models.PositiveSmallIntegerField(default=4)
    absent_days = models.PositiveSmallIntegerField(default=0)
    late_days = models.PositiveSmallIntegerField(default=0)
    paid_holidays = models.PositiveSmallIntegerField(default=2)
    unpaid_holidays = models.PositiveSmallIntegerField(default=0)
    paid_leave_days = models.PositiveSmallIntegerField(default=2)
    unpaid_leave_days = models.PositiveSmallIntegerField(default=0)
    nis_days = models.PositiveSmallIntegerField(
        default=26,
        help_text="Insurable days in the period for National Insurance Scheme / social security calculations",
    )
    nis_manual_override_reason = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        unique_together = [("tenant", "employee", "year", "month")]
        indexes = [models.Index(fields=["tenant", "company", "year", "month"])]
        ordering = ["-year", "-month", "employee__employee_code"]


class LeaveType(CompanyOwnedModel):
    """Configurable leave types (Casual, Sick, Earned/Annual, Maternity, Paternity, Short, Unpaid) (Module 10)."""

    name = models.CharField(max_length=120)
    name_bn = models.CharField(max_length=120, blank=True, default="")
    code = models.CharField(max_length=24)
    annual_quota_days = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("14.00"))
    is_paid = models.BooleanField(default=True)
    carry_forward_allowed = models.BooleanField(default=False)
    max_carry_forward_days = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    encashment_allowed = models.BooleanField(default=False)

    class Meta:
        unique_together = [("tenant", "company", "code")]
        indexes = [models.Index(fields=["tenant", "company", "code"])]
        ordering = ["code"]


class LeaveLedger(LedgerModel):
    """Append-only leave balance ledger (ACCRUAL, TAKEN, ADJUSTMENT, CARRY_FORWARD, ENCASHMENT, EXPIRY) (Module 10)."""

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="leave_ledger_entries")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name="ledger_entries")

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "leave_type", "posted_on"])]
        ordering = ["-posted_on", "-created_at"]


class LeaveRequest(RequestModel):
    """Employee leave application routed via Approval Workflow Engine (Module 10)."""

    reference_no = models.CharField(max_length=40, db_index=True)
    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="leave_requests")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name="leave_requests")
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("1.00"))
    reason = models.TextField()

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "status", "start_date"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="leave_req_valid_dates_chk",
            ),
            models.CheckConstraint(
                condition=models.Q(days_requested__gt=Decimal("0.00")),
                name="leave_req_positive_days_chk",
            ),
        ]
        ordering = ["-created_at"]


class OvertimeRequest(RequestModel):
    """Overtime application and approved hours with configurable rate multiplier (Module 12)."""

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="overtime_requests")
    work_date = models.DateField(db_index=True)
    requested_hours = models.DecimalField(max_digits=5, decimal_places=2)
    approved_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    rate_multiplier = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("2.0000"))
    is_holiday_ot = models.BooleanField(default=False)
    reason = models.CharField(max_length=255)

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "work_date"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(requested_hours__gt=Decimal("0.00")),
                name="ot_req_positive_hours_chk",
            ),
        ]
        ordering = ["-work_date"]


class FieldDutyMovement(RequestModel):
    """Field duty and remote work movement request with mobile check-in location capture (Module 13)."""

    employee = models.ForeignKey("organization.Employee", on_delete=models.PROTECT, related_name="field_movements")
    movement_type = models.CharField(max_length=32, default="FIELD_VISIT")  # FIELD_VISIT, REMOTE_WORK, CLIENT_MEETING
    work_date = models.DateField()
    client_or_location = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=4, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=4, null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["tenant", "employee", "work_date"])]
        ordering = ["-work_date"]
