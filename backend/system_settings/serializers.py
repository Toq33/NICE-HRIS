"""Serializers for Module 42 (System Settings & Numbering) and Module 40 (Audit Log)."""
from rest_framework import serializers

from .models import Attachment, AuditLog, NumberSequence, TenantSetting


class TenantSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantSetting
        fields = [
            "id",
            "statutory_disclaimer",
            "pf_employee_rate_pct",
            "pf_employer_rate_pct",
            "revenue_stamp_bdt",
            "default_salary_breakdown_pct",
            "nis_days_rule",
            "audit_retention_days",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]


class NumberSequenceSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = NumberSequence
        fields = [
            "id",
            "company",
            "company_name",
            "code",
            "prefix",
            "include_year",
            "padding",
            "next_val",
        ]
        read_only_fields = ["id"]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor_id",
            "actor_email",
            "action",
            "entity",
            "entity_id",
            "old_values",
            "new_values",
            "ip_address",
            "created_at",
        ]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = [
            "id",
            "company",
            "entity_type",
            "entity_id",
            "file_name",
            "content_type",
            "file_size_bytes",
            "storage_key",
            "virus_scan_status",
            "access_count",
            "created_at",
        ]
        read_only_fields = ["id", "storage_key", "virus_scan_status", "access_count", "created_at"]
