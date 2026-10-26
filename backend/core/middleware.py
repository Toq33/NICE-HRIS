"""Middleware for tenant context lifecycle and Idempotency-Key enforcement."""
import hashlib
import json
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse

from .context import (
    clear_context,
    set_current_company_id,
    set_current_tenant_id,
    set_current_user_id,
)


class TenantResolutionMiddleware:
    """Ensures contextvars are always initialized and cleaned up around every HTTP request."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def _resolve_early_auth(self, request: HttpRequest) -> None:
        """Resolves session, JWT, or API-Key user/tenant context before downstream middleware."""
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            set_current_user_id(user.id)
            if getattr(user, "tenant_id", None):
                set_current_tenant_id(user.tenant_id)
            if getattr(user, "default_company_id", None):
                set_current_company_id(user.default_company_id)
            return

        # Check JWT Bearer header or cookie
        try:
            from rest_framework.request import Request as DRFRequest

            from .authentication import APIKeyAuthentication, CookieOrHeaderJWTAuthentication

            drf_req = DRFRequest(request)
            jwt_auth = CookieOrHeaderJWTAuthentication()
            auth_res = jwt_auth.authenticate(drf_req)
            if auth_res is None:
                api_key_auth = APIKeyAuthentication()
                auth_res = api_key_auth.authenticate(drf_req)
        except Exception:
            pass

    def __call__(self, request: HttpRequest) -> HttpResponse:
        clear_context()
        try:
            self._resolve_early_auth(request)
            response = self.get_response(request)
            return response
        finally:
            clear_context()


class IdempotencyMiddleware:
    """Supports `Idempotency-Key` header on POST/PUT/PATCH requests per docs/04-api-and-integrations.md."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method not in ("POST", "PUT", "PATCH"):
            return self.get_response(request)

        idem_key = request.headers.get("Idempotency-Key")
        if not idem_key or len(idem_key) > 128:
            return self.get_response(request)

        from django.db import transaction

        from system_settings.models import IdempotencyRecord

        body_hash = hashlib.sha256(request.body or b"").hexdigest()
        existing = IdempotencyRecord.objects.filter(
            key=idem_key,
            method=request.method,
            path=request.path,
        ).first()

        if existing:
            if existing.request_hash != body_hash:
                return JsonResponse(
                    {
                        "error": {
                            "code": "idempotency_conflict",
                            "message": "Idempotency-Key was already used with a different request payload.",
                            "details": {},
                        }
                    },
                    status=409,
                )
            return JsonResponse(
                json.loads(existing.response_body),
                status=existing.status_code,
                headers={"X-Idempotent-Replay": "true"},
            )

        response = self.get_response(request)
        if 200 <= response.status_code < 300 and hasattr(response, "content"):
            try:
                decoded = response.content.decode("utf-8")
                json.loads(decoded)
                with transaction.atomic():
                    IdempotencyRecord.objects.get_or_create(
                        key=idem_key,
                        method=request.method,
                        path=request.path,
                        defaults={
                            "request_hash": body_hash,
                            "status_code": response.status_code,
                            "response_body": decoded,
                        },
                    )
            except Exception:
                pass
        return response
