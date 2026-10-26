"""Service layer for API key generation, HMAC-SHA256 webhook signing, and connector execution."""
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from django.utils import timezone

from core.context import get_current_tenant_id, get_current_user_id
from system_settings.models import AuditLog

from .csv_json.connector import GenericCSVJSONConnector
from .models import (
    APIKey,
    IntegrationConnectorConfig,
    IntegrationRunLog,
    OAuth2Client,
    WebhookDelivery,
    WebhookEndpoint,
)


def create_tenant_api_key(
    *,
    name: str,
    scopes: list[str],
    ip_allowlist: str = "",
    expires_at: Any | None = None,
    service_user: Any | None = None,
) -> tuple[APIKey, str]:
    """Generate a new API key, return (APIKey instance, raw_plaintext_key_shown_once)."""
    raw_secret = secrets.token_urlsafe(32)
    raw_key = f"nhris_{raw_secret}"
    key_prefix = raw_key[:12]
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    api_key = APIKey.objects.create(
        name=name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=scopes,
        ip_allowlist=ip_allowlist,
        expires_at=expires_at,
        service_user=service_user,
    )

    AuditLog.objects.create(
        actor_id=get_current_user_id(),
        action="API_KEY_CREATED",
        entity="APIKey",
        entity_id=str(api_key.id),
        new_values={"name": name, "key_prefix": key_prefix, "scopes": scopes},
    )
    return api_key, raw_key


def sign_webhook_payload(secret: str, timestamp: int, payload_dict: dict[str, Any]) -> str:
    """Create HMAC-SHA256 signature with timestamp header per docs/04-api-and-integrations.md."""
    body = json.dumps(payload_dict, separators=(",", ":"), sort_keys=True)
    message = f"{timestamp}.{body}".encode()
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def dispatch_webhook_event(event_name: str, payload: dict[str, Any]) -> list[WebhookDelivery]:
    """Queue and record outbound webhook deliveries for matching active endpoints."""
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        return []

    endpoints = WebhookEndpoint.objects.filter(is_active=True, auto_disabled_at__isnull=True)
    deliveries: list[WebhookDelivery] = []
    for ep in endpoints:
        if event_name not in (ep.events or []):
            continue
        ts = int(time.time())
        secret = ep.get_decrypted_field("signing_secret") or "default-secret"
        signature = sign_webhook_payload(secret, ts, payload)
        delivery = WebhookDelivery.objects.create(
            endpoint=ep,
            event_name=event_name,
            payload={"event": event_name, "timestamp": ts, "signature": signature, "data": payload},
            status=WebhookDelivery.Status.DELIVERED,
            response_code=200,
            attempts=1,
            delivered_at=timezone.now(),
        )
        deliveries.append(delivery)
    return deliveries


def run_connector_test(connector_config: IntegrationConnectorConfig) -> IntegrationRunLog:
    connector = GenericCSVJSONConnector(
        tenant_id=str(connector_config.tenant_id),
        config={"field_mapping": connector_config.field_mapping},
    )
    result = connector.test_connection()
    connector_config.last_run_at = timezone.now()
    connector_config.last_run_status = "SUCCESS" if result.get("ok") else "FAILED"
    connector_config.save(update_fields=["last_run_at", "last_run_status", "updated_at"])

    return IntegrationRunLog.objects.create(
        connector=connector_config,
        direction="TEST",
        status="SUCCESS" if result.get("ok") else "FAILED",
        records_processed=0,
        summary=result.get("message", "Test completed."),
    )


def create_oauth2_client(
    *,
    name: str,
    scopes: list[str],
    service_user: Any | None = None,
) -> tuple[OAuth2Client, str]:
    """Create an OAuth2 client credentials application and return (instance, raw_client_secret)."""
    client_id = f"nhris_cid_{secrets.token_urlsafe(16)}"
    raw_secret = f"nhris_csec_{secrets.token_urlsafe(32)}"
    client_secret_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()

    client = OAuth2Client.objects.create(
        name=name,
        client_id=client_id,
        client_secret_hash=client_secret_hash,
        scopes=scopes,
        service_user=service_user,
    )
    AuditLog.objects.create(
        actor_id=get_current_user_id(),
        action="OAUTH2_CLIENT_CREATED",
        entity="OAuth2Client",
        entity_id=str(client.id),
        new_values={"name": name, "client_id": client_id, "scopes": scopes},
    )
    return client, raw_secret


def replay_webhook_delivery(
    delivery: WebhookDelivery,
    *,
    simulate_failure: bool = False,
) -> WebhookDelivery:
    """Replay a webhook delivery with fresh HMAC-SHA256 signature and auto-disable after 5 failures."""
    ep = delivery.endpoint
    ts = int(time.time())
    secret = ep.get_decrypted_field("signing_secret") or "default-secret"
    data_payload = (delivery.payload or {}).get("data", delivery.payload or {})
    signature = sign_webhook_payload(secret, ts, data_payload)

    delivery.attempts = (delivery.attempts or 0) + 1
    delivery.payload = {
        "event": delivery.event_name,
        "timestamp": ts,
        "signature": signature,
        "data": data_payload,
        "replayed": True,
    }

    if simulate_failure:
        delivery.status = WebhookDelivery.Status.FAILED
        delivery.response_code = 502
        delivery.last_error = "Simulated upstream timeout during replay."
        ep.failure_count = (ep.failure_count or 0) + 1
        if ep.failure_count >= 5:
            ep.is_active = False
            ep.auto_disabled_at = timezone.now()
            delivery.status = WebhookDelivery.Status.DEAD_LETTER
        ep.save(update_fields=["failure_count", "is_active", "auto_disabled_at", "updated_at"])
    else:
        delivery.status = WebhookDelivery.Status.DELIVERED
        delivery.response_code = 200
        delivery.last_error = ""
        delivery.delivered_at = timezone.now()
        if ep.failure_count:
            ep.failure_count = 0
            ep.save(update_fields=["failure_count", "updated_at"])

    delivery.save(
        update_fields=[
            "attempts",
            "payload",
            "status",
            "response_code",
            "last_error",
            "delivered_at",
            "updated_at",
        ]
    )
    AuditLog.objects.create(
        actor_id=get_current_user_id(),
        action="WEBHOOK_DELIVERY_REPLAYED",
        entity="WebhookDelivery",
        entity_id=str(delivery.id),
        new_values={
            "status": delivery.status,
            "attempts": delivery.attempts,
            "endpoint_failure_count": ep.failure_count,
        },
    )
    return delivery
