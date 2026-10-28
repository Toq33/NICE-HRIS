"""Tenant-scoped ViewSets for Organization & Employee baselines with DataScope enforcement and Bulk Import."""
from datetime import date, timedelta
from decimal import Decimal

from django.db import models, transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from core.context import get_current_company_id
from core.permissions import IsTenantMemberAndModuleEnabled
from system_settings.models import AuditLog

from .models import (
    Branch,
    Company,
    CostCenter,
    Department,
    Designation,
    EmergencyContact,
    Employee,
    EmployeeDocument,
    EmployeeExperience,
    EmployeeQualification,
    EmploymentRecord,
    FamilyMember,
    Grade,
    ReportingLine,
    Section,
)
from .serializers import (
    BranchSerializer,
    CompanySerializer,
    CostCenterSerializer,
    DepartmentSerializer,
    DesignationSerializer,
    EmergencyContactSerializer,
    EmployeeDocumentSerializer,
    EmployeeExperienceSerializer,
    EmployeeQualificationSerializer,
    EmployeeSerializer,
    EmploymentRecordSerializer,
    FamilyMemberSerializer,
    GradeSerializer,
    ReportingLineSerializer,
    SectionSerializer,
)


class CompanyScopedViewSetMixin:
    """Filters by active company (`X-Company-ID` or `?company=`) and enforces user `DataScope` rules (Module 33 & 39)."""

    def filter_by_company(self, queryset):
        company_id = self.request.query_params.get("company") or get_current_company_id()
        if company_id and self.request.query_params.get("all_companies") != "true":
            if hasattr(queryset.model, "company_id"):
                queryset = queryset.filter(company_id=company_id)

        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated or getattr(user, "is_platform_admin", False):
            return queryset

        # Check explicit DataScope records if configured for this user
        scopes = list(user.data_scopes.all()) if hasattr(user, "data_scopes") else []
        if scopes:
            scope_types = {s.scope_type for s in scopes}
            if "ALL_TENANT" not in scope_types:
                if "OWN_AND_DIRECT_REPORTS" in scope_types:
                    emp_profile = getattr(user, "employee_profile", None)
                    if emp_profile:
                        if queryset.model is Employee:
                            queryset = queryset.filter(
                                models.Q(id=emp_profile.id) | models.Q(manager_id=emp_profile.id)
                            )
                        elif hasattr(queryset.model, "employee_id"):
                            queryset = queryset.filter(
                                models.Q(employee_id=emp_profile.id)
                                | models.Q(employee__manager_id=emp_profile.id)
                            )
                elif "DEPARTMENTS" in scope_types:
                    dept_ids = [did for s in scopes for did in (s.department_ids or [])]
                    if dept_ids:
                        if hasattr(queryset.model, "department_id"):
                            queryset = queryset.filter(department_id__in=dept_ids)
                        elif hasattr(queryset.model, "employee_id"):
                            queryset = queryset.filter(employee__department_id__in=dept_ids)
                elif "BRANCHES" in scope_types:
                    branch_ids = [bid for s in scopes for bid in (s.branch_ids or [])]
                    if branch_ids:
                        if hasattr(queryset.model, "branch_id"):
                            queryset = queryset.filter(branch_id__in=branch_ids)
                        elif hasattr(queryset.model, "employee_id"):
                            queryset = queryset.filter(employee__branch_id__in=branch_ids)
                elif "COMPANIES" in scope_types:
                    comp_ids = [cid for s in scopes for cid in (s.company_ids or [])]
                    if comp_ids and hasattr(queryset.model, "company_id"):
                        queryset = queryset.filter(company_id__in=comp_ids)
        return queryset


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 2
    search_fields = ["name", "name_bn", "code"]

    def get_queryset(self):
        return Company.objects.all()


class BranchViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 2
    search_fields = ["name", "name_bn", "code", "city"]

    def get_queryset(self):
        return self.filter_by_company(Branch.objects.select_related("company").all())


class DepartmentViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 2
    search_fields = ["name", "name_bn", "code"]

    def get_queryset(self):
        return self.filter_by_company(Department.objects.select_related("company", "branch").all())


class SectionViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 2

    def get_queryset(self):
        return self.filter_by_company(Section.objects.select_related("department").all())


class GradeViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 2

    def get_queryset(self):
        return self.filter_by_company(Grade.objects.all())


class DesignationViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = DesignationSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 2
    search_fields = ["title", "title_bn", "code"]

    def get_queryset(self):
        return self.filter_by_company(Designation.objects.select_related("grade").all())


class CostCenterViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = CostCenterSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 2

    def get_queryset(self):
        return self.filter_by_company(CostCenter.objects.all())


class ReportingLineViewSet(viewsets.ModelViewSet):
    serializer_class = ReportingLineSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 2
    filterset_fields = ["employee", "manager"]

    def get_queryset(self):
        return ReportingLine.objects.select_related("employee", "manager").all()


class EmployeeViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 3
    search_fields = ["employee_code", "full_name", "full_name_bn", "work_email"]
    filterset_fields = ["company", "branch", "department", "designation", "employment_status"]

    def get_queryset(self):
        qs = Employee.objects.select_related(
            "company", "branch", "department", "designation", "manager", "role"
        ).all()
        return self.filter_by_company(qs)

    @extend_schema(summary="Bulk import employees with dry_run validation and per-row error reporting (docs/04)")
    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request: Request) -> Response:
        dry_run = bool(request.data.get("dry_run", True))
        rows = request.data.get("rows") or []
        errors = []
        valid_payloads = []

        for idx, row in enumerate(rows):
            ser = EmployeeSerializer(data=row, context={"request": request})
            if ser.is_valid():
                valid_payloads.append((idx, ser, row))
            else:
                errors.append({"row": idx + 1, "errors": ser.errors})

        created_ids = []
        if not dry_run and not errors:
            with transaction.atomic():
                for _, ser, raw_row in valid_payloads:
                    emp = ser.save(
                        gross_salary_bdt=Decimal(str(raw_row.get("gross_salary_bdt", "45000.00"))),
                        national_id_encrypted=str(raw_row.get("national_id", "")),
                        bank_account_encrypted=str(raw_row.get("bank_account", "")),
                    )
                    created_ids.append(str(emp.id))
                AuditLog.objects.create(
                    actor_id=request.user.id,
                    actor_email=request.user.email,
                    action="EMPLOYEE_BULK_IMPORT",
                    entity="Employee",
                    entity_id="BULK",
                    new_values={"count": len(created_ids), "created_ids": created_ids},
                )

        return Response(
            {
                "dry_run": dry_run,
                "valid_count": len(valid_payloads),
                "error_count": len(errors),
                "errors": errors,
                "created_ids": created_ids,
            },
            status=status.HTTP_200_OK if dry_run or not errors else status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(summary="Inter-company transfer: closes employment in old company and opens in target company (docs/02)")
    @action(detail=True, methods=["post"], url_path="inter-company-transfer")
    def inter_company_transfer(self, request: Request, pk: str = None) -> Response:
        emp = self.get_object()
        target_company_id = request.data.get("target_company") or request.data.get("target_company_id")
        target_branch_id = request.data.get("target_branch") or request.data.get("target_branch_id")
        target_department_id = request.data.get("target_department") or request.data.get("target_department_id")
        target_designation_id = request.data.get("target_designation") or request.data.get("target_designation_id")
        effective_from_str = request.data.get("effective_from") or str(date.today())
        eff_date = date.fromisoformat(effective_from_str)

        target_company = Company.objects.get(pk=target_company_id)
        target_branch = (
            Branch.objects.get(pk=target_branch_id)
            if target_branch_id
            else (Branch.objects.filter(company=target_company).first() or emp.branch)
        )
        target_dept = (
            Department.objects.get(pk=target_department_id)
            if target_department_id
            else (Department.objects.filter(company=target_company).first() or emp.department)
        )
        target_desig = (
            Designation.objects.get(pk=target_designation_id)
            if target_designation_id
            else (Designation.objects.filter(company=target_company).first() or emp.designation)
        )

        with transaction.atomic():
            # Close active EmploymentRecord in current company
            EmploymentRecord.objects.filter(employee=emp, effective_to__isnull=True).update(
                effective_to=eff_date - timedelta(days=1),
                status="CLOSED_BY_TRANSFER",
            )
            # Open new EmploymentRecord in target company
            new_rec = EmploymentRecord.objects.create(
                company=target_company,
                employee=emp,
                contract_reference=f"TRN-{target_company.code}-{emp.employee_code}",
                contract_type="PERMANENT",
                branch=target_branch,
                department=target_dept,
                designation=target_desig,
                effective_from=eff_date,
                change_reason=request.data.get("reason", "Inter-company group transfer"),
                status="RUNNING",
            )
            from talent_relations.models import CareerMovement

            CareerMovement.objects.create(
                company=emp.company,
                employee=emp,
                movement_type="INTER_COMPANY_TRANSFER",
                target_company=target_company,
                new_designation=target_desig,
                effective_from=eff_date,
                previous_gross_bdt=emp.gross_salary_bdt,
                revised_gross_bdt=Decimal(str(request.data.get("revised_gross_bdt", emp.gross_salary_bdt))),
                change_reason=request.data.get("reason", "Inter-company group transfer"),
                status="APPROVED",
            )
            emp.company = target_company
            emp.branch = target_branch
            emp.department = target_dept
            emp.designation = target_desig
            emp.save()

            AuditLog.objects.create(
                actor_id=request.user.id,
                actor_email=request.user.email,
                action="INTER_COMPANY_TRANSFER",
                entity="Employee",
                entity_id=str(emp.id),
                new_values={
                    "target_company": str(target_company.id),
                    "employment_record_id": str(new_rec.id),
                    "effective_from": str(eff_date),
                },
            )
        return Response(EmployeeSerializer(emp, context={"request": request}).data)


class EmergencyContactViewSet(viewsets.ModelViewSet):
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 3
    filterset_fields = ["employee"]

    def get_queryset(self):
        return EmergencyContact.objects.select_related("employee").all()


class FamilyMemberViewSet(viewsets.ModelViewSet):
    serializer_class = FamilyMemberSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 3
    filterset_fields = ["employee", "is_nominee"]

    def get_queryset(self):
        return FamilyMember.objects.select_related("employee").all()


class EmployeeQualificationViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeQualificationSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 3
    filterset_fields = ["employee"]

    def get_queryset(self):
        return EmployeeQualification.objects.select_related("employee").all()


class EmployeeExperienceViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeExperienceSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 3
    filterset_fields = ["employee"]

    def get_queryset(self):
        return EmployeeExperience.objects.select_related("employee").all()


class EmploymentRecordViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = EmploymentRecordSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 3
    filterset_fields = ["employee", "company", "status"]

    def get_queryset(self):
        return self.filter_by_company(
            EmploymentRecord.objects.select_related("company", "employee", "department", "designation").all()
        )


class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 3
    filterset_fields = ["employee", "document_type"]

    def get_queryset(self):
        return EmployeeDocument.objects.select_related("employee").all()
