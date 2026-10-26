"""Service layer for Attendance computation, NIS Days calculation, and Leave Ledger balances."""
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from system_settings.models import AuditLog
from workflows.services import submit_to_workflow

from .models import (
    AttendanceDay,
    AttendancePunch,
    LeaveLedger,
    LeaveRequest,
    LeaveType,
)


def compute_nis_days(
    *,
    present_days: int,
    paid_leave_days: int,
    paid_holidays: int,
    weekend_days: int = 0,
    include_weekends: bool = False,
) -> int:
    """Compute insurable NIS days per docs/02-architecture-and-database.md.

    Default configurable rule: days present + paid leave + paid holidays (unpaid leave and absence excluded).
    """
    total = present_days + paid_leave_days + paid_holidays
    if include_weekends:
        total += weekend_days
    return max(0, total)


def get_employee_leave_balance(employee: Any, leave_type: LeaveType) -> Decimal:
    """Leave balance is always the sum of append-only LeaveLedger entries (AGENTS.md Section 4 & docs/01 Mod 10)."""
    agg = LeaveLedger.objects.filter(employee=employee, leave_type=leave_type).aggregate(total=Sum("quantity"))
    return agg["total"] or Decimal("0.0000")


@transaction.atomic
def submit_leave_application(
    *,
    company: Any,
    employee: Any,
    leave_type: LeaveType,
    start_date: Any,
    end_date: Any,
    days_requested: Decimal,
    reason: str,
    reference_no: str,
) -> LeaveRequest:
    """Create a LeaveRequest and route it through the central Approval Workflow Engine (Module 37)."""
    leave_req = LeaveRequest.objects.create(
        company=company,
        reference_no=reference_no,
        employee=employee,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        days_requested=days_requested,
        reason=reason,
        status=LeaveRequest.Status.SUBMITTED,
        submitted_at=timezone.now(),
    )
    wf_req = submit_to_workflow(
        company=company,
        module_number=10,
        request_type="LEAVE_REQUEST",
        subject_type="LeaveRequest",
        subject_id=leave_req.id,
        title=f"Leave {reference_no}: {employee.full_name} ({leave_type.name}, {days_requested}d)",
        requester_employee=employee,
        summary_payload={
            "reference_no": reference_no,
            "leave_type": leave_type.name,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "days": str(days_requested),
        },
    )
    leave_req.approval_request_id = wf_req.id
    leave_req.save(update_fields=["approval_request_id", "updated_at"])
    return leave_req


@transaction.atomic
def approve_leave_request(leave_req: LeaveRequest) -> LeaveRequest:
    """Approve a LeaveRequest and append a negative TAKEN entry to the LeaveLedger."""
    if leave_req.status == LeaveRequest.Status.APPROVED:
        return leave_req

    leave_req.status = LeaveRequest.Status.APPROVED
    leave_req.decided_at = timezone.now()
    leave_req.save(update_fields=["status", "decided_at", "updated_at"])

    LeaveLedger.objects.create(
        employee=leave_req.employee,
        leave_type=leave_req.leave_type,
        quantity=-abs(Decimal(str(leave_req.days_requested))),
        reason=f"Approved leave {leave_req.reference_no}",
        source_type="TAKEN",
        source_id=leave_req.id,
    )
    return leave_req


@transaction.atomic
def record_mobile_check_in(
    *,
    company: Any,
    employee: Any,
    punch_type: str = "IN",
    latitude: Decimal | None = None,
    longitude: Decimal | None = None,
    within_geofence: bool = True,
) -> tuple[AttendancePunch, AttendanceDay]:
    """Record an immutable mobile/biometric punch and update today's computed AttendanceDay."""
    now = timezone.now()
    today = timezone.localdate()

    punch = AttendancePunch.objects.create(
        company=company,
        employee=employee,
        punch_time=now,
        punch_type=punch_type,
        source="MOBILE",
        latitude=latitude,
        longitude=longitude,
        within_geofence=within_geofence,
    )

    att_day, created = AttendanceDay.objects.get_or_create(
        company=company,
        employee=employee,
        work_date=today,
        defaults={
            "check_in": now if punch_type == "IN" else None,
            "check_out": now if punch_type == "OUT" else None,
            "status": AttendanceDay.DayStatus.PRESENT,
            "source": "MOBILE",
            "within_geofence": within_geofence,
        },
    )
    if not created:
        if punch_type == "OUT":
            att_day.check_out = now
        elif not att_day.check_in:
            att_day.check_in = now
        att_day.within_geofence = within_geofence
        att_day.save()

    AuditLog.objects.create(
        actor_email=employee.work_email,
        action=f"MOBILE_CHECK_{punch_type}",
        entity="AttendancePunch",
        entity_id=str(punch.id),
        new_values={"work_date": str(today), "within_geofence": within_geofence},
    )
    return punch, att_day
