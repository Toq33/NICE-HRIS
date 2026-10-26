"""API views for authentication, demo persona switching, and Module 39 (Users, Roles & Permissions)."""
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from core.context import get_current_tenant_id
from core.permissions import IsTenantMemberAndModuleEnabled
from core.throttling import LoginRateThrottle

from .models import DataScope, LoginHistory, Role, User
from .serializers import (
    DataScopeSerializer,
    LoginHistorySerializer,
    LoginSerializer,
    RoleSerializer,
    UserSerializer,
)
from .services import authenticate_and_issue_tokens, build_session_context


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
    """Returns pre-seeded demo accounts (Platform Admin, Single-Company Tenant, Multi-Company Tenant) for quick switching."""

    permission_classes = [AllowAny]
    serializer_class = serializers.Serializer

    @extend_schema(summary="List demo personas for instant experience & tenant switching")
    def get(self, request: Request) -> Response:
        users = (
            User.objects.select_related("tenant", "default_company")
            .filter(is_active=True)
            .order_by("-is_platform_admin", "tenant__name", "experience_mode")
        )
        personas = [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "full_name_bn": u.full_name_bn,
                "experience_mode": u.experience_mode,
                "is_platform_admin": u.is_platform_admin,
                "tenant_name": u.tenant.name if u.tenant else "Platform Admin (All Tenants)",
                "tenant_slug": u.tenant.slug if u.tenant else "platform",
                "multi_company_enabled": u.tenant.multi_company_enabled if u.tenant else False,
            }
            for u in users
        ]
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
    """Tenant-scoped Role management (Module 39)."""

    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 39

    def get_queryset(self):
        return Role.objects.prefetch_related("permissions").all()


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
