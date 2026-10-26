"""Generic CSV/JSON Connector implementation (docs/04-api-and-integrations.md)."""
from typing import Any

from integrations.base import BaseIntegrationConnector


class GenericCSVJSONConnector(BaseIntegrationConnector):
    connector_code = "csv_json"
    display_name = "Generic CSV / JSON Import & Export Connector"

    def test_connection(self) -> dict[str, Any]:
        return {
            "ok": True,
            "connector": self.connector_code,
            "message": "CSV/JSON parser and schema validator ready.",
        }

    def map_fields(self, raw_record: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
        if not mapping:
            return dict(raw_record)
        return {target_field: raw_record.get(source_field) for source_field, target_field in mapping.items()}

    def pull(self, payload: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        rows = payload or []
        mapping = self.config.get("field_mapping", {})
        mapped = [self.map_fields(r, mapping) for r in rows]
        return {
            "status": "SUCCESS",
            "records_processed": len(mapped),
            "records_failed": 0,
            "preview": mapped[:5],
        }

    def push(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "status": "SUCCESS",
            "records_exported": len(records),
        }
