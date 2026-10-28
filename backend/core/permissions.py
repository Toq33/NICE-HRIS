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
    """Enforces that the user belongs to an active tenant, the module is enabled for that tenant,
    and the user's RolePermission grants the required action ('view', 'create', 'edit', or 'delete').

    Per AGENTS.md Section 4: Only modules enabled for a tenant expose endpoints and navigation.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Super Admin (Platform Admin) has full access to every module and every edit action
        if getattr(user, "is_platform_admin", False):
            return True

        tenant_id = get_current_tenant_id() or getattr(user, "tenant_id", None)
        if not tenant_id:
            return False

        module_number = getattr(view, "module_number", None)
        if module_number == 43:
            from accounts.services import is_super_admin_or_admin

            return is_super_admin_or_admin(user)

        if module_number is not None:
            from accounts.services import get_user_module_actions, is_super_admin_or_admin
            from platform_admin.models import EnabledModule

            is_enabled = EnabledModule.objects.filter(
                tenant_id=tenant_id,
                module_number=module_number,
                is_enabled=True,
            ).exists()
            if not is_enabled:
                return False

            # RoleViewSet is shared by Module 3 (Employee Role selector), Module 39, and Module 43
            if view.__class__.__name__ == "RoleViewSet":
                if request.method in ("GET", "HEAD", "OPTIONS"):
                    return True
                return is_super_admin_or_admin(user)

            # Lookup endpoints (GET/HEAD/OPTIONS) used for dropdowns across modules (e.g. companies, branches, departments)
            # are allowed if the user can view either the target module or any related dependent module,
            # EXCEPT when directly querying a module endpoint where we check 'view' permission.
            allowed_actions = get_user_module_actions(user, int(module_number))
            method = (request.method or "GET").upper()
            view_action = getattr(view, "action", None)

            if method in ("GET", "HEAD", "OPTIONS"):
                if "view" in allowed_actions:
                    return True
                if request.query_params.get("lookup") == "1":
                    return True
                if view.__class__.__name__ in (
                    "CompanyViewSet",
                    "BranchViewSet",
                    "DepartmentViewSet",
                    "DesignationViewSet",
                    "GradeViewSet",
                    "LeaveTypeViewSet",
                ):
                    return True
                # Composite Self-Service (Modules 32 & 33) and Dashboard (Module 1) read widgets
                if int(module_number) in (3, 8, 10, 22):
                    if "view" in get_user_module_actions(user, 32) or "view" in get_user_module_actions(user, 33):
                        return True
                if int(module_number) == 37 and "view" in get_user_module_actions(user, 1):
                    return True
                return False

            if view_action == "mobile_punch":
                return (
                    "create" in allowed_actions
                    or "create" in get_user_module_actions(user, 32)
                    or "create" in get_user_module_actions(user, 33)
                )

            if method == "DELETE" or view_action in ("destroy", "revoke", "undo"):
                return "delete" in allowed_actions

            if method in ("PUT", "PATCH") or view_action in (
                "update",
                "partial_update",
                "approve",
                "reject",
                "confirm",
                "lock",
                "finalize",
                "advance_stage",
                "execute",
                "verify",
                "resolve",
                "close",
                "assign",
                "publish",
                "disburse",
                "settle",
                "acknowledge",
                "toggle_module",
            ):
                return "edit" in allowed_actions

            if method == "POST":
                # Custom detail actions (e.g. /approve/, /confirm/, /lock/) require 'edit'; collection POST requires 'create'
                if getattr(view, "detail", False) and view_action not in (None, "create"):
                    return "edit" in allowed_actions
                return "create" in allowed_actions

        return True
