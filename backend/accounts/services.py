"""Service layer for authentication, session context, and RBAC."""
from typing import Any

from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from organization.models import Company, Employee
from platform_admin.models import EnabledModule, Tenant

from .models import DataScope, LoginHistory, Role, RolePermission, User


def get_user_primary_role(user: User) -> Role | None:
    """Resolve the primary Role assigned to a User via DataScope, Employee profile, or experience_mode."""
    if not user or not user.is_authenticated:
        return None

    scope = (
        DataScope.unscoped_objects.filter(user=user, deleted_at__isnull=True)
        .select_related("role")
        .first()
    )
    if scope and scope.role_id:
        role = Role.unscoped_objects.filter(pk=scope.role_id, deleted_at__isnull=True).first()
        if role:
            return role

    emp = Employee.unscoped_objects.filter(user=user, deleted_at__isnull=True).first()
    if emp and emp.role_id:
        role = Role.unscoped_objects.filter(pk=emp.role_id, deleted_at__isnull=True).first()
        if role:
            return role

    tenant_id = user.tenant_id
    if not tenant_id and user.is_platform_admin:
        t = Tenant.objects.filter(slug="jamuna-group").first() or Tenant.objects.first()
        tenant_id = t.id if t else None

    if tenant_id:
        if user.is_platform_admin:
            fallback_code = "super-admin"
        elif user.experience_mode == User.ExperienceMode.ADMIN:
            fallback_code = "admin"
        elif user.experience_mode == User.ExperienceMode.MANAGER:
            fallback_code = "manager"
        else:
            fallback_code = "user"
        return Role.unscoped_objects.filter(
            tenant_id=tenant_id, code=fallback_code, deleted_at__isnull=True
        ).first()
    return None


def is_super_admin_or_admin(user: User) -> bool:
    """Return True if the user is Super Admin (Platform Admin) or Admin."""
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_platform_admin", False):
        return True
    role = get_user_primary_role(user)
    if role:
        return role.code in ("super-admin", "admin", "hr-director")
    return getattr(user, "experience_mode", "") == User.ExperienceMode.ADMIN


def get_user_module_actions(user: User, module_number: int) -> list[str]:
    """Return the list of allowed actions ('view', 'create', 'edit', 'delete') for user on module_number."""
    if not user or not user.is_authenticated:
        return []
    if getattr(user, "is_platform_admin", False):
        return ["view", "create", "edit", "delete"]

    role = get_user_primary_role(user)
    admin_access = is_super_admin_or_admin(user)

    if module_number == 43:
        return ["view", "create", "edit", "delete"] if admin_access else []

    if role:
        perm = RolePermission.unscoped_objects.filter(
            role=role, module_number=module_number, deleted_at__isnull=True
        ).first()
        if perm is not None:
            return [a.lower() for a in (perm.actions or [])]

    if admin_access:
        return ["view", "create", "edit", "delete"]
    return []


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
    from platform_admin.registry import ALL_42_MODULES

    tenant = user.tenant
    if not tenant and user.is_platform_admin:
        tenant = Tenant.objects.filter(slug="jamuna-group").first() or Tenant.objects.first()

    companies_data: list[dict[str, Any]] = []
    enabled_module_numbers: list[int] = []

    if tenant:
        qs = Company.unscoped_objects.filter(tenant=tenant, deleted_at__isnull=True, is_active=True)
        if not user.is_platform_admin and user.allowed_companies.exists():
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
        enabled_module_numbers = [m["number"] for m in ALL_42_MODULES]

    role = get_user_primary_role(user)
    admin_access = is_super_admin_or_admin(user)
    super_admin_access = bool(user.is_platform_admin or (role and role.code == "super-admin"))

    all_nums = [m["number"] for m in ALL_42_MODULES]
    tenant_enabled_set = set(enabled_module_numbers) if enabled_module_numbers else set(all_nums)
    if admin_access:
        tenant_enabled_set.add(43)

    module_permissions: dict[int, list[str]] = {}
    if super_admin_access:
        for num in all_nums:
            module_permissions[num] = ["view", "create", "edit", "delete"]
        enabled_module_numbers = sorted(all_nums)
    elif role:
        raw_perms = RolePermission.unscoped_objects.filter(
            role=role, deleted_at__isnull=True
        )
        perm_by_mod = {
            p.module_number: [a.lower() for a in (p.actions or [])]
            for p in raw_perms
        }
        for num in all_nums:
            if num == 43 and not admin_access:
                module_permissions[num] = []
            elif num == 43 and admin_access:
                module_permissions[num] = ["view", "create", "edit", "delete"]
            elif num in perm_by_mod:
                module_permissions[num] = perm_by_mod[num]
            elif admin_access:
                module_permissions[num] = ["view", "create", "edit", "delete"]
            else:
                module_permissions[num] = []

        enabled_module_numbers = sorted(
            [
                num
                for num in all_nums
                if num in tenant_enabled_set and "view" in module_permissions.get(num, [])
            ]
        )
    else:
        for num in all_nums:
            module_permissions[num] = ["view", "create", "edit", "delete"] if admin_access else ["view"]
        if not admin_access:
            module_permissions[43] = []
            enabled_module_numbers = [n for n in enabled_module_numbers if n != 43]

    selected_company_id = active_company_id or (str(user.default_company_id) if user.default_company_id else None)
    if not selected_company_id and companies_data:
        selected_company_id = companies_data[0]["id"]

    # Per AGENTS.md Section 4:
    # Single-company vs multi-company is driven by tenant.multi_company_enabled plus number of companies.
    show_company_switcher = bool(
        tenant and tenant.multi_company_enabled and len(companies_data) > 1
    )

    role_code = "super-admin" if user.is_platform_admin else (role.code if role else ("admin" if admin_access else "user"))
    role_name = "Super Admin" if user.is_platform_admin else (role.name if role else ("Admin" if admin_access else "User"))

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "full_name_bn": user.full_name_bn,
            "experience_mode": user.experience_mode,
            "is_platform_admin": user.is_platform_admin,
            "is_super_admin": super_admin_access,
            "is_admin": admin_access,
            "role_code": role_code,
            "role_name": role_name,
            "can_view_salary": bool(
                super_admin_access
                or (role.can_view_confidential_salary if role else user.can_view_salary)
            ),
            "can_view_medical": bool(
                super_admin_access
                or (role.can_view_confidential_medical if role else user.can_view_medical)
            ),
            "has_approval_authority": bool(
                super_admin_access
                or (role.has_approval_authority if role else user.has_approval_authority)
            ),
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
        "module_permissions": module_permissions,
    }
