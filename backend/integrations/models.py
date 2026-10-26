"""Models for Module 41: API Keys, Outbound Webhooks, Connector Configurations, and Run Logs."""
import ipaddress
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db import models

from core.models import SensitiveFieldMixin, TenantModel


def validate_webhook_url_ssrf_safe(url: str) -> None:
    """Enforce HTTPS-only and block loopback/private IP addresses (SSRF protection per docs/04)."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValidationError("Webhook URLs must use HTTPS.")
    hostname = parsed.hostname or ""
    if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0") or hostname.endswith(".internal"):
        raise ValidationError("Webhook URLs cannot target internal or loopback addresses (SSRF blocked).")
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValidationError("Webhook URLs cannot target private or reserved IP ranges (SSRF blocked).")
    except ValueError:
        # Hostname is a domain name, allowed
        pass


class APIKey(TenantModel):
    """Scoped, hashed, expiring API key for external software integrations (docs/04-api-and-integrations.md)."""

    name = models.CharField(max_length=120)
    key_prefix = models.CharField(max_length=16, db_index=True)
    key_hash = models.CharField(max_length=64, unique=True, db_index=True)
    service_user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="api_keys",
    )
    scopes = models.JSONField(
        default=list,
        help_text="List of module scopes e.g. ['employees:read', 'attendance:write']",
    )
    ip_allowlist = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Comma-separated allowed IPv4/IPv6 addresses",
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["key_hash"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.key_prefix}...)"


class WebhookEndpoint(TenantModel, SensitiveFieldMixin):
    """Outbound HTTPS webhook subscription with HMAC-SHA256 signing secret and auto-disable."""

    SENSITIVE_ENCRYPTED_FIELDS = ("signing_secret",)

    name = models.CharField(max_length=120)
    target_url = models.URLField(max_length=500, validators=[validate_webhook_url_ssrf_safe])
    events = models.JSONField(
        default=list,
        help_text="Subscribed events e.g. ['employee.created', 'leave.approved', 'payroll.run.approved']",
    )
    signing_secret = models.CharField(max_length=512)
    failure_count = models.PositiveSmallIntegerField(default=0)
    auto_disabled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "is_active"])]
        ordering = ["-created_at"]

    def clean(self) -> None:
        super().clean()
        validate_webhook_url_ssrf_safe(self.target_url)

    def save(self, *args, **kwargs) -> None:
        validate_webhook_url_ssrf_safe(self.target_url)
        self.encrypt_sensitive_fields()
        super().save(*args, **kwargs)


class WebhookDelivery(TenantModel):
    """Delivery log and replay record for outbound webhooks."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        DELIVERED = "DELIVERED", "Delivered"
        FAILED = "FAILED", "Failed"
        DEAD_LETTER = "DEAD_LETTER", "Dead Letter"

    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries")
    event_name = models.CharField(max_length=80, db_index=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    response_code = models.PositiveSmallIntegerField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "endpoint", "created_at"])]
        ordering = ["-created_at"]


class IntegrationConnectorConfig(TenantModel, SensitiveFieldMixin):
    """Per-tenant connector configuration and field mapping (Module 41)."""

    SENSITIVE_ENCRYPTED_FIELDS = ("encrypted_credentials",)

    connector_code = models.SlugField(max_length=50)
    name = models.CharField(max_length=120)
    is_enabled = models.BooleanField(default=False)
    schedule_cron = models.CharField(max_length=64, blank=True, default="")
    encrypted_credentials = models.TextField(blank=True, default="")
    field_mapping = models.JSONField(default=dict, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_run_status = models.CharField(max_length=32, blank=True, default="NEVER_RUN")

    class Meta:
        unique_together = [("tenant", "connector_code")]
        indexes = [models.Index(fields=["tenant", "connector_code"])]

    def save(self, *args, **kwargs) -> None:
        self.encrypt_sensitive_fields()
        super().save(*args, **kwargs)


class IntegrationRunLog(TenantModel):
    """Execution log for connector runs and CSV/JSON imports/exports."""

    connector = models.ForeignKey(
        IntegrationConnectorConfig,
        on_delete=models.CASCADE,
        related_name="run_logs",
    )
    direction = models.CharField(max_length=16, default="PULL")
    status = models.CharField(max_length=24, default="SUCCESS")
    records_processed = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    summary = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["tenant", "connector", "created_at"])]
        ordering = ["-created_at"]


class OAuth2Client(TenantModel):
    """OAuth2 Client Credentials app for machine-to-machine integrations (docs/04-api-and-integrations.md)."""

    name = models.CharField(max_length=120)
    client_id = models.CharField(max_length=64, unique=True, db_index=True)
    client_secret_hash = models.CharField(max_length=64, db_index=True)
    scopes = models.JSONField(
        default=list,
        help_text="Allowed OAuth2 scopes e.g. ['employees:read', 'payroll:read']",
    )
    service_user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="oauth2_clients",
    )
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["client_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.client_id})"
