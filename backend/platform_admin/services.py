"""Service layer for Platform Admin tenant provisioning and module management."""
from typing import Any

from django.db import transaction

from core.context import tenant_context

from .models import EnabledModule, Plan, Tenant
from .registry import ALL_42_MODULES


@transaction.atomic
def provision_tenant(
    *,
    name: str,
    slug: str,
    plan: Plan,
    name_bn: str = "",
    multi_company_enabled: bool = False,
    employee_limit: int | None = None,
    status: str = Tenant.Status.ACTIVE,
    initial_company_name: str | None = None,
    enabled_module_numbers: list[int] | None = None,
) -> Tenant:
    """Create a tenant, initialize its 42 module toggles, default company, and numbering sequences."""
    tenant = Tenant.objects.create(
        name=name,
        name_bn=name_bn,
        slug=slug,
        plan=plan,
        status=status,
        multi_company_enabled=multi_company_enabled,
        employee_limit=employee_limit or plan.max_employees,
        weekly_off_days=["FRI"],
    )

    active_nums = set(
        enabled_module_numbers
        if enabled_module_numbers is not None
        else (plan.default_module_numbers or [m["number"] for m in ALL_42_MODULES])
    )

    module_rows = [
        EnabledModule(
            tenant=tenant,
            module_number=mod["number"],
            module_slug=mod["slug"],
            module_name=mod["name"],
            module_group=mod["group"],
            phase=mod["phase"],
            is_enabled=(mod["number"] in active_nums),
        )
        for mod in ALL_42_MODULES
    ]
    EnabledModule.objects.bulk_create(module_rows)

    from organization.models import Company
    from system_settings.models import NumberSequence, TenantSetting

    with tenant_context(tenant):
        comp_name = initial_company_name or name
        company = Company.objects.create(
            tenant=tenant,
            name=comp_name,
            name_bn=name_bn,
            code=slug.upper()[:12].replace("-", "_"),
            is_primary=True,
            currency="BDT",
            timezone="Asia/Dhaka",
        )
        TenantSetting.objects.get_or_create(
            tenant=tenant,
            defaults={
                "statutory_disclaimer": "Bangladesh default statutory config — needs review by a local HR/tax professional.",
                "nis_days_rule": {
                    "include_present": True,
                    "include_paid_leave": True,
                    "include_paid_holidays": True,
                    "include_weekends": False,
                    "exclude_unpaid_leave": True,
                    "exclude_absent": True,
                },
            },
        )
        for seq_code, prefix in [
            ("EMPLOYEE", "EMP"),
            ("REQUISITION", "REQ"),
            ("LEAVE_REQUEST", "LR"),
            ("TICKET", "TKT"),
            ("LOAN", "LN"),
            ("PAYSLIP", "PS"),
        ]:
            NumberSequence.objects.get_or_create(
                tenant=tenant,
                company=company,
                code=seq_code,
                defaults={"prefix": prefix, "padding": 4, "next_val": 1},
            )

    return tenant


@transaction.atomic
def update_tenant_modules(tenant: Tenant, module_toggles: list[dict[str, Any]]) -> list[EnabledModule]:
    """Update enabled status of modules for a tenant and log to audit trail."""
    for item in module_toggles:
        mod_num = item.get("module_number")
        is_enabled = bool(item.get("is_enabled", True))
        EnabledModule.objects.filter(tenant=tenant, module_number=mod_num).update(is_enabled=is_enabled)
    return list(EnabledModule.objects.filter(tenant=tenant).order_by("module_number"))
