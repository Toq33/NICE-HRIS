"""Authentication classes supporting HTTP-only JWT cookies, Bearer tokens, and scoped API keys."""
import hashlib
from typing import Any

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication

from .context import set_current_company_id, set_current_tenant_id, set_current_user_id


class CookieOrHeaderJWTAuthentication(JWTAuthentication):
    """Authenticates via HTTP-only `access_token` cookie or `Authorization: Bearer <token>` header."""

    def authenticate(self, request: Request) -> tuple[Any, Any] | None:
        header = self.get_header(request)
        if header is None:
            raw_token = request.COOKIES.get("access_token")
        else:
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        self._apply_tenant_context(request, user)
        return (user, validated_token)

    def _apply_tenant_context(self, request: Request, user: Any) -> None:
        if not user or not user.is_authenticated:
            return
        set_current_user_id(user.id)

        # Allow platform superadmins to inspect a specific tenant via header if explicitly requested
        requested_tenant_id = request.headers.get("X-Tenant-ID")
        if user.is_platform_admin and requested_tenant_id:
            set_current_tenant_id(requested_tenant_id)
        elif getattr(user, "tenant_id", None):
            set_current_tenant_id(user.tenant_id)

        requested_company_id = request.headers.get("X-Company-ID")
        if requested_company_id:
            set_current_company_id(requested_company_id)
        elif getattr(user, "default_company_id", None):
            set_current_company_id(user.default_company_id)


class APIKeyAuthentication(BaseAuthentication):
    """Server-to-server authentication via `X-API-Key: nhris_...` header (docs/04-api-and-integrations.md)."""

    def authenticate(self, request: Request) -> tuple[Any, Any] | None:
        raw_key = request.headers.get("X-API-Key")
        if not raw_key:
            return None

        from integrations.models import APIKey

        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        api_key = (
            APIKey.unscoped_objects.select_related("tenant", "service_user")
            .filter(key_hash=key_hash, is_active=True, revoked_at__isnull=True)
            .first()
        )
        if not api_key:
            raise AuthenticationFailed("Invalid or revoked API key.")

        if api_key.expires_at and api_key.expires_at < timezone.now():
            raise AuthenticationFailed("API key has expired.")

        if api_key.ip_allowlist:
            client_ip = request.META.get("REMOTE_ADDR", "")
            allowed = [ip.strip() for ip in api_key.ip_allowlist.split(",") if ip.strip()]
            if allowed and client_ip not in allowed:
                raise AuthenticationFailed("Client IP is not in the API key allow-list.")

        APIKey.unscoped_objects.filter(pk=api_key.pk).update(last_used_at=timezone.now())
        set_current_tenant_id(api_key.tenant_id)
        if api_key.service_user_id:
            set_current_user_id(api_key.service_user_id)
        request.api_key = api_key
        try:
            from system_settings.models import AuditLog

            AuditLog.objects.create(
                actor_id=api_key.service_user_id,
                action="API_KEY_REQUEST",
                entity="APIKey",
                entity_id=str(api_key.id),
                new_values={
                    "api_key_id": str(api_key.id),
                    "key_prefix": api_key.key_prefix,
                    "method": request.method,
                    "path": request.path,
                },
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:500],
            )
        except Exception:
            pass
        return (api_key.service_user, api_key)
