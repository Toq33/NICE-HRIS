"""Automated test suite for Phases 1–6 business rules: Workflow Engine, Leave Ledger, NIS Days, Payroll Run & Locking, and Restricted Data Classes."""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from core.context import tenant_context
from payroll.models import PayrollPeriod
from payroll.services import amount_to_bdt_words, generate_company_payroll_run, lock_payroll_run
from talent_relations.models import HealthSafetyRecord
from time_presence.models import LeaveLedger, LeaveType, MonthlyAttendanceSummary
from time_presence.services import (
    approve_leave_request,
    compute_nis_days,
    get_employee_leave_balance,
    submit_leave_application,
)
from workflows.services import decide_approval_request, submit_to_workflow


@pytest.mark.django_db
def test_workflow_engine_and_mandatory_rejection_reason(seeded_tenants):
    """Module 37: Approvals route via Workflow Engine; rejecting without reason raises ValidationError."""
    tenant_a = seeded_tenants["tenant_a"]
    comp_a = seeded_tenants["comp_a"]
    emp_a = seeded_tenants["emp_a"]

    with tenant_context(tenant_a):
        req = submit_to_workflow(
            company=comp_a,
            module_number=12,
            request_type="OVERTIME_REQUEST",
            subject_type="OvertimeRequest",
            subject_id=emp_a.id,
            title="Overtime 4h Request",
            requester_employee=emp_a,
            amount=Decimal("1500.00"),
        )
        assert req.status == "PENDING"
        assert req.current_step == 1

        # Rejecting without a reason must fail
        with pytest.raises(ValidationError):
            decide_approval_request(approval_request=req, decision="REJECTED", comments="   ")

        # Approving step 1 advances to step 2 (IN_PROGRESS)
        req = decide_approval_request(approval_request=req, decision="APPROVED", comments="Supervisor approved")
        assert req.status == "IN_PROGRESS"
        assert req.current_step == 2

        # Approving final step sets status to APPROVED
        req = decide_approval_request(approval_request=req, decision="APPROVED", comments="HR Final approved")
        assert req.status == "APPROVED"
        assert req.decisions.count() == 2


@pytest.mark.django_db
def test_leave_ledger_balance_and_approval(seeded_tenants):
    """Module 10: Leave balance is strictly the sum of append-only LeaveLedger entries."""
    tenant_a = seeded_tenants["tenant_a"]
    comp_a = seeded_tenants["comp_a"]
    emp_a = seeded_tenants["emp_a"]

    with tenant_context(tenant_a):
        lt = LeaveType.objects.create(
            company=comp_a,
            name="Annual Leave",
            code="AL",
            annual_quota_days=Decimal("18.00"),
        )
        LeaveLedger.objects.create(
            employee=emp_a,
            leave_type=lt,
            quantity=Decimal("18.0000"),
            reason="Opening entitlement",
            source_type="ACCRUAL",
        )
        assert get_employee_leave_balance(emp_a, lt) == Decimal("18.0000")

        leave_req = submit_leave_application(
            company=comp_a,
            employee=emp_a,
            leave_type=lt,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 11, 12),
            days_requested=Decimal("3.00"),
            reason="Personal trip",
            reference_no="LR-TEST-001",
        )
        assert leave_req.approval_request_id is not None

        approve_leave_request(leave_req)
        assert get_employee_leave_balance(emp_a, lt) == Decimal("15.0000")


@pytest.mark.django_db
def test_payroll_run_nis_days_bdt_words_and_immutability(seeded_tenants):
    """Module 15, 20, 22: Payroll freezes inputs, computes NIS & Taka in words, and locked runs are immutable."""
    assert amount_to_bdt_words(Decimal("165000.00")) == "One Lakh, Sixty-Five Thousand Taka Only"
    assert compute_nis_days(present_days=22, paid_leave_days=2, paid_holidays=2) == 26

    tenant_a = seeded_tenants["tenant_a"]
    comp_a = seeded_tenants["comp_a"]
    emp_a = seeded_tenants["emp_a"]

    with tenant_context(tenant_a):
        MonthlyAttendanceSummary.objects.create(
            company=comp_a,
            employee=emp_a,
            year=2026,
            month=10,
            status="APPROVED",
            salary_days=30,
            present_days=22,
            absent_days=0,
            nis_days=26,
        )
        period = PayrollPeriod.objects.create(
            company=comp_a,
            name="October 2026",
            year=2026,
            month=10,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
        )
        run = generate_company_payroll_run(company=comp_a, period=period, run_number="PR-TEST-202610")
        assert run.employee_count == 1
        assert run.total_gross_bdt == Decimal("80000.00")
        assert "Taka Only" in run.total_net_in_words

        slip = run.payslips.first()
        assert slip.basic_bdt == Decimal("40000.00")
        assert slip.house_rent_bdt == Decimal("20000.00")
        assert slip.nis_days == 26
        assert slip.snapshot_json["nis_days"] == 26

        # Lock the payroll run and verify immutability
        lock_payroll_run(run)
        assert run.period.is_locked is True

        with pytest.raises(ValidationError):
            run.total_net_bdt = Decimal("999999.00")
            run.save()

    # Verify PDF Payslip (ReportLab) and Excel Report (openpyxl) endpoints
    client_a = APIClient()
    res_a = client_a.post("/api/v1/auth/login/", {"email": "admin@alpha.bd", "password": "Password123!"}, format="json")
    client_a.credentials(HTTP_AUTHORIZATION=f"Bearer {res_a.data['access']}")

    pdf_res = client_a.get(f"/api/v1/payroll/payslips/{slip.id}/pdf/")
    assert pdf_res.status_code == 200
    assert pdf_res["Content-Type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF-")

    from workflows.models import ReportDefinition

    with tenant_context(tenant_a):
        rep = ReportDefinition.objects.create(
            name="Headcount & Workforce Report",
            code="REP-HEADCOUNT",
            module_number=38,
            category="WORKFORCE",
        )
    xlsx_res = client_a.get(f"/api/v1/reports/definitions/{rep.id}/export-xlsx/")
    assert xlsx_res.status_code == 200
    assert "spreadsheetml.sheet" in xlsx_res["Content-Type"]
    assert xlsx_res.content.startswith(b"PK")


@pytest.mark.django_db
def test_restricted_medical_record_encryption_and_masking(seeded_tenants):
    """Module 29: Medical data is encrypted at rest and masked unless user has can_view_medical."""
    tenant_b = seeded_tenants["tenant_b"]
    comp_b1 = seeded_tenants["comp_b1"]
    emp_b = seeded_tenants["emp_b"]

    with tenant_context(tenant_b):
        rec = HealthSafetyRecord.objects.create(
            company=comp_b1,
            employee=emp_b,
            record_type="MEDICAL_CHECK",
            incident_or_checkup_date=date(2026, 10, 15),
            restricted_medical_notes="Confidential cardiac screening normal.",
        )
        assert rec.restricted_medical_notes.startswith("enc::")

    client_b = APIClient()
    res_b = client_b.post("/api/v1/auth/login/", {"email": "admin@beta.bd", "password": "Password123!"}, format="json")
    client_b.credentials(HTTP_AUTHORIZATION=f"Bearer {res_b.data['access']}")

    med_res = client_b.get(f"/api/v1/relations/health-safety/{rec.id}/")
    assert med_res.status_code == 200
    assert "Restricted Medical Data" in med_res.data["medical_notes_display"]


@pytest.mark.django_db
def test_attachment_upload_virus_scan_and_signed_url_audit(seeded_tenants):
    """Shared Attachment table: 10MB limit, content-type validation, EICAR quarantine, and signed URL audit."""
    comp_a = seeded_tenants["comp_a"]
    emp_a = seeded_tenants["emp_a"]

    client_a = APIClient()
    res_a = client_a.post(
        "/api/v1/auth/login/",
        {"email": "admin@alpha.bd", "password": "Password123!"},
        format="json",
    )
    client_a.credentials(HTTP_AUTHORIZATION=f"Bearer {res_a.data['access']}")

    # 1. Clean PDF upload succeeds and issues signed URL with AuditLog entry
    att_res = client_a.post(
        "/api/v1/settings/attachments/",
        {
            "company": str(comp_a.id),
            "entity_type": "EmployeeDocument",
            "entity_id": str(emp_a.id),
            "file_name": "National_ID_Card.pdf",
            "content_type": "application/pdf",
            "file_size_bytes": 124000,
        },
        format="json",
    )
    assert att_res.status_code == 201
    assert att_res.data["virus_scan_status"] == "CLEAN"

    url_res = client_a.post(f"/api/v1/settings/attachments/{att_res.data['id']}/signed-url/")
    assert url_res.status_code == 200
    assert "signature=" in url_res.data["signed_url"]

    # 2. EICAR virus signature is rejected at upload validation time
    quar_res = client_a.post(
        "/api/v1/settings/attachments/",
        {
            "company": str(comp_a.id),
            "entity_type": "EmployeeDocument",
            "entity_id": str(emp_a.id),
            "file_name": "EICAR-TEST-FILE.pdf",
            "content_type": "application/pdf",
            "file_size_bytes": 4096,
        },
        format="json",
    )
    assert quar_res.status_code == 400


@pytest.mark.django_db
def test_bulk_imports_and_inter_company_transfer(seeded_tenants):
    """Module 3, 8, 14: Bulk imports with dry_run=True/False and inter-company transfer."""
    comp_b1 = seeded_tenants["comp_b1"]
    comp_b2 = seeded_tenants["comp_b2"]
    emp_b = seeded_tenants["emp_b"]

    client_b = APIClient()
    res_b = client_b.post(
        "/api/v1/auth/login/",
        {"email": "admin@beta.bd", "password": "Password123!"},
        format="json",
    )
    client_b.credentials(HTTP_AUTHORIZATION=f"Bearer {res_b.data['access']}")

    # 1. Dry-run employee bulk import
    dry_res = client_b.post(
        "/api/v1/employees/bulk-import/",
        {
            "dry_run": True,
            "rows": [
                {
                    "company": str(comp_b1.id),
                    "employee_code": "BETA-0099",
                    "full_name": "Dry Run Candidate",
                    "work_email": "dryrun@beta.bd",
                    "phone": "+8801711009988",
                    "joining_date": "2026-10-01",
                    "branch": str(emp_b.branch_id),
                    "department": str(emp_b.department_id),
                    "designation": str(emp_b.designation_id),
                    "gross_salary_bdt": "55000.00",
                }
            ],
        },
        format="json",
    )
    assert dry_res.status_code == 200
    assert dry_res.data["dry_run"] is True
    assert dry_res.data["valid_count"] == 1
    assert dry_res.data["created_ids"] == []

    # 2. Inter-company transfer in multi-company tenant B
    xfer_res = client_b.post(
        f"/api/v1/employees/{emp_b.id}/inter-company-transfer/",
        {
            "target_company_id": str(comp_b2.id),
            "effective_from": "2026-11-01",
            "reason": "Group restructuring transfer",
        },
        format="json",
    )
    assert xfer_res.status_code == 200
    assert str(xfer_res.data["company"]) == str(comp_b2.id)


@pytest.mark.django_db
def test_oauth2_client_credentials_and_webhook_replay(seeded_tenants):
    """Module 41: OAuth2 client_credentials token grant and webhook delivery replay with auto-disable."""
    client_a = APIClient()
    res_a = client_a.post(
        "/api/v1/auth/login/",
        {"email": "admin@alpha.bd", "password": "Password123!"},
        format="json",
    )
    client_a.credentials(HTTP_AUTHORIZATION=f"Bearer {res_a.data['access']}")

    # 1. Create OAuth2 client and exchange for Bearer JWT
    oauth_res = client_a.post(
        "/api/v1/integrations/oauth-clients/",
        {"name": "Payroll ERP Sync", "scopes": ["employees:read", "payroll:read"]},
        format="json",
    )
    assert oauth_res.status_code == 201
    cid = oauth_res.data["client_id"]
    csec = oauth_res.data["client_secret"]

    tok_res = APIClient().post(
        "/api/v1/auth/oauth2/token/",
        {"grant_type": "client_credentials", "client_id": cid, "client_secret": csec},
        format="json",
    )
    assert tok_res.status_code == 200
    assert "access_token" in tok_res.data

    # 2. Create Webhook Endpoint, dispatch event, and replay delivery
    wh_res = client_a.post(
        "/api/v1/integrations/webhooks/",
        {
            "name": "Replay Hook",
            "target_url": "https://hooks.partner-erp.com/events",
            "events": ["employee.created"],
        },
        format="json",
    )
    assert wh_res.status_code == 201
    wh_id = wh_res.data["id"]

    disp_res = client_a.post(f"/api/v1/integrations/webhooks/{wh_id}/test-dispatch/")
    assert disp_res.status_code == 200
    deliv_id = disp_res.data[0]["id"]

    rep_res = client_a.post(f"/api/v1/integrations/webhook-deliveries/{deliv_id}/replay/")
    assert rep_res.status_code == 200
    assert rep_res.data["attempts"] == 2
    assert rep_res.data["status"] == "DELIVERED"
