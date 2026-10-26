"""Adapter interface for all integration connectors per AGENTS.md Section 6 & docs/04."""
from abc import ABC, abstractmethod
from typing import Any


class BaseIntegrationConnector(ABC):
    """Every connector in `backend/integrations/<name>/` implements this contract."""

    connector_code: str = "base"
    display_name: str = "Base Connector"

    def __init__(self, tenant_id: str, config: dict[str, Any] | None = None) -> None:
        self.tenant_id = tenant_id
        self.config = config or {}

    @abstractmethod
    def test_connection(self) -> dict[str, Any]:
        """Verify credentials or file/endpoint reachability."""

    @abstractmethod
    def pull(self, payload: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Pull data from external source into HRM."""

    @abstractmethod
    def push(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Push HRM records to external target."""

    @abstractmethod
    def map_fields(self, raw_record: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
        """Transform external record keys to HRM canonical field names."""
