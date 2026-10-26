"""Thread-safe and async-safe tenant, company, and user context management."""
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any
from uuid import UUID

_current_tenant_id: ContextVar[UUID | None] = ContextVar("current_tenant_id", default=None)
_current_company_id: ContextVar[UUID | None] = ContextVar("current_company_id", default=None)
_current_user_id: ContextVar[UUID | None] = ContextVar("current_user_id", default=None)


def get_current_tenant_id() -> UUID | None:
    return _current_tenant_id.get()


def set_current_tenant_id(tenant_id: UUID | None) -> None:
    if isinstance(tenant_id, str):
        tenant_id = UUID(tenant_id)
    _current_tenant_id.set(tenant_id)


def get_current_company_id() -> UUID | None:
    return _current_company_id.get()


def set_current_company_id(company_id: UUID | None) -> None:
    if isinstance(company_id, str):
        company_id = UUID(company_id)
    _current_company_id.set(company_id)


def get_current_user_id() -> UUID | None:
    return _current_user_id.get()


def set_current_user_id(user_id: UUID | None) -> None:
    if isinstance(user_id, str):
        user_id = UUID(user_id)
    _current_user_id.set(user_id)


def clear_context() -> None:
    _current_tenant_id.set(None)
    _current_company_id.set(None)
    _current_user_id.set(None)


@contextmanager
def tenant_context(
    tenant: Any,
    company: Any = None,
    user: Any = None,
) -> Iterator[None]:
    """Context manager to temporarily scope operations to a specific tenant/company/user."""
    tenant_id = getattr(tenant, "id", tenant)
    company_id = getattr(company, "id", company) if company else None
    user_id = getattr(user, "id", user) if user else None

    token_tenant = _current_tenant_id.set(UUID(str(tenant_id)) if tenant_id else None)
    token_company = _current_company_id.set(UUID(str(company_id)) if company_id else None)
    token_user = _current_user_id.set(UUID(str(user_id)) if user_id else None)
    try:
        yield
    finally:
        _current_tenant_id.reset(token_tenant)
        _current_company_id.reset(token_company)
        _current_user_id.reset(token_user)
