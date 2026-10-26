"""Service layer for authentication, session context, and RBAC."""
from typing import Any

from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from organization.models import Company
from platform_admin.models import EnabledModule

from .models import LoginHistory, User


def authenticate_and_issue_tokens(
    *,
    email: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str = "",
) -> tuple[User, str, str]:
    user = authenticate(username=email, password=password)
    if not user or not user.is_active:
        LoginHistory.objects.create(
            email_attempted=email,
            ip_address=ip_address,
            user_agent=user_agent[:512],
            succeeded=False,
        )
        raise AuthenticationFailed("Invalid email or password.")

    LoginHistory.objects.create(
        user=user,
        email_attempted=email,
        tenant_id=user.tenant_id,
        ip_address=ip_address,
        user_agent=user_agent[:512],
        succeeded=True,
    )
    refresh = RefreshToken.for_user(user)
    return user, str(refresh.access_token), str(refresh)


def build_session_context(user: User, active_company_id: str | None = None) -> dict[str, Any]:
    """Build complete tenant, company (single vs multi-company), role, and enabled-module context for the UI shell."""
    tenant = user.tenant
    companies_data: list[dict[str, Any]] = []
    enabled_module_numbers: list[int] = []

    if tenant:
        qs = Company.unscoped_objects.filter(tenant=tenant, deleted_at__isnull=True, is_active=True)
        if user.allowed_companies.exists():
            qs = qs.filter(id__in=user.allowed_companies.values_list("id", flat=True))
        companies_data = [
            {
                "id": str(c.id),
                "name": c.name,
                "name_bn": c.name_bn,
                "code": c.code,
                "is_primary": c.is_primary,
                "currency": c.currency,
                "timezone": c.timezone,
            }
            for c in qs
        ]
        enabled_module_numbers = list(
            EnabledModule.objects.filter(tenant=tenant, is_enabled=True)
            .order_by("module_number")
            .values_list("module_number", flat=True)
        )
    else:
        from platform_admin.registry import ALL_42_MODULES

        enabled_module_numbers = [m["number"] for m in ALL_42_MODULES]

    selected_company_id = active_company_id or (str(user.default_company_id) if user.default_company_id else None)
    if not selected_company_id and companies_data:
        selected_company_id = companies_data[0]["id"]

    # Per AGENTS.md Section 4:
    # Single-company vs multi-company is driven by tenant.multi_company_enabled plus number of companies.
    show_company_switcher = bool(
        tenant and tenant.multi_company_enabled and len(companies_data) > 1
    )

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "full_name_bn": user.full_name_bn,
            "experience_mode": user.experience_mode,
            "is_platform_admin": user.is_platform_admin,
            "can_view_salary": user.can_view_salary,
            "can_view_medical": user.can_view_medical,
            "has_approval_authority": user.has_approval_authority,
            "totp_enabled": user.totp_enabled,
        },
        "tenant": (
            {
                "id": str(tenant.id),
                "name": tenant.name,
                "name_bn": tenant.name_bn,
                "slug": tenant.slug,
                "status": tenant.status,
                "multi_company_enabled": tenant.multi_company_enabled,
                "show_company_switcher": show_company_switcher,
                "default_currency": tenant.default_currency,
                "default_timezone": tenant.default_timezone,
                "lakh_grouping_enabled": tenant.lakh_grouping_enabled,
                "weekly_off_days": tenant.weekly_off_days,
            }
            if tenant
            else None
        ),
        "companies": companies_data,
        "active_company_id": selected_company_id,
        "enabled_module_numbers": enabled_module_numbers,
    }
