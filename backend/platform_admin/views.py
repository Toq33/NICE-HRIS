"""Platform Admin API views for managing Plans, Tenants, and the 42 HRM Modules."""
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsPlatformAdmin

from .models import EnabledModule, Plan, Tenant
from .registry import ALL_42_MODULES
from .serializers import EnabledModuleSerializer, PlanSerializer, TenantSerializer
from .services import update_tenant_modules


class PlanViewSet(viewsets.ModelViewSet):
    """Manage subscription plans at the Platform Admin layer."""

    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin]
    pagination_class = None


class TenantViewSet(viewsets.ModelViewSet):
    """Platform Admin viewset to list, create, suspend, and configure client tenants."""

    queryset = Tenant.objects.select_related("plan").all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin]
    pagination_class = None

    @extend_schema(
        summary="List or update enabled modules for a tenant",
        responses={200: EnabledModuleSerializer(many=True)},
    )
    @action(detail=True, methods=["get", "put", "patch"], url_path="modules")
    def modules(self, request: Request, pk: str = None) -> Response:
        tenant = self.get_object()
        if request.method in ("PUT", "PATCH"):
            toggles = request.data.get("modules", [])
            updated = update_tenant_modules(tenant, toggles)
            return Response(EnabledModuleSerializer(updated, many=True).data)
        mods = EnabledModule.objects.filter(tenant=tenant).order_by("module_number")
        return Response(EnabledModuleSerializer(mods, many=True).data)


class ModuleRegistryView(APIView):
    """Returns the canonical catalog of all 42 HRM modules and their enablement for the active tenant."""

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer

    @extend_schema(summary="Get all 42 HRM modules with active tenant enablement status")
    def get(self, request: Request) -> Response:
        tenant_id = getattr(request.user, "tenant_id", None)
        req_tenant_id = request.headers.get("X-Tenant-ID")
        if getattr(request.user, "is_platform_admin", False) and req_tenant_id:
            tenant_id = req_tenant_id

        enabled_map: dict[int, bool] = {}
        if tenant_id:
            rows = EnabledModule.objects.filter(tenant_id=tenant_id)
            enabled_map = {r.module_number: r.is_enabled for r in rows}

        results = []
        for mod in ALL_42_MODULES:
            results.append(
                {
                    **mod,
                    "is_enabled": enabled_map.get(mod["number"], True),
                }
            )
        return Response({"count": len(results), "modules": results}, status=status.HTTP_200_OK)
