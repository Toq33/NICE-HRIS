"""Role, module-enablement, and tenant-isolation permission classes."""
from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from .context import get_current_tenant_id


class IsPlatformAdmin(BasePermission):
    """Allows access only to Platform Superadmins (above tenants)."""

    def has_permission(self, request: Request, view: Any) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_platform_admin", False)
        )


class IsTenantMemberAndModuleEnabled(BasePermission):
    """Enforces that the user belongs to an active tenant and the module is enabled for that tenant.

    Per AGENTS.md Section 4: Only modules enabled for a tenant expose endpoints and navigation.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        tenant_id = get_current_tenant_id() or getattr(user, "tenant_id", None)
        if not tenant_id:
            return bool(getattr(user, "is_platform_admin", False))

        module_number = getattr(view, "module_number", None)
        if module_number is not None:
            from platform_admin.models import EnabledModule

            is_enabled = EnabledModule.objects.filter(
                tenant_id=tenant_id,
                module_number=module_number,
                is_enabled=True,
            ).exists()
            if not is_enabled:
                return False

        return True
