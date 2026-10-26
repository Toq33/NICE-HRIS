"""Phase 0 Foundation & Cross-Tenant Isolation Test Suite (AGENTS.md Section 4 & 8)."""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from accounts.models import User
from core.context import clear_context, tenant_context
from integrations.models import WebhookEndpoint
from organization.models import Company, Employee
from platform_admin.models import EnabledModule, Plan
from platform_admin.services import provision_tenant
from system_settings.models import AuditLog, LedgerEntrySample


@pytest.fixture
def seeded_tenants(db):
    all_mods = list(range(1, 43))
    plan_single = Plan.objects.create(
        code="test-single",
        name="Test Single Plan",
        max_employees=100,
        max_companies=1,
        monthly_price_bdt=Decimal("10000.00"),
        default_module_numbers=all_mods,
    )
    plan_multi = Plan.objects.create(
        code="test-multi",
        name="Test Multi Plan",
        max_employees=500,
        max_companies=5,
        monthly_price_bdt=Decimal("35000.00"),
        default_module_numbers=all_mods,
    )

    tenant_a = provision_tenant(
        name="Tenant Alpha Ltd.",
        slug="tenant-alpha",
        plan=plan_single,
        multi_company_enabled=False,
    )
    tenant_b = provision_tenant(
        name="Tenant Beta Group",
        slug="tenant-beta",
        plan=plan_multi,
        multi_company_enabled=True,
    )

    with tenant_context(tenant_a):
        comp_a = Company.objects.first()
        from organization.models import Branch, Department, Designation

        br_a = Branch.objects.create(company=comp_a, name="Alpha HQ", code="A-HQ", city="Dhaka")
        dept_a = Department.objects.create(company=comp_a, branch=br_a, name="HR", code="A-HR")
        des_a = Designation.objects.create(company=comp_a, title="Manager", code="A-MGR")
        emp_a = Employee.objects.create(
            company=comp_a,
            employee_code="ALP-0001",
            full_name="Alpha Employee",
            full_name_bn="আলফা কর্মী",
            work_email="emp@alpha.bd",
            phone="+8801700000001",
            joining_date="2024-01-01",
            branch=br_a,
            department=dept_a,
            designation=des_a,
            gross_salary_bdt=Decimal("80000.00"),
            national_id_encrypted="1990123456789",
            bank_account_encrypted="1501987654321",
        )

    with tenant_context(tenant_b):
        comp_b1 = Company.objects.first()
        comp_b2 = Company.objects.create(name="Beta Subsidiary 2", code="BETA2")
        from organization.models import Branch, Department, Designation

        br_b = Branch.objects.create(company=comp_b1, name="Beta HQ", code="B-HQ", city="Chattogram")
        dept_b = Department.objects.create(company=comp_b1, branch=br_b, name="Engineering", code="B-ENG")
        des_b = Designation.objects.create(company=comp_b1, title="Director", code="B-DIR")
        emp_b = Employee.objects.create(
            company=comp_b1,
            employee_code="BET-0001",
            full_name="Beta Employee",
            full_name_bn="বিটা কর্মী",
            work_email="emp@beta.bd",
            phone="+8801800000001",
            joining_date="2024-02-01",
            branch=br_b,
            department=dept_b,
            designation=des_b,
            gross_salary_bdt=Decimal("120000.00"),
            national_id_encrypted="1995987654321",
            bank_account_encrypted="2041122334455",
        )

    user_a = User.objects.create_user(
        email="admin@alpha.bd",
        password="Password123!",
        full_name="Alpha Admin",
        tenant=tenant_a,
        default_company=comp_a,
        can_view_salary=True,
    )
    user_b = User.objects.create_user(
        email="admin@beta.bd",
        password="Password123!",
        full_name="Beta Admin",
        tenant=tenant_b,
        default_company=comp_b1,
        can_view_salary=False,
    )
    platform_admin = User.objects.create_superuser(
        email="root@nicehris.bd",
        password="Password123!",
        full_name="Platform Superadmin",
    )

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "emp_a": emp_a,
        "emp_b": emp_b,
        "comp_a": comp_a,
        "comp_b1": comp_b1,
        "comp_b2": comp_b2,
        "user_a": user_a,
        "user_b": user_b,
        "platform_admin": platform_admin,
    }


@pytest.mark.django_db
def test_unscoped_tenant_manager_returns_empty_by_default(seeded_tenants):
    """Proves TenantManager never leaks rows when no tenant context is active."""
    clear_context()
    assert Employee.objects.count() == 0
    assert Company.objects.count() == 0


@pytest.mark.django_db
def test_cross_tenant_api_isolation(seeded_tenants):
    """CI mandatory test: Tenant A can NEVER read or mutate Tenant B through any API endpoint."""
    client_a = APIClient()
    login_res = client_a.post(
        "/api/v1/auth/login/",
        {"email": "admin@alpha.bd", "password": "Password123!"},
        format="json",
    )
    assert login_res.status_code == 200
    token_a = login_res.data["access"]
    client_a.credentials(HTTP_AUTHORIZATION=f"Bearer {token_a}")

    # 1. Listing employees only returns Tenant A's employee
    emp_list = client_a.get("/api/v1/employees/")
    assert emp_list.status_code == 200
    emp_ids = [item["id"] for item in emp_list.data["results"]]
    assert str(seeded_tenants["emp_a"].id) in emp_ids
    assert str(seeded_tenants["emp_b"].id) not in emp_ids

    # 2. Direct detail lookup of Tenant B's employee returns 404 Not Found
    emp_b_detail = client_a.get(f"/api/v1/employees/{seeded_tenants['emp_b'].id}/")
    assert emp_b_detail.status_code == 404

    # 3. Direct detail lookup of Tenant B's company returns 404 Not Found
    comp_b_detail = client_a.get(f"/api/v1/organization/companies/{seeded_tenants['comp_b1'].id}/")
    assert comp_b_detail.status_code == 404

    # 4. Spoofing X-Tenant-ID header as a regular tenant user cannot switch to Tenant B
    spoof_res = client_a.get(
        f"/api/v1/employees/{seeded_tenants['emp_b'].id}/",
        HTTP_X_TENANT_ID=str(seeded_tenants["tenant_b"].id),
    )
    assert spoof_res.status_code == 404


@pytest.mark.django_db
def test_single_vs_multi_company_session_context(seeded_tenants):
    """Single-company tenant never sees company switcher; multi-company tenant gets it."""
    client = APIClient()

    # Single-company tenant A
    res_a = client.post(
        "/api/v1/auth/login/",
        {"email": "admin@alpha.bd", "password": "Password123!"},
        format="json",
    )
    assert res_a.status_code == 200
    assert res_a.data["tenant"]["multi_company_enabled"] is False
    assert res_a.data["tenant"]["show_company_switcher"] is False
    assert len(res_a.data["companies"]) == 1

    # Multi-company tenant B
    res_b = client.post(
        "/api/v1/auth/login/",
        {"email": "admin@beta.bd", "password": "Password123!"},
        format="json",
    )
    assert res_b.status_code == 200
    assert res_b.data["tenant"]["multi_company_enabled"] is True
    assert res_b.data["tenant"]["show_company_switcher"] is True
    assert len(res_b.data["companies"]) == 2


@pytest.mark.django_db
def test_soft_delete_and_append_only_ledgers_and_audit(seeded_tenants):
    """HR records soft-delete only; LedgerModel and AuditLog forbid update/delete."""
    tenant_a = seeded_tenants["tenant_a"]
    emp_a = seeded_tenants["emp_a"]

    with tenant_context(tenant_a):
        # Create append-only ledger entry
        ledger = LedgerEntrySample.objects.create(
            employee=emp_a,
            amount=Decimal("0.00"),
            quantity=Decimal("14.0000"),
            reason="Annual leave opening accrual",
            source_type="ACCRUAL",
        )
        with pytest.raises(ValidationError):
            ledger.quantity = Decimal("10.0000")
            ledger.save()
        with pytest.raises(ValidationError):
            ledger.delete()

        # AuditLog immutability
        audit = AuditLog.objects.create(
            actor_email="admin@alpha.bd",
            action="TEST_ACTION",
            entity="Employee",
            entity_id=str(emp_a.id),
        )
        with pytest.raises(ValidationError):
            audit.action = "TAMPERED"
            audit.save()
        with pytest.raises(ValidationError):
            audit.delete()

        # Soft delete on Employee
        emp_a.delete()
        assert Employee.objects.filter(pk=emp_a.pk).count() == 0
        raw_emp = Employee.unscoped_objects.get(pk=emp_a.pk)
        assert raw_emp.deleted_at is not None
        assert raw_emp.is_active is False


@pytest.mark.django_db
def test_sensitive_field_encryption_and_salary_confidentiality(seeded_tenants):
    """Bank account and National ID are encrypted at rest and masked in API; salary respects permission."""
    emp_a = seeded_tenants["emp_a"]
    assert emp_a.national_id_encrypted.startswith("enc::")
    assert emp_a.bank_account_encrypted.startswith("enc::")
    assert emp_a.get_decrypted_field("national_id_encrypted") == "1990123456789"
    assert emp_a.get_masked_field("national_id_encrypted", visible_tail=4).endswith("6789")

    # User B does not have can_view_salary -> salary should be masked
    client_b = APIClient()
    res_b = client_b.post("/api/v1/auth/login/", {"email": "admin@beta.bd", "password": "Password123!"}, format="json")
    client_b.credentials(HTTP_AUTHORIZATION=f"Bearer {res_b.data['access']}")
    emp_b_res = client_b.get(f"/api/v1/employees/{seeded_tenants['emp_b'].id}/")
    assert emp_b_res.status_code == 200
    assert "Restricted" in emp_b_res.data["gross_salary_display"]
    assert emp_b_res.data["national_id_masked"].endswith("4321")


@pytest.mark.django_db
def test_api_key_auth_webhook_ssrf_and_idempotency(seeded_tenants):
    """Verifies APIKey auth, SSRF protection on webhooks, and Idempotency-Key replay."""
    client = APIClient()
    res = client.post("/api/v1/auth/login/", {"email": "admin@alpha.bd", "password": "Password123!"}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    # 1. Create API key with Idempotency-Key header
    idem_headers = {"HTTP_IDEMPOTENCY_KEY": "idem-key-001"}
    payload = {"name": "ERP Connector Key", "scopes": ["employees:read"]}
    key_res1 = client.post("/api/v1/integrations/api-keys/", payload, format="json", **idem_headers)
    assert key_res1.status_code == 201
    raw_key = key_res1.data["raw_key"]
    assert raw_key.startswith("nhris_")

    # Replay same Idempotency-Key returns cached response
    key_res2 = client.post("/api/v1/integrations/api-keys/", payload, format="json", **idem_headers)
    assert key_res2.status_code == 201
    assert key_res2.headers.get("X-Idempotent-Replay") == "true"

    # Different payload with same Idempotency-Key returns 409 Conflict
    key_conflict = client.post(
        "/api/v1/integrations/api-keys/",
        {"name": "Different Key Name", "scopes": ["employees:read"]},
        format="json",
        **idem_headers,
    )
    assert key_conflict.status_code == 409

    # 2. Authenticate using X-API-Key header
    api_key_client = APIClient()
    emp_res = api_key_client.get("/api/v1/employees/", HTTP_X_API_KEY=raw_key)
    assert emp_res.status_code == 200
    assert len(emp_res.data["results"]) == 1

    # 3. SSRF protection blocks non-HTTPS and private/loopback webhook URLs
    with tenant_context(seeded_tenants["tenant_a"]):
        with pytest.raises(ValidationError):
            WebhookEndpoint.objects.create(
                name="Bad HTTP Hook",
                target_url="http://example.com/webhook",
                events=["employee.created"],
                signing_secret="sec",
            )
        with pytest.raises(ValidationError):
            WebhookEndpoint.objects.create(
                name="Bad SSRF Localhost Hook",
                target_url="https://127.0.0.1/admin",
                events=["employee.created"],
                signing_secret="sec",
            )


@pytest.mark.django_db
def test_disabled_module_blocks_endpoint(seeded_tenants):
    """Per AGENTS.md Section 4: Only modules enabled for a tenant expose endpoints."""
    client = APIClient()
    res = client.post("/api/v1/auth/login/", {"email": "admin@alpha.bd", "password": "Password123!"}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    EnabledModule.objects.filter(tenant=seeded_tenants["tenant_a"], module_number=3).update(is_enabled=False)
    blocked_res = client.get("/api/v1/employees/")
    assert blocked_res.status_code == 403
