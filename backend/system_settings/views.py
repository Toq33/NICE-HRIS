"""Views for Module 42 (System Settings & Master Data) and Module 40 (Audit Logs)."""
import hashlib
import hmac
import time

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from core.permissions import IsTenantMemberAndModuleEnabled

from .models import Attachment, AuditLog, NumberSequence, TenantSetting
from .serializers import (
    AttachmentSerializer,
    AuditLogSerializer,
    NumberSequenceSerializer,
    TenantSettingSerializer,
)


class TenantSettingViewSet(viewsets.ModelViewSet):
    serializer_class = TenantSettingSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 42

    def get_queryset(self):
        return TenantSetting.objects.all()


class NumberSequenceViewSet(viewsets.ModelViewSet):
    serializer_class = NumberSequenceSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 42

    def get_queryset(self):
        return NumberSequence.objects.select_related("company").all()


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 40
    filterset_fields = ["entity", "action"]
    search_fields = ["actor_email", "entity", "entity_id"]

    def get_queryset(self):
        return AuditLog.objects.all()


class AttachmentViewSet(viewsets.ModelViewSet):
    """Generic S3/MinIO attachment management with virus-scan hook, signed URLs, and document access logging."""

    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 35
    filterset_fields = ["entity_type", "entity_id", "virus_scan_status"]

    def get_queryset(self):
        return Attachment.objects.all()

    @extend_schema(summary="Generate a short-lived signed download URL and record document access in AuditLog")
    @action(detail=True, methods=["post"], url_path="signed-url")
    def signed_url(self, request: Request, pk: str = None) -> Response:
        att = self.get_object()
        expires = int(time.time()) + 900
        sig_payload = f"{att.id}:{att.storage_key}:{expires}".encode()
        sig = hmac.new(settings.SECRET_KEY.encode(), sig_payload, hashlib.sha256).hexdigest()
        att.access_count += 1
        att.save(update_fields=["access_count", "updated_at"])
        AuditLog.objects.create(
            actor_id=request.user.id,
            actor_email=request.user.email,
            action="DOCUMENT_SIGNED_URL_ISSUED",
            entity=att.entity_type,
            entity_id=str(att.entity_id),
            new_values={"attachment_id": str(att.id), "file_name": att.file_name, "expires": expires},
        )
        return Response(
            {
                "attachment_id": str(att.id),
                "file_name": att.file_name,
                "signed_url": f"https://storage.nicehris.bd/download/{att.id}?expires={expires}&signature={sig}",
                "expires_at_epoch": expires,
            }
        )
