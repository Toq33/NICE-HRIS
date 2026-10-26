"""Serializers & ViewSets for Phase 3 Payroll & Compensation (Modules 14-22)."""
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from core.permissions import IsTenantMemberAndModuleEnabled
from organization.views import CompanyScopedViewSetMixin

from .models import (
    BonusRun,
    EmployeeLoan,
    EmployeeSalaryStructure,
    ExpenseClaim,
    PaymentBatch,
    PayrollPeriod,
    PayrollRun,
    Payslip,
    ProvidentFundLedger,
    SalaryComponent,
    StatutoryScheme,
    TaxSlab,
)
from .services import build_payslip_pdf_bytes, get_loan_outstanding_balance, lock_payroll_run


class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = [
            "id",
            "company",
            "name",
            "name_bn",
            "code",
            "component_type",
            "formula_type",
            "rate_or_amount",
            "currency",
            "is_taxable",
        ]
        read_only_fields = ["id"]


class EmployeeSalaryStructureSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_code = serializers.CharField(source="employee.employee_code", read_only=True)

    class Meta:
        model = EmployeeSalaryStructure
        fields = [
            "id",
            "company",
            "employee",
            "employee_name",
            "employee_code",
            "gross_amount",
            "basic_amount",
            "house_rent_amount",
            "medical_amount",
            "conveyance_amount",
            "entertainment_amount",
            "currency",
            "effective_from",
            "effective_to",
            "change_reason",
        ]
        read_only_fields = ["id"]


class StatutorySchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatutoryScheme
        fields = [
            "id",
            "company",
            "name",
            "code",
            "employee_rate_pct",
            "employer_rate_pct",
            "wage_ceiling_bdt",
            "wage_floor_bdt",
            "currency",
            "effective_from",
            "effective_to",
            "review_flag",
        ]
        read_only_fields = ["id"]


class TaxSlabSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxSlab
        fields = [
            "id",
            "company",
            "income_year",
            "slab_order",
            "threshold_amount_bdt",
            "tax_rate_pct",
            "currency",
            "review_flag",
        ]
        read_only_fields = ["id"]


class PayrollPeriodSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = PayrollPeriod
        fields = [
            "id",
            "company",
            "company_name",
            "name",
            "year",
            "month",
            "start_date",
            "end_date",
            "is_locked",
            "locked_at",
        ]
        read_only_fields = ["id", "locked_at"]


class PayrollRunSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    period_name = serializers.CharField(source="period.name", read_only=True)

    class Meta:
        model = PayrollRun
        fields = [
            "id",
            "company",
            "company_name",
            "period",
            "period_name",
            "run_number",
            "status",
            "employee_count",
            "total_gross_bdt",
            "total_deductions_bdt",
            "total_net_bdt",
            "currency",
            "total_net_in_words",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PayslipSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_code = serializers.CharField(source="employee.employee_code", read_only=True)
    department_name = serializers.CharField(source="employee.department.name", read_only=True)
    designation_title = serializers.CharField(source="employee.designation.title", read_only=True)
    period_name = serializers.CharField(source="payroll_run.period.name", read_only=True)

    class Meta:
        model = Payslip
        fields = [
            "id",
            "company",
            "payroll_run",
            "period_name",
            "employee",
            "employee_name",
            "employee_code",
            "department_name",
            "designation_title",
            "payslip_number",
            "status",
            "salary_days",
            "present_days",
            "absent_days",
            "nis_days",
            "basic_bdt",
            "house_rent_bdt",
            "medical_bdt",
            "conveyance_bdt",
            "entertainment_bdt",
            "overtime_bdt",
            "gross_bdt",
            "pf_employee_bdt",
            "pf_employer_bdt",
            "nis_employee_bdt",
            "nis_employer_bdt",
            "ait_tax_bdt",
            "loan_recovery_bdt",
            "revenue_stamp_bdt",
            "total_deductions_bdt",
            "net_bdt",
            "currency",
            "net_in_words",
            "snapshot_json",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BonusRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = BonusRun
        fields = [
            "id",
            "company",
            "name",
            "bonus_type",
            "effective_date",
            "pct_of_basic",
            "total_amount_bdt",
            "currency",
            "status",
        ]
        read_only_fields = ["id"]


class ExpenseClaimSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = ExpenseClaim
        fields = [
            "id",
            "company",
            "reference_no",
            "employee",
            "employee_name",
            "category",
            "claim_date",
            "amount_bdt",
            "currency",
            "description",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class EmployeeLoanSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    outstanding_balance_bdt = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeLoan
        fields = [
            "id",
            "company",
            "loan_number",
            "employee",
            "employee_name",
            "loan_type",
            "principal_bdt",
            "monthly_installment_bdt",
            "total_installments",
            "outstanding_balance_bdt",
            "disbursed_on",
            "currency",
            "status",
        ]
        read_only_fields = ["id"]

    def get_outstanding_balance_bdt(self, obj: EmployeeLoan) -> str:
        return str(get_loan_outstanding_balance(obj))


class ProvidentFundLedgerSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = ProvidentFundLedger
        fields = [
            "id",
            "employee",
            "employee_name",
            "contribution_type",
            "posted_on",
            "amount",
            "currency",
            "reason",
            "source_type",
        ]
        read_only_fields = ["id"]


class PaymentBatchSerializer(serializers.ModelSerializer):
    run_number = serializers.CharField(source="payroll_run.run_number", read_only=True)

    class Meta:
        model = PaymentBatch
        fields = [
            "id",
            "company",
            "payroll_run",
            "run_number",
            "batch_number",
            "payout_channel",
            "bank_or_mfs_name",
            "total_amount_bdt",
            "currency",
            "record_count",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SalaryComponentViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SalaryComponentSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 14

    def get_queryset(self):
        return self.filter_by_company(SalaryComponent.objects.all())


class EmployeeSalaryStructureViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = EmployeeSalaryStructureSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 14

    def get_queryset(self):
        return self.filter_by_company(EmployeeSalaryStructure.objects.select_related("employee").all())

    @extend_schema(summary="Bulk import salary structures with dry_run validation and per-row error reporting")
    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request: Request) -> Response:
        from django.db import transaction

        dry_run = bool(request.data.get("dry_run", True))
        rows = request.data.get("rows") or []
        errors = []
        valid_payloads = []
        for idx, row in enumerate(rows):
            ser = EmployeeSalaryStructureSerializer(data=row, context={"request": request})
            if ser.is_valid():
                valid_payloads.append((idx, ser))
            else:
                errors.append({"row": idx + 1, "errors": ser.errors})

        created_ids = []
        if not dry_run and not errors:
            with transaction.atomic():
                for _, ser in valid_payloads:
                    obj = ser.save()
                    created_ids.append(str(obj.id))

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


class StatutorySchemeViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = StatutorySchemeSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 20

    def get_queryset(self):
        return self.filter_by_company(StatutoryScheme.objects.all())


class TaxSlabViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = TaxSlabSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 20

    def get_queryset(self):
        return self.filter_by_company(TaxSlab.objects.all())


class PayrollPeriodViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = PayrollPeriodSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 15

    def get_queryset(self):
        return self.filter_by_company(PayrollPeriod.objects.select_related("company").all())


class PayrollRunViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = PayrollRunSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 15

    def get_queryset(self):
        return self.filter_by_company(PayrollRun.objects.select_related("company", "period").all())

    @extend_schema(summary="Lock a payroll run and its period permanently (immutable)")
    @action(detail=True, methods=["post"])
    def lock(self, request: Request, pk: str = None) -> Response:
        run = self.get_object()
        locked = lock_payroll_run(run)
        return Response(PayrollRunSerializer(locked).data, status=status.HTTP_200_OK)


class PayslipViewSet(CompanyScopedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = PayslipSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 22
    filterset_fields = ["payroll_run", "employee", "status"]

    def get_queryset(self):
        return self.filter_by_company(
            Payslip.objects.select_related(
                "company", "employee", "employee__department", "employee__designation", "payroll_run", "payroll_run__period"
            ).all()
        )

    @extend_schema(summary="Download Payslip as PDF generated via ReportLab")
    @action(detail=True, methods=["get"], url_path="pdf")
    def download_pdf(self, request: Request, pk: str = None):
        from django.http import HttpResponse

        slip = self.get_object()
        pdf_bytes = build_payslip_pdf_bytes(slip)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{slip.payslip_number}.pdf"'
        return response


class BonusRunViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = BonusRunSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 16

    def get_queryset(self):
        return self.filter_by_company(BonusRun.objects.all())


class ExpenseClaimViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ExpenseClaimSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 17

    def get_queryset(self):
        return self.filter_by_company(ExpenseClaim.objects.select_related("employee").all())


class EmployeeLoanViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = EmployeeLoanSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 18

    def get_queryset(self):
        return self.filter_by_company(EmployeeLoan.objects.select_related("employee").all())


class ProvidentFundLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProvidentFundLedgerSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 19

    def get_queryset(self):
        return ProvidentFundLedger.objects.select_related("employee").all()


class PaymentBatchViewSet(CompanyScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = PaymentBatchSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAndModuleEnabled]
    module_number = 21

    def get_queryset(self):
        return self.filter_by_company(PaymentBatch.objects.select_related("payroll_run").all())
