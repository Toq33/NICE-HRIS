"""Serializers and ViewSets for Module 41 (API Keys, OAuth2 Clients, Webhooks, Connectors)."""
import hashlib
import secrets

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from core.context import set_current_tenant_id, set_current_user_id
from core.permissions import IsTenantMemberAndModuleEnabled
from system_settings.models import AuditLog

from .models import (
    APIKey,
    IntegrationConnectorConfig,
    IntegrationRunLog,
    OAuth2Client,
    WebhookDelivery,
    WebhookEndpoint,
)
from .services import (
    create_oauth2_client,
    create_tenant_api_key,
    dispatch_webhook_event,
    replay_webhook_delivery,
    run_connector_test,
)


class APIKeySerializer(serializers.ModelSerializer):
    raw_key = serializers.CharField(read_only=True)

    class Meta:
        model = APIKey
        fields = [
            "id",
            "name",
            "key_prefix",
            "scopes",
            "ip_allowlist",
            "expires_at",
            "last_used_at",
            "revoked_at",
            "is_active",
            "raw_key",
            "created_at",
        ]
        read_only_fields = ["id", "key_prefix", "last_used_at", "revoked_at", "raw_key", "created_at"]


class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEndpoint
        fields = [
            "id",
            "name",
            "target_url",
            "events",
            "failure_count",
            "auto_disabled_at",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "failure_count", "auto_disabled_at", "created_at"]

    def create(self, validated_data: dict) -> WebhookEndpoint:
        validated_data["signing_secret"] = f"whsec_{secrets.token_urlsafe(24)}"
        return super().create(validated_data)


class WebhookDeliverySerializer(serializers.ModelSerializer):
    endpoint_name = serializers.CharField(source="endpoint.name", read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            "id",
            "endpoint",
            "endpoint_name",
            "event_name",
            "payload",
            "status",
            "response_code",
            "attempts",
            "last_error",
            "delivered_at",
            "created_at",
        ]


class IntegrationRunLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationRunLog
        fields = [
            "id",
            "connector",
            "direction",
            "status",
            "records_processed",
            "records_failed",
            "summary",
            "created_at",
        ]


class IntegrationConnectorConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationConnectorConfig
        fields = [
            "id",
            "connector_code",
            "name",
            "is_enabled",
            "schedule_cron",
            "field_mapping",
            "last_run_at",
            "last_run_status",
            "created_at",
        ]
        read_only_fields = ["id", "last_run_at", "last_run_status", "created_at"]


class APIKeyViewSet(viewsets.ModelViewSet):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 41

    def get_queryset(self):
        return APIKey.objects.all()

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_key, raw_key = create_tenant_api_key(
            name=serializer.validated_data["name"],
            scopes=serializer.validated_data.get("scopes", ["employees:read"]),
            ip_allowlist=serializer.validated_data.get("ip_allowlist", ""),
            expires_at=serializer.validated_data.get("expires_at"),
            service_user=request.user,
        )
        out = APIKeySerializer(api_key).data
        out["raw_key"] = raw_key
        return Response(out, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Revoke an API key immediately")
    @action(detail=True, methods=["post"])
    def revoke(self, request: Request, pk: str = None) -> Response:
        api_key = self.get_object()
        api_key.is_active = False
        api_key.revoked_at = timezone.now()
        api_key.save(update_fields=["is_active", "revoked_at", "updated_at"])
        return Response(APIKeySerializer(api_key).data)


class WebhookEndpointViewSet(viewsets.ModelViewSet):
    serializer_class = WebhookEndpointSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 41

    def get_queryset(self):
        return WebhookEndpoint.objects.all()

    @extend_schema(summary="Trigger a test webhook event delivery")
    @action(detail=True, methods=["post"], url_path="test-dispatch")
    def test_dispatch(self, request: Request, pk: str = None) -> Response:
        ep = self.get_object()
        event_name = (ep.events or ["employee.created"])[0]
        deliveries = dispatch_webhook_event(event_name, {"test": True, "endpoint_id": str(ep.id)})
        return Response(WebhookDeliverySerializer(deliveries, many=True).data)


class WebhookDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WebhookDeliverySerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 41

    def get_queryset(self):
        return WebhookDelivery.objects.select_related("endpoint").all()

    @extend_schema(summary="Replay a webhook delivery with fresh HMAC-SHA256 signature")
    @action(detail=True, methods=["post"], url_path="replay")
    def replay(self, request: Request, pk: str = None) -> Response:
        delivery = self.get_object()
        simulate_failure = str(request.data.get("simulate_failure", "false")).lower() in ("true", "1")
        replayed = replay_webhook_delivery(delivery, simulate_failure=simulate_failure)
        return Response(WebhookDeliverySerializer(replayed).data)


class OAuth2ClientSerializer(serializers.ModelSerializer):
    client_secret = serializers.CharField(read_only=True)

    class Meta:
        model = OAuth2Client
        fields = [
            "id",
            "name",
            "client_id",
            "client_secret",
            "scopes",
            "last_used_at",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "client_id", "client_secret", "last_used_at", "created_at"]


class OAuth2ClientViewSet(viewsets.ModelViewSet):
    serializer_class = OAuth2ClientSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 41

    def get_queryset(self):
        return OAuth2Client.objects.all()

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client, raw_secret = create_oauth2_client(
            name=serializer.validated_data["name"],
            scopes=serializer.validated_data.get("scopes", ["employees:read"]),
            service_user=request.user,
        )
        out = OAuth2ClientSerializer(client).data
        out["client_secret"] = raw_secret
        return Response(out, status=status.HTTP_201_CREATED)


class OAuth2TokenRequestSerializer(serializers.Serializer):
    grant_type = serializers.ChoiceField(choices=["client_credentials"], default="client_credentials")
    client_id = serializers.CharField()
    client_secret = serializers.CharField()
    scope = serializers.CharField(required=False, allow_blank=True, default="")


class OAuth2TokenView(APIView):
    """OAuth2 Client Credentials token endpoint (`POST /api/v1/auth/oauth2/token/`)."""

    permission_classes = [AllowAny]
    serializer_class = OAuth2TokenRequestSerializer

    @extend_schema(
        request=OAuth2TokenRequestSerializer,
        summary="Issue a short-lived JWT access token via OAuth2 client_credentials grant",
    )
    def post(self, request: Request) -> Response:
        serializer = OAuth2TokenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_id = serializer.validated_data["client_id"]
        client_secret = serializer.validated_data["client_secret"]
        secret_hash = hashlib.sha256(client_secret.encode("utf-8")).hexdigest()

        client = (
            OAuth2Client.unscoped_objects.select_related("tenant", "service_user")
            .filter(client_id=client_id, client_secret_hash=secret_hash, is_active=True)
            .first()
        )
        if not client or not client.service_user:
            raise AuthenticationFailed("Invalid OAuth2 client_id or client_secret.")

        OAuth2Client.unscoped_objects.filter(pk=client.pk).update(last_used_at=timezone.now())
        set_current_tenant_id(client.tenant_id)
        set_current_user_id(client.service_user_id)

        refresh = RefreshToken.for_user(client.service_user)
        access = refresh.access_token
        access["tenant_id"] = str(client.tenant_id)
        access["oauth2_client_id"] = client.client_id
        access["scopes"] = client.scopes or []

        AuditLog.objects.create(
            actor_id=client.service_user_id,
            action="OAUTH2_TOKEN_ISSUED",
            entity="OAuth2Client",
            entity_id=str(client.id),
            new_values={"client_id": client.client_id, "scopes": client.scopes},
        )
        return Response(
            {
                "access_token": str(access),
                "token_type": "Bearer",
                "expires_in": 900,
                "scope": " ".join(client.scopes or []),
            }
        )


class IntegrationConnectorViewSet(viewsets.ModelViewSet):
    serializer_class = IntegrationConnectorConfigSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 41

    def get_queryset(self):
        return IntegrationConnectorConfig.objects.all()

    @extend_schema(summary="Test connection for a configured integration connector")
    @action(detail=True, methods=["post"], url_path="test-connection")
    def test_connection(self, request: Request, pk: str = None) -> Response:
        config = self.get_object()
        log_entry = run_connector_test(config)
        return Response(IntegrationRunLogSerializer(log_entry).data)


class IntegrationRunLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IntegrationRunLogSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 41

    def get_queryset(self):
        return IntegrationRunLog.objects.select_related("connector").all()
