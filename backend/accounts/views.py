"""API views for authentication, demo persona switching, and Module 39 (Users, Roles & Permissions)."""
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from core.context import get_current_tenant_id
from core.permissions import IsTenantMemberAndModuleEnabled
from core.throttling import LoginRateThrottle

from .models import DataScope, LoginHistory, Role, RolePermission, User
from .serializers import (
    DataScopeSerializer,
    LoginHistorySerializer,
    LoginSerializer,
    RoleSerializer,
    UserSerializer,
)
from .services import (
    authenticate_and_issue_tokens,
    build_session_context,
    get_user_primary_role,
    is_super_admin_or_admin,
)


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="Lax",
        max_age=8 * 3600,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="Lax",
        max_age=7 * 24 * 3600,
    )


class LoginView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]
    serializer_class = LoginSerializer

    @extend_schema(request=LoginSerializer, summary="Sign in with email & password (sets HTTP-only JWT cookie)")
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, access, refresh = authenticate_and_issue_tokens(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        session_data = build_session_context(user)
        response = Response(
            {
                "access": access,
                "refresh": refresh,
                **session_data,
            },
            status=status.HTTP_200_OK,
        )
        _set_auth_cookies(response, access, refresh)
        return response


class LogoutView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    serializer_class = serializers.Serializer

    @extend_schema(summary="Clear HTTP-only auth cookies and end session")
    def post(self, request: Request) -> Response:
        response = Response({"status": "logged_out"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer

    @extend_schema(summary="Get current user, tenant, company mode, and enabled modules")
    def get(self, request: Request) -> Response:
        active_company_id = request.headers.get("X-Company-ID")
        return Response(build_session_context(request.user, active_company_id=active_company_id))


class DemoPersonaListView(APIView):
    """Returns pre-seeded demo accounts (Super Admin, Admin, Single-Company Tenant, Multi-Company Tenant) for quick switching."""

    authentication_classes: list = []
    permission_classes = [AllowAny]
    serializer_class = serializers.Serializer

    @extend_schema(summary="List demo personas for instant experience & tenant switching")
    def get(self, request: Request) -> Response:
        users = (
            User.objects.select_related("tenant", "default_company")
            .filter(is_active=True)
            .order_by("-is_platform_admin", "tenant__name", "experience_mode")
        )
        personas = []
        for u in users:
            role = get_user_primary_role(u)
            role_label = (
                "Super Admin"
                if u.is_platform_admin
                else (role.name if role else ("Admin" if u.experience_mode == "ADMIN" else u.experience_mode))
            )
            personas.append(
                {
                    "id": str(u.id),
                    "email": u.email,
                    "full_name": u.full_name,
                    "full_name_bn": u.full_name_bn,
                    "experience_mode": u.experience_mode,
                    "role_name": role_label,
                    "is_platform_admin": u.is_platform_admin,
                    "tenant_name": (
                        "Super Admin (All Modules & Tenants)"
                        if u.is_platform_admin
                        else (u.tenant.name if u.tenant else "Super Admin (All Modules)")
                    ),
                    "tenant_slug": u.tenant.slug if u.tenant else "platform",
                    "multi_company_enabled": u.tenant.multi_company_enabled if u.tenant else True,
                }
            )
        return Response({"personas": personas})

    @extend_schema(summary="Switch to a demo persona and issue tokens")
    def post(self, request: Request) -> Response:
        email = request.data.get("email")
        user = User.objects.select_related("tenant", "default_company").filter(email=email, is_active=True).first()
        if not user:
            return Response(
                {"error": {"code": "not_found", "message": "Demo persona not found.", "details": {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        refresh = RefreshToken.for_user(user)
        access_str = str(refresh.access_token)
        refresh_str = str(refresh)
        session_data = build_session_context(user)
        response = Response({"access": access_str, "refresh": refresh_str, **session_data})
        _set_auth_cookies(response, access_str, refresh_str)
        return response


class UserViewSet(viewsets.ModelViewSet):
    """Tenant-scoped User directory (Module 39)."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 39
    search_fields = ["full_name", "full_name_bn", "email"]

    def get_queryset(self):
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            return User.objects.none()
        return User.objects.filter(tenant_id=tenant_id).select_related("tenant", "default_company")

    def perform_create(self, serializer: UserSerializer) -> None:
        serializer.save(tenant_id=get_current_tenant_id())


class RoleViewSet(viewsets.ModelViewSet):
    """Tenant-scoped Role & Permission Matrix management (Modules 39 & 43)."""

    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 39

    def get_queryset(self):
        return Role.objects.prefetch_related("permissions").all()

    def _require_admin(self, request: Request) -> None:
        if not is_super_admin_or_admin(request.user):
            raise PermissionDenied("Only Super Admin and Admin can create or modify roles and permissions.")

    def perform_create(self, serializer: RoleSerializer) -> None:
        self._require_admin(self.request)
        serializer.save()

    def perform_update(self, serializer: RoleSerializer) -> None:
        self._require_admin(self.request)
        serializer.save()

    def perform_destroy(self, instance: Role) -> None:
        self._require_admin(self.request)
        if instance.code in ("super-admin", "admin"):
            raise PermissionDenied("Core administrative roles ('Super Admin' and 'Admin') cannot be deleted.")

        from organization.models import Employee

        # Reassign any employees holding this role to the fallback 'user' role
        default_user_role = Role.unscoped_objects.filter(
            tenant_id=instance.tenant_id, code="user"
        ).first()
        if default_user_role:
            Employee.unscoped_objects.filter(role=instance).update(role=default_user_role)
            DataScope.unscoped_objects.filter(role=instance).update(role=default_user_role)
        else:
            Employee.unscoped_objects.filter(role=instance).update(role=None)
            DataScope.unscoped_objects.filter(role=instance).delete()

        from django.utils import timezone

        code_to_delete = instance.code
        super().perform_destroy(instance)
        now = timezone.now()
        Role.unscoped_objects.filter(code=code_to_delete).update(deleted_at=now, is_active=False)
        RolePermission.unscoped_objects.filter(role__code=code_to_delete).update(
            deleted_at=now, is_active=False
        )

    @action(detail=True, methods=["post"], url_path="toggle-permission")
    def toggle_permission(self, request: Request, pk: str | None = None) -> Response:
        """Toggle a single action ('view', 'create', 'edit', 'delete') on a module for this role."""
        self._require_admin(request)
        role = self.get_object()
        module_number = int(request.data.get("module_number", 1))
        action_name = str(request.data.get("action", "view")).lower()
        if action_name not in ("view", "create", "edit", "delete"):
            return Response(
                {"error": {"code": "invalid_action", "message": "Action must be view, create, edit, or delete."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        perm = RolePermission.unscoped_objects.filter(
            role=role,
            module_number=module_number,
            deleted_at__isnull=True,
        ).first()
        if not perm:
            perm = RolePermission.unscoped_objects.create(
                tenant_id=role.tenant_id,
                role=role,
                module_number=module_number,
                actions=[],
            )
        current_actions = [a.lower() for a in (perm.actions or [])]
        if action_name in current_actions:
            if action_name == "view":
                # Turning off 'view' revokes all actions on that module so the role cannot see or mutate it
                current_actions = []
            else:
                current_actions = [a for a in current_actions if a != action_name]
        else:
            current_actions.append(action_name)
            # Enabling create/edit/delete automatically ensures 'view' is also enabled
            if action_name in ("create", "edit", "delete") and "view" not in current_actions:
                current_actions.insert(0, "view")

        # Keep canonical order: view, create, edit, delete
        ordered_actions = [a for a in ("view", "create", "edit", "delete") if a in current_actions]

        # Sync across all Role records with the same code across tenants
        matching_roles = list(Role.unscoped_objects.filter(code=role.code, deleted_at__isnull=True))
        for r in matching_roles:
            RolePermission.unscoped_objects.update_or_create(
                tenant_id=r.tenant_id,
                role=r,
                module_number=module_number,
                defaults={"actions": list(ordered_actions)},
            )
        role.refresh_from_db()
        return Response(RoleSerializer(role).data)

    @action(detail=True, methods=["post"], url_path="bulk-group-permissions")
    def bulk_group_permissions(self, request: Request, pk: str | None = None) -> Response:
        """Grant All or Revoke All actions across a list of module_numbers for this role."""
        self._require_admin(request)
        role = self.get_object()
        module_numbers = request.data.get("module_numbers", [])
        grant = bool(request.data.get("grant", True))
        target_actions = ["view", "create", "edit", "delete"] if grant else []

        matching_roles = list(Role.unscoped_objects.filter(code=role.code, deleted_at__isnull=True))
        for r in matching_roles:
            for mod_num in module_numbers:
                RolePermission.unscoped_objects.update_or_create(
                    tenant_id=r.tenant_id,
                    role=r,
                    module_number=int(mod_num),
                    defaults={"actions": list(target_actions)},
                )
        role.refresh_from_db()
        return Response(RoleSerializer(role).data)


class DataScopeViewSet(viewsets.ModelViewSet):
    """Tenant-scoped DataScope assignments (Module 39)."""

    serializer_class = DataScopeSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 39

    def get_queryset(self):
        return DataScope.objects.select_related("user", "role").all()


class LoginHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Immutable Login History (Module 40 foundation)."""

    serializer_class = LoginHistorySerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 40

    def get_queryset(self):
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            return LoginHistory.objects.none()
        return LoginHistory.objects.filter(tenant_id=tenant_id)
