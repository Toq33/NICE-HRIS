"""Service layer for the Approval Workflow Engine (Module 37) and Letter Generation (Module 35)."""
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.context import get_current_user_id
from system_settings.models import AuditLog

from .models import (
    ApprovalDecision,
    ApprovalRequest,
    GeneratedLetter,
    LetterTemplate,
    Notification,
    WorkflowDefinition,
)


@transaction.atomic
def submit_to_workflow(
    *,
    company: Any,
    module_number: int,
    request_type: str,
    subject_type: str,
    subject_id: Any,
    title: str,
    requester_employee: Any,
    amount: Any = 0,
    summary_payload: dict[str, Any] | None = None,
) -> ApprovalRequest:
    """Generic entry point for any HRM module to raise an ApprovalRequest."""
    wf = WorkflowDefinition.objects.filter(
        module_number=module_number,
        request_type=request_type,
        is_active=True,
    ).first()
    if not wf:
        wf = WorkflowDefinition.objects.create(
            name=f"{request_type.replace('_', ' ').title()} Standard Workflow",
            code=f"wf-{module_number}-{request_type.lower().replace('_', '-')}",
            module_number=module_number,
            request_type=request_type,
            steps_config=[
                {"step": 1, "role": "line-manager", "label": "Line Manager Review", "sla_hours": 24},
                {"step": 2, "role": "hr-director", "label": "HR Final Approval", "sla_hours": 48},
            ],
        )

    steps = wf.steps_config or [{"step": 1, "role": "line-manager"}]
    approver = requester_employee.manager if requester_employee and requester_employee.manager else requester_employee

    req = ApprovalRequest.objects.create(
        company=company,
        workflow=wf,
        module_number=module_number,
        subject_type=subject_type,
        subject_id=subject_id,
        title=title,
        requester_employee=requester_employee,
        current_approver=approver,
        current_step=1,
        total_steps=len(steps),
        amount=amount,
        status=ApprovalRequest.Status.PENDING,
        summary_payload=summary_payload or {},
    )

    AuditLog.objects.create(
        actor_id=get_current_user_id(),
        action="APPROVAL_SUBMITTED",
        entity=subject_type,
        entity_id=str(subject_id),
        new_values={"approval_request_id": str(req.id), "title": title, "status": req.status},
    )
    return req


@transaction.atomic
def decide_approval_request(
    *,
    approval_request: ApprovalRequest,
    decision: str,
    comments: str = "",
    actor_employee: Any | None = None,
) -> ApprovalRequest:
    """Process an approval or rejection step, enforcing mandatory rejection reason and updating audit trail."""
    decision = decision.upper()
    if decision not in ("APPROVED", "REJECTED"):
        raise ValidationError({"decision": "Decision must be APPROVED or REJECTED."})
    if decision == "REJECTED" and not comments.strip():
        raise ValidationError({"comments": "Rejection reason is mandatory when rejecting a request."})

    ApprovalDecision.objects.create(
        approval_request=approval_request,
        step_number=approval_request.current_step,
        actor_employee=actor_employee,
        decision=decision,
        comments=comments,
    )

    if decision == "REJECTED":
        approval_request.status = ApprovalRequest.Status.REJECTED
        approval_request.rejection_reason = comments
        approval_request.decided_at = timezone.now()
    else:
        if approval_request.current_step < approval_request.total_steps:
            approval_request.current_step += 1
            approval_request.status = ApprovalRequest.Status.IN_PROGRESS
        else:
            approval_request.status = ApprovalRequest.Status.APPROVED
            approval_request.decided_at = timezone.now()

    approval_request.save()

    if approval_request.requester_employee and approval_request.requester_employee.user:
        Notification.objects.create(
            recipient=approval_request.requester_employee.user,
            title=f"Request {approval_request.status.title()}: {approval_request.title}",
            message=comments or f"Your request '{approval_request.title}' is now {approval_request.status}.",
            action_url="/m/37/approval-workflow-engine",
        )

    AuditLog.objects.create(
        actor_id=get_current_user_id(),
        action=f"APPROVAL_{decision}",
        entity=approval_request.subject_type,
        entity_id=str(approval_request.subject_id),
        new_values={
            "approval_request_id": str(approval_request.id),
            "status": approval_request.status,
            "step": approval_request.current_step,
            "comments": comments,
        },
    )
    return approval_request


def render_letter_from_template(
    *,
    company: Any,
    employee: Any,
    template: LetterTemplate,
    reference_no: str,
    extra_context: dict[str, Any] | None = None,
) -> GeneratedLetter:
    """Render an HR letter preserving merge data and template version snapshot (Module 35)."""
    merge_data = {
        "company_name": company.name,
        "employee_name": employee.full_name,
        "employee_name_bn": employee.full_name_bn,
        "employee_code": employee.employee_code,
        "designation": employee.designation.title,
        "department": employee.department.name,
        "joining_date": str(employee.joining_date),
        "gross_salary": str(employee.gross_salary_bdt),
        "reference_no": reference_no,
        **(extra_context or {}),
    }
    rendered = template.body_template
    for key, val in merge_data.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(val))

    return GeneratedLetter.objects.create(
        company=company,
        employee=employee,
        template=template,
        template_version=template.version,
        reference_no=reference_no,
        merge_data=merge_data,
        rendered_html=rendered,
    )


def build_report_excel_bytes(report: Any) -> bytes:
    """Generates an Excel (.xlsx) workbook using openpyxl for a ReportDefinition (Module 38)."""
    from io import BytesIO

    import openpyxl

    from organization.models import Employee

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = (report.code or "Report")[:31]
    ws.append(
        [
            "Employee Code",
            "Full Name (EN)",
            "Full Name (BN)",
            "Company",
            "Department",
            "Designation",
            "Status",
            "Joining Date",
        ]
    )
    for emp in Employee.objects.select_related("company", "department", "designation").all()[:200]:
        ws.append(
            [
                emp.employee_code,
                emp.full_name,
                emp.full_name_bn,
                emp.company.name,
                emp.department.name,
                emp.designation.title,
                emp.employment_status,
                str(emp.joining_date),
            ]
        )
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

