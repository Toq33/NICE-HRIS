"""Rate limiting per API key, per tenant, and on login per docs/04-api-and-integrations.md & AGENTS.md Section 7."""
from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle

from .context import get_current_tenant_id


class TenantAndAPIKeyRateThrottle(SimpleRateThrottle):
    """Enforces per-API-key and per-tenant request rate limits."""

    scope = "tenant_api"

    def get_cache_key(self, request: Request, view) -> str | None:
        api_key = getattr(request, "api_key", None)
        if api_key is not None:
            ident = f"apikey:{api_key.id}"
        else:
            tenant_id = get_current_tenant_id() or getattr(getattr(request, "user", None), "tenant_id", None)
            if tenant_id:
                ident = f"tenant:{tenant_id}"
            elif request.user and request.user.is_authenticated:
                ident = f"user:{request.user.pk}"
            else:
                ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class LoginRateThrottle(SimpleRateThrottle):
    """Rate-limits login attempts by IP and email per AGENTS.md Section 7."""

    scope = "login"

    def get_cache_key(self, request: Request, view) -> str | None:
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
