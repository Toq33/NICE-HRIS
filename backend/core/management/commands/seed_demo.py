"""Management command to seed Platform Admin, 2 Demo Tenants (Single-Company & Multi-Company), 30+ Employees each, and data across all 42 modules."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import DataScope, Role, RolePermission, User
from core.context import tenant_context
from integrations.models import IntegrationConnectorConfig, OAuth2Client, WebhookEndpoint
from organization.models import (
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
from payroll.models import (
    BonusRun,
    EmployeeLoan,
    EmployeeSalaryStructure,
    ExpenseClaim,
    LoanLedger,
    PayrollPeriod,
    SalaryComponent,
    StatutoryScheme,
    TaxSlab,
)
from payroll.services import generate_company_payroll_run
from platform_admin.models import EnabledModule, Plan, Tenant
from platform_admin.registry import ALL_42_MODULES
from platform_admin.services import provision_tenant
from system_settings.models import Attachment, AuditLog, NumberSequence, TenantSetting
from talent_relations.models import (
    AppraisalSurvey,
    AssetMovementLedger,
    CareerMovement,
    ClearanceItem,
    CompanyAsset,
    DisciplinaryCase,
    FinalSettlement,
    Goal,
    GrievanceCase,
    HealthSafetyRecord,
    HelpdeskTicket,
    Interview,
    JobApplicant,
    JobRequisition,
    ManpowerPlan,
    Offer,
    OnboardingChecklist,
    PerformanceAppraisal,
    ProbationReview,
    ResignationRequest,
    ReviewCycle,
    TrainingNomination,
    TrainingProgram,
)
from time_presence.models import (
    AttendanceDay,
    FieldDutyMovement,
    Holiday,
    LeaveLedger,
    LeaveType,
    MonthlyAttendanceSummary,
    OvertimeRequest,
    RosterBatch,
    Shift,
    WorkCalendar,
)
from time_presence.services import compute_nis_days, submit_leave_application
from workflows.models import (
    Announcement,
    LetterTemplate,
    Notification,
    PolicyDocument,
    ReportDefinition,
)
from workflows.services import render_letter_from_template

BD_FIRST_NAMES = [
    ("Tanvir", "তানভীর"),
    ("Nusrat", "নুসরাত"),
    ("Mahmudul", "মাহমুদুল"),
    ("Farhana", "ফারহানা"),
    ("Sabbir", "সাব্বির"),
    ("Tasnim", "তাসনিম"),
    ("Rakibul", "রাকিবুল"),
    ("Sadia", "সাদিয়া"),
    ("Mehedi", "মেহেদী"),
    ("Jannatul", "জান্নাতুল"),
    ("Ashraful", "আশরাফুল"),
    ("Nazia", "নাজিয়া"),
    ("Kamrul", "কামরুল"),
    ("Sharmin", "শারমিন"),
    ("Ariful", "আরিফুল"),
    ("Sumaiya", "সুমাইয়া"),
]

BD_LAST_NAMES = [
    ("Rahman", "রহমান"),
    ("Hossain", "হোসেন"),
    ("Islam", "ইসলাম"),
    ("Ahmed", "আহমেদ"),
    ("Chowdhury", "চৌধুরী"),
    ("Khan", "খান"),
    ("Akter", "আক্তার"),
    ("Siddique", "সিদ্দিকী"),
]


class Command(BaseCommand):
    help = "Seeds 2 demo tenants (Single-Company & Multi-Company) with 32-36 Bangladesh employees each and full 42-module data."

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("Seeding NICE HRIS Platform Admin, Plans, and 2 Demo Tenants (all 42 modules)...")

        all_mod_nums = [m["number"] for m in ALL_42_MODULES]

        plan_single, _ = Plan.objects.update_or_create(
            code="single-entity-pro",
            defaults={
                "name": "Standard Single-Company Plan",
                "description": "Full 42-module HRM suite for single-entity organizations in Bangladesh.",
                "max_employees": 250,
                "max_companies": 1,
                "monthly_price_bdt": Decimal("18500.00"),
                "currency": "BDT",
                "default_module_numbers": all_mod_nums,
            },
        )

        plan_group, _ = Plan.objects.update_or_create(
            code="enterprise-group",
            defaults={
                "name": "Enterprise Multi-Company Group Plan",
                "description": "Multi-entity conglomerate HRM with inter-company transfers & consolidated reporting.",
                "max_employees": 1000,
                "max_companies": 10,
                "monthly_price_bdt": Decimal("48000.00"),
                "currency": "BDT",
                "default_module_numbers": all_mod_nums,
            },
        )

        # Platform Superadmin (Super Admin)
        platform_admin, created = User.objects.update_or_create(
            email="platform.admin@nicehris.bd",
            defaults={
                "full_name": "Tariqul Islam (Super Admin)",
                "full_name_bn": "তারিকুল ইসলাম",
                "is_platform_admin": True,
                "is_staff": True,
                "is_superuser": True,
                "experience_mode": User.ExperienceMode.ADMIN,
                "can_view_salary": True,
                "can_view_medical": True,
                "has_approval_authority": True,
            },
        )
        if created:
            platform_admin.set_password("Pass1234!")
            platform_admin.save()

        # Tenant 1: Single-Company Tenant
        t1 = Tenant.objects.filter(slug="padma-apparel").first()
        if not t1:
            t1 = provision_tenant(
                name="Padma Apparel & Textiles Ltd.",
                name_bn="পদ্মা অ্যাপারেল অ্যান্ড টেক্সটাইলস লিমিটেড",
                slug="padma-apparel",
                plan=plan_single,
                multi_company_enabled=False,
                employee_limit=250,
                initial_company_name="Padma Apparel & Textiles Ltd.",
            )
            self._populate_single_company_tenant(t1)
        else:
            self._backfill_new_tables_if_needed(t1)

        # Tenant 2: Multi-Company Group Tenant
        t2 = Tenant.objects.filter(slug="jamuna-group").first()
        if not t2:
            t2 = provision_tenant(
                name="Jamuna Conglomerate Group",
                name_bn="যমুনা কনগ্লোমারেট গ্রুপ",
                slug="jamuna-group",
                plan=plan_group,
                multi_company_enabled=True,
                employee_limit=1000,
                initial_company_name="Jamuna Tech Solutions Ltd.",
            )
            self._populate_multi_company_tenant(t2)
        else:
            self._backfill_new_tables_if_needed(t2)

        self.stdout.write(self.style.SUCCESS("Demo seed completed! Both Single-Company and Multi-Company tenants ready."))

    def _backfill_new_tables_if_needed(self, tenant: Tenant) -> None:
        EnabledModule.objects.update_or_create(
            tenant=tenant,
            module_number=43,
            defaults={"module_slug": "roles-permissions-matrix", "is_enabled": True},
        )
        with tenant_context(tenant):
            self._ensure_seven_role_tabs_and_employee_roles(tenant)
            OAuth2Client.objects.get_or_create(
                client_id=f"nhris_cid_{tenant.slug}_erp",
                defaults={
                    "name": f"{tenant.name} ERP OAuth2 Service Client",
                    "client_secret_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "scopes": ["employees:read", "payroll:read", "attendance:write"],
                },
            )
            if EmergencyContact.objects.exists():
                return
            for company in Company.objects.all():
                employees = list(Employee.objects.filter(company=company)[:5])
                for emp in employees:
                    EmergencyContact.objects.create(
                        employee=emp,
                        name="Rafiqul Islam",
                        relationship="Spouse / Guardian",
                        phone="+8801711998877",
                        address="Uttara Sector 7, Dhaka",
                        is_primary=True,
                    )
                    FamilyMember.objects.create(
                        employee=emp,
                        full_name="Aisha Siddiqua",
                        relationship="SPOUSE",
                        date_of_birth=date(1994, 5, 14),
                        is_nominee=True,
                        nominee_share_pct=Decimal("100.0000"),
                    )
                    EmployeeQualification.objects.create(
                        employee=emp,
                        degree_or_certification="BBA in Human Resource Management",
                        institution="University of Dhaka",
                        passing_year=2018,
                        result_or_cgpa="CGPA 3.78 / 4.00",
                    )
                    EmployeeExperience.objects.create(
                        employee=emp,
                        employer_name="Meghna Industrial Textiles Ltd.",
                        designation_held="HR Officer",
                        start_date=date(2019, 1, 1),
                        end_date=emp.joining_date - timedelta(days=1),
                        responsibilities="Attendance, payroll verification, and factory compliance.",
                    )
                    EmploymentRecord.objects.create(
                        company=company,
                        employee=emp,
                        contract_reference=f"CNT-{emp.employee_code}-01",
                        contract_type="PERMANENT",
                        branch=emp.branch,
                        department=emp.department,
                        designation=emp.designation,
                        effective_from=emp.joining_date,
                        effective_to=None,
                        change_reason="Initial appointment",
                        status="RUNNING",
                    )
                    Attachment.objects.create(
                        company=company,
                        entity_type="EmployeeDocument",
                        entity_id=emp.id,
                        file_name=f"NID_Verified_{emp.employee_code}.pdf",
                        content_type="application/pdf",
                        file_size_bytes=245120,
                        storage_key=f"tenants/{tenant.slug}/employees/{emp.employee_code}/nid.pdf",
                        virus_scan_status=Attachment.ScanStatus.CLEAN,
                    )
                    EmployeeDocument.objects.create(
                        employee=emp,
                        document_type="NATIONAL_ID",
                        title=f"National ID Card - {emp.full_name}",
                        issue_date=date(2020, 1, 15),
                        expiry_date=date(2030, 1, 15),
                        storage_key=f"tenants/{tenant.slug}/employees/{emp.employee_code}/nid.pdf",
                        is_verified=True,
                    )

    def _populate_single_company_tenant(self, tenant: Tenant) -> None:
        with tenant_context(tenant):
            company = Company.objects.filter(is_primary=True).first()
            company.registration_no = "C-148920/2018"
            company.tin_number = "491827364510"
            company.address = "Plot 42, Gulshan Avenue, Gulshan-2, Dhaka-1212"
            company.save()

            branches = [
                Branch.objects.create(
                    company=company,
                    name="Gulshan Corporate HQ",
                    name_bn="গুলশান কর্পোরেট হেড অফিস",
                    code="DHK-HQ",
                    city="Dhaka",
                    address="Plot 42, Gulshan-2, Dhaka-1212",
                    latitude=Decimal("23.7925"),
                    longitude=Decimal("90.4078"),
                ),
                Branch.objects.create(
                    company=company,
                    name="Gazipur Knitting & Dyeing Plant",
                    name_bn="গাজীপুর নিটিং অ্যান্ড ডাইং প্ল্যান্ট",
                    code="GZP-PLT",
                    city="Gazipur",
                    address="Konabari Industrial Area, Gazipur",
                    latitude=Decimal("24.0023"),
                    longitude=Decimal("90.3264"),
                ),
                Branch.objects.create(
                    company=company,
                    name="Chattogram Export Hub",
                    name_bn="চট্টগ্রাম এক্সপোর্ট হাব",
                    code="CTG-EXP",
                    city="Chattogram",
                    address="Agrabad Commercial Area, Chattogram",
                    latitude=Decimal("22.3264"),
                    longitude=Decimal("91.8123"),
                ),
            ]

            depts = [
                Department.objects.create(
                    company=company, branch=branches[0], name="Human Resources & Admin", name_bn="মানবসম্পদ ও প্রশাসন", code="HR", approved_headcount=10
                ),
                Department.objects.create(
                    company=company, branch=branches[0], name="Finance & Accounts", name_bn="অর্থ ও হিসাব", code="FIN", approved_headcount=12
                ),
                Department.objects.create(
                    company=company, branch=branches[1], name="Garment Production & QA", name_bn="উৎপাদন ও মান নিয়ন্ত্রণ", code="PROD", approved_headcount=25
                ),
                Department.objects.create(
                    company=company, branch=branches[1], name="Supply Chain & Merchandising", name_bn="সাপ্লাই চেইন ও মার্চেন্ডাইজিং", code="SCM", approved_headcount=15
                ),
                Department.objects.create(
                    company=company, branch=branches[0], name="IT & ERP Operations", name_bn="তথ্যপ্রযুক্তি বিভাগ", code="IT", approved_headcount=8
                ),
                Department.objects.create(
                    company=company, branch=branches[2], name="Export & Logistics", name_bn="রপ্তানি ও লজিস্টিকস", code="EXP", approved_headcount=10
                ),
            ]

            grades = [
                Grade.objects.create(company=company, name="Grade G1 - Executive Leadership", code="G1", rank_order=1, min_gross_bdt=Decimal("120000"), max_gross_bdt=Decimal("250000")),
                Grade.objects.create(company=company, name="Grade G2 - Senior Management", code="G2", rank_order=2, min_gross_bdt=Decimal("75000"), max_gross_bdt=Decimal("130000")),
                Grade.objects.create(company=company, name="Grade G3 - Mid Management & Specialist", code="G3", rank_order=3, min_gross_bdt=Decimal("45000"), max_gross_bdt=Decimal("80000")),
                Grade.objects.create(company=company, name="Grade G4 - Officer & Associate", code="G4", rank_order=4, min_gross_bdt=Decimal("25000"), max_gross_bdt=Decimal("50000")),
            ]

            designations = [
                Designation.objects.create(company=company, title="Head of Human Resources", title_bn="মানবসম্পদ প্রধান", code="DES-HHR", grade=grades[0]),
                Designation.objects.create(company=company, title="Engineering & Production Manager", title_bn="প্রোডাকশন ম্যানেজার", code="DES-PM", grade=grades[1]),
                Designation.objects.create(company=company, title="Senior Merchandiser", title_bn="সিনিয়র মার্চেন্ডাইজার", code="DES-SM", grade=grades[2]),
                Designation.objects.create(company=company, title="Quality Assurance Specialist", title_bn="মান নিয়ন্ত্রণ বিশেষজ্ঞ", code="DES-QA", grade=grades[2]),
                Designation.objects.create(company=company, title="HR & Payroll Executive", title_bn="এইচআর ও পেরোল এক্সিকিউটিভ", code="DES-HRE", grade=grades[3]),
                Designation.objects.create(company=company, title="Software & Systems Engineer", title_bn="সফটওয়্যার ইঞ্জিনিয়ার", code="DES-SSE", grade=grades[2]),
            ]

            cc = CostCenter.objects.create(company=company, name="Padma Operations Center", code="CC-PADMA-01", budget_bdt=Decimal("25000000.00"))

            self._create_roles_and_settings(tenant, [company])

            hr_user = self._create_user(
                email="hr.admin@padmaapparel.bd",
                full_name="Nusrat Jahan (HR Admin)",
                full_name_bn="নুসরাত জাহান",
                tenant=tenant,
                default_company=company,
                allowed_companies=[company],
                mode=User.ExperienceMode.ADMIN,
                can_view_salary=True,
                has_approval=True,
            )
            mgr_user = self._create_user(
                email="manager@padmaapparel.bd",
                full_name="Mahmudul Hasan (Line Manager)",
                full_name_bn="মাহমুদুল হাসান",
                tenant=tenant,
                default_company=company,
                allowed_companies=[company],
                mode=User.ExperienceMode.MANAGER,
                can_view_salary=False,
                has_approval=True,
            )
            emp_user = self._create_user(
                email="employee@padmaapparel.bd",
                full_name="Sabbir Ahmed (Employee)",
                full_name_bn="সাব্বির আহমেদ",
                tenant=tenant,
                default_company=company,
                allowed_companies=[company],
                mode=User.ExperienceMode.EMPLOYEE,
                can_view_salary=False,
                has_approval=False,
            )

            created_employees: list[Employee] = []
            for idx in range(1, 33):
                fn, fn_bn = BD_FIRST_NAMES[(idx - 1) % len(BD_FIRST_NAMES)]
                ln, ln_bn = BD_LAST_NAMES[(idx // 2) % len(BD_LAST_NAMES)]
                full_en = f"{fn} {ln}"
                full_bn = f"{fn_bn} {ln_bn}"
                emp_code = f"PAD-{str(idx).zfill(4)}"
                branch = branches[(idx - 1) % len(branches)]
                dept = depts[(idx - 1) % len(depts)]
                desig = designations[(idx - 1) % len(designations)]
                gross = Decimal(str(35000 + (idx * 2500)))

                linked_user = None
                if idx == 1:
                    full_en, full_bn = "Nusrat Jahan", "নুসরাত জাহান"
                    linked_user = hr_user
                    dept = depts[0]
                    desig = designations[0]
                elif idx == 2:
                    full_en, full_bn = "Mahmudul Hasan", "মাহমুদুল হাসান"
                    linked_user = mgr_user
                    dept = depts[2]
                    desig = designations[1]
                elif idx == 3:
                    full_en, full_bn = "Sabbir Ahmed", "সাব্বির আহমেদ"
                    linked_user = emp_user
                    dept = depts[4]
                    desig = designations[5]

                emp = Employee.objects.create(
                    company=company,
                    employee_code=emp_code,
                    full_name=full_en,
                    full_name_bn=full_bn,
                    work_email=f"{fn.lower()}.{ln.lower()}{idx}@padmaapparel.bd",
                    phone=f"+8801711{str(100000 + idx)[-6:]}",
                    joining_date=date(2023, 1, 1) + timedelta(days=idx * 12),
                    employment_status=Employee.EmploymentStatus.PROBATION if idx > 28 else Employee.EmploymentStatus.PERMANENT,
                    branch=branch,
                    department=dept,
                    designation=desig,
                    grade=desig.grade,
                    cost_center=cc,
                    manager=created_employees[1] if len(created_employees) >= 2 else (created_employees[0] if created_employees else None),
                    user=linked_user,
                    gross_salary_bdt=gross,
                    national_id_encrypted=f"199{idx % 9}26948100{str(idx).zfill(2)}",
                    bank_name="BRAC Bank PLC" if idx % 2 == 0 else "Dutch-Bangla Bank PLC",
                    bank_account_encrypted=f"1501204891{str(idx).zfill(4)}",
                )
                created_employees.append(emp)
                if emp.manager:
                    ReportingLine.objects.create(
                        employee=emp,
                        manager=emp.manager,
                        effective_from=emp.joining_date,
                        change_reason="Initial onboarding assignment",
                    )

            self._seed_all_modules_for_company(tenant, company, created_employees, depts, designations)
            self._ensure_seven_role_tabs_and_employee_roles(tenant)

    def _populate_multi_company_tenant(self, tenant: Tenant) -> None:
        with tenant_context(tenant):
            c1 = Company.objects.filter(is_primary=True).first()
            c1.code = "JTSL"
            c1.name = "Jamuna Tech Solutions Ltd."
            c1.name_bn = "যমুনা টেক সলিউশনস লিমিটেড"
            c1.registration_no = "C-162001/2020"
            c1.address = "Banani Road 11, Dhaka-1213"
            c1.save()

            c2 = Company.objects.create(
                name="Jamuna Agro & Foods Ltd.",
                name_bn="যমুনা অ্যাগ্রো অ্যান্ড ফুডস লিমিটেড",
                code="JAFL",
                registration_no="C-162002/2020",
                address="Tejgaon Industrial Area, Dhaka-1208",
                is_primary=False,
            )
            c3 = Company.objects.create(
                name="Jamuna Logistics & Supply Chain Ltd.",
                name_bn="যমুনা লজিস্টিকস অ্যান্ড সাপ্লাই চেইন লিমিটেড",
                code="JLSL",
                registration_no="C-162003/2021",
                address="Strand Road, Chattogram",
                is_primary=False,
            )
            companies = [c1, c2, c3]

            for comp in companies[1:]:
                for seq_code, prefix in [("EMPLOYEE", comp.code), ("LEAVE_REQUEST", "LR"), ("PAYSLIP", "PS")]:
                    NumberSequence.objects.get_or_create(
                        tenant=tenant,
                        company=comp,
                        code=seq_code,
                        defaults={"prefix": prefix, "padding": 4, "next_val": 1},
                    )

            self._create_roles_and_settings(tenant, companies)

            group_hr = self._create_user(
                email="group.hr@jamunagroup.bd",
                full_name="Farhana Rahman (Group HR Director)",
                full_name_bn="ফারহানা রহমান",
                tenant=tenant,
                default_company=c1,
                allowed_companies=companies,
                mode=User.ExperienceMode.ADMIN,
                can_view_salary=True,
                has_approval=True,
            )
            group_mgr = self._create_user(
                email="manager@jamunagroup.bd",
                full_name="Tanvir Chowdhury (Engineering Lead)",
                full_name_bn="তানভীর চৌধুরী",
                tenant=tenant,
                default_company=c1,
                allowed_companies=[c1, c2],
                mode=User.ExperienceMode.MANAGER,
                can_view_salary=False,
                has_approval=True,
            )
            group_emp = self._create_user(
                email="employee@jamunagroup.bd",
                full_name="Tasnim Akter (Product Specialist)",
                full_name_bn="তাসনিম আক্তার",
                tenant=tenant,
                default_company=c1,
                allowed_companies=[c1],
                mode=User.ExperienceMode.EMPLOYEE,
                can_view_salary=False,
                has_approval=False,
            )

            global_idx = 1
            for c_idx, comp in enumerate(companies):
                b1 = Branch.objects.create(
                    company=comp,
                    name=f"{comp.code} Dhaka Central Office",
                    name_bn=f"{comp.name_bn} ঢাকা অফিস",
                    code=f"{comp.code}-DHK",
                    city="Dhaka",
                    latitude=Decimal("23.7937"),
                    longitude=Decimal("90.4066"),
                )
                b2 = Branch.objects.create(
                    company=comp,
                    name=f"{comp.code} Regional Operations Center",
                    name_bn=f"{comp.name_bn} আঞ্চলিক কার্যালয়",
                    code=f"{comp.code}-REG",
                    city="Sylhet" if c_idx == 0 else ("Bogura" if c_idx == 1 else "Chattogram"),
                    latitude=Decimal("24.8949"),
                    longitude=Decimal("91.8687"),
                )
                d1 = Department.objects.create(company=comp, branch=b1, name="People & Culture", name_bn="মানবসম্পদ বিভাগ", code="PNC", approved_headcount=10)
                d2 = Department.objects.create(company=comp, branch=b1, name="Core Operations & Delivery", name_bn="কোর অপারেশনস", code="OPS", approved_headcount=20)
                d3 = Department.objects.create(company=comp, branch=b2, name="Commercial & Growth", name_bn="বাণিজ্যিক ও প্রবৃদ্ধি", code="COM", approved_headcount=12)

                g1 = Grade.objects.create(company=comp, name="Band M1 - Director / Lead", code="M1", rank_order=1, min_gross_bdt=Decimal("110000"), max_gross_bdt=Decimal("220000"))
                g2 = Grade.objects.create(company=comp, name="Band M2 - Senior Specialist", code="M2", rank_order=2, min_gross_bdt=Decimal("55000"), max_gross_bdt=Decimal("105000"))

                des1 = Designation.objects.create(company=comp, title="Department Lead", title_bn="বিভাগীয় প্রধান", code="DL", grade=g1)
                des2 = Designation.objects.create(company=comp, title="Senior Specialist", title_bn="সিনিয়র স্পেশালিস্ট", code="SS", grade=g2)

                comp_employees: list[Employee] = []
                comp_lead = None
                for local_i in range(1, 13):
                    fn, fn_bn = BD_FIRST_NAMES[(global_idx - 1) % len(BD_FIRST_NAMES)]
                    ln, ln_bn = BD_LAST_NAMES[(global_idx // 2) % len(BD_LAST_NAMES)]
                    full_en = f"{fn} {ln}"
                    full_bn = f"{fn_bn} {ln_bn}"
                    linked_u = None
                    if global_idx == 1:
                        full_en, full_bn = "Farhana Rahman", "ফারহানা রহমান"
                        linked_u = group_hr
                    elif global_idx == 2:
                        full_en, full_bn = "Tanvir Chowdhury", "তানভীর চৌধুরী"
                        linked_u = group_mgr
                    elif global_idx == 3:
                        full_en, full_bn = "Tasnim Akter", "তাসনিম আক্তার"
                        linked_u = group_emp

                    emp = Employee.objects.create(
                        company=comp,
                        employee_code=f"{comp.code}-{str(local_i).zfill(4)}",
                        full_name=full_en,
                        full_name_bn=full_bn,
                        work_email=f"{fn.lower()}.{ln.lower()}{global_idx}@jamunagroup.bd",
                        phone=f"+8801819{str(200000 + global_idx)[-6:]}",
                        joining_date=date(2022, 6, 1) + timedelta(days=global_idx * 10),
                        employment_status=Employee.EmploymentStatus.PERMANENT,
                        branch=b1 if local_i % 2 == 1 else b2,
                        department=[d1, d2, d3][(local_i - 1) % 3],
                        designation=des1 if local_i <= 2 else des2,
                        grade=g1 if local_i <= 2 else g2,
                        manager=comp_lead,
                        user=linked_u,
                        gross_salary_bdt=Decimal(str(45000 + (local_i * 4500))),
                        national_id_encrypted=f"199{global_idx % 9}30192837{str(global_idx).zfill(2)}",
                        bank_name="Eastern Bank PLC",
                        bank_account_encrypted=f"1041070982{str(global_idx).zfill(4)}",
                    )
                    comp_employees.append(emp)
                    if local_i == 1:
                        comp_lead = emp
                    global_idx += 1

                self._seed_all_modules_for_company(tenant, comp, comp_employees, [d1, d2, d3], [des1, des2])
            self._ensure_seven_role_tabs_and_employee_roles(tenant)

    def _seed_all_modules_for_company(
        self,
        tenant: Tenant,
        company: Company,
        employees: list[Employee],
        depts: list[Department],
        designations: list[Designation],
    ) -> None:
        """Populates realistic Bangladesh data across Phases 1-6 for a company."""
        # Phase 1: Policies, Letter Templates, Announcements & Child Employee Profile Records
        Section.objects.get_or_create(
            company=company,
            department=depts[0],
            code="SEC-OPS",
            defaults={"name": "Core Operations Section", "name_bn": "কোর অপারেশনস সেকশন"},
        )
        for emp in employees[:5]:
            EmergencyContact.objects.create(
                employee=emp,
                name="Rafiqul Islam",
                relationship="Spouse / Guardian",
                phone="+8801711998877",
                address="Uttara Sector 7, Dhaka",
                is_primary=True,
            )
            FamilyMember.objects.create(
                employee=emp,
                full_name="Aisha Siddiqua",
                relationship="SPOUSE",
                date_of_birth=date(1994, 5, 14),
                is_nominee=True,
                nominee_share_pct=Decimal("100.0000"),
            )
            EmployeeQualification.objects.create(
                employee=emp,
                degree_or_certification="BBA in Human Resource Management",
                institution="University of Dhaka",
                passing_year=2018,
                result_or_cgpa="CGPA 3.78 / 4.00",
            )
            EmployeeExperience.objects.create(
                employee=emp,
                employer_name="Meghna Industrial Textiles Ltd.",
                designation_held="HR Officer",
                start_date=date(2019, 1, 1),
                end_date=emp.joining_date - timedelta(days=1),
                responsibilities="Attendance, payroll verification, and factory compliance.",
            )
            EmploymentRecord.objects.create(
                company=company,
                employee=emp,
                contract_reference=f"CNT-{emp.employee_code}-01",
                contract_type="PERMANENT",
                branch=emp.branch,
                department=emp.department,
                designation=emp.designation,
                effective_from=emp.joining_date,
                effective_to=None,
                change_reason="Initial appointment",
                status="RUNNING",
            )
            Attachment.objects.create(
                company=company,
                entity_type="EmployeeDocument",
                entity_id=emp.id,
                file_name=f"NID_Verified_{emp.employee_code}.pdf",
                content_type="application/pdf",
                file_size_bytes=245120,
                storage_key=f"tenants/{tenant.slug}/employees/{emp.employee_code}/nid.pdf",
                virus_scan_status=Attachment.ScanStatus.CLEAN,
            )
            EmployeeDocument.objects.create(
                employee=emp,
                document_type="NATIONAL_ID",
                title=f"National ID Card - {emp.full_name}",
                issue_date=date(2020, 1, 15),
                expiry_date=date(2030, 1, 15),
                storage_key=f"tenants/{tenant.slug}/employees/{emp.employee_code}/nid.pdf",
                is_verified=True,
            )

        PolicyDocument.objects.create(
            company=company,
            title="Bangladesh Labour Rules & Leave Policy 2026",
            title_bn="বাংলাদেশ শ্রম বিধি ও ছুটি নীতিমালা ২০২৬",
            category="Leave & Attendance",
            version="2.1",
            effective_date=date(2026, 1, 1),
            content_markdown="All permanent employees are entitled to 10 days Casual Leave, 14 days Sick Leave, and 18 days Earned Leave per calendar year. Friday is the standard weekly off.",
            requires_acknowledgment=True,
            acknowledged_count=len(employees) - 2,
        )
        tmpl = LetterTemplate.objects.create(
            company=company,
            name="Standard Appointment Letter (Bangladesh)",
            code=f"appt-{company.code.lower()}",
            letter_type="APPOINTMENT",
            version=1,
            language="EN",
            body_template="Dear {{employee_name}} ({{employee_name_bn}}),\nWe are pleased to appoint you as {{designation}} in the {{department}} department at {{company_name}} effective {{joining_date}} with a monthly gross compensation of BDT {{gross_salary}}.",
        )
        render_letter_from_template(
            company=company,
            employee=employees[0],
            template=tmpl,
            reference_no=f"LTR-{company.code}-2026-001",
        )

        Announcement.objects.create(
            company=company,
            title="October 2026 Payroll & NIS Days Verification Notice",
            title_bn="অক্টোবর ২০২৬ বেতন ও এনআইএস দিবস যাচাইকরণ বিজ্ঞপ্তি",
            category="NOTICE",
            body="Department heads are requested to confirm monthly attendance summaries and NIS insurable days before the 28th of the month.",
            is_pinned=True,
        )

        # Phase 2: Calendar, Holidays, Shifts, Roster, Attendance, Leave
        cal = WorkCalendar.objects.create(
            company=company,
            name=f"{company.code} Standard Bangladesh Calendar 2026",
            year=2026,
            weekly_off_days=["FRI"],
        )
        for h_name, h_bn, h_date, h_type in [
            ("Shaheed Day & International Mother Language Day", "শহীদ দিবস ও আন্তর্জাতিক মাতৃভাষা দিবস", date(2026, 2, 21), Holiday.HolidayType.PUBLIC),
            ("Independence & National Day", "স্বাধীনতা ও জাতীয় দিবস", date(2026, 3, 26), Holiday.HolidayType.PUBLIC),
            ("Pohela Boishakh (Bangla New Year)", "পহেলা বৈশাখ", date(2026, 4, 14), Holiday.HolidayType.PUBLIC),
            ("Eid-ul-Fitr Holiday Block", "ঈদুল ফিতর ছুটি", date(2026, 3, 20), Holiday.HolidayType.FESTIVAL),
            ("Victory Day of Bangladesh", "বিজয় দিবস", date(2026, 12, 16), Holiday.HolidayType.PUBLIC),
        ]:
            Holiday.objects.create(company=company, calendar=cal, name=h_name, name_bn=h_bn, date=h_date, holiday_type=h_type)

        shift_day = Shift.objects.create(
            company=company, name="General Day Shift (09:00 - 18:00)", code="SH-GEN", start_time=time(9, 0), end_time=time(18, 0), crosses_midnight=False
        )
        Shift.objects.create(
            company=company, name="Night Production Shift (22:00 - 06:00)", code="SH-NGT", start_time=time(22, 0), end_time=time(6, 0), crosses_midnight=True
        )
        RosterBatch.objects.create(
            company=company,
            name=f"October 2026 General Roster ({company.code})",
            shift=shift_day,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
            status="APPROVED",
            employee_count=len(employees),
        )

        lt_casual = LeaveType.objects.create(company=company, name="Casual Leave", name_bn="নৈমিত্তিক ছুটি", code="CL", annual_quota_days=Decimal("10.00"))
        lt_sick = LeaveType.objects.create(company=company, name="Sick / Medical Leave", name_bn="অসুস্থতাজনিত ছুটি", code="SL", annual_quota_days=Decimal("14.00"))
        lt_annual = LeaveType.objects.create(
            company=company,
            name="Earned / Annual Leave",
            name_bn="অর্জিত ছুটি",
            code="EL",
            annual_quota_days=Decimal("18.00"),
            carry_forward_allowed=True,
            max_carry_forward_days=Decimal("40.00"),
            encashment_allowed=True,
        )

        today = date(2026, 10, 26)
        for i, emp in enumerate(employees):
            for lt in (lt_casual, lt_sick, lt_annual):
                LeaveLedger.objects.create(
                    employee=emp,
                    leave_type=lt,
                    posted_on=date(2026, 1, 1),
                    quantity=lt.annual_quota_days,
                    reason="2026 Annual Opening Entitlement Accrual",
                    source_type="ACCRUAL",
                )

            AttendanceDay.objects.create(
                company=company,
                employee=emp,
                shift=shift_day,
                work_date=today,
                check_in=timezone.make_aware(datetime.combine(today, time(8, 55 if i % 4 != 0 else 9, 22))),
                check_out=timezone.make_aware(datetime.combine(today, time(18, 10))),
                status=AttendanceDay.DayStatus.LATE if i % 4 == 0 else AttendanceDay.DayStatus.PRESENT,
                worked_hours=Decimal("8.25"),
                extra_hours=Decimal("0.25") if i % 3 == 0 else Decimal("0.00"),
                late_minutes=22 if i % 4 == 0 else 0,
                source="BIOMETRIC" if i % 2 == 0 else "MOBILE",
                within_geofence=True,
            )

            present_d = 22 if i % 5 != 0 else 21
            absent_d = 0 if i % 5 != 0 else 1
            paid_leave_d = 2
            paid_hol_d = 2
            nis_d = compute_nis_days(
                present_days=present_d,
                paid_leave_days=paid_leave_d,
                paid_holidays=paid_hol_d,
            )
            MonthlyAttendanceSummary.objects.create(
                company=company,
                employee=emp,
                year=2026,
                month=10,
                status=MonthlyAttendanceSummary.Status.CONFIRMED if i < 6 else MonthlyAttendanceSummary.Status.APPROVED,
                salary_days=30,
                present_days=present_d,
                weekend_days=4,
                absent_days=absent_d,
                late_days=1 if i % 4 == 0 else 0,
                paid_holidays=paid_hol_d,
                paid_leave_days=paid_leave_d,
                nis_days=nis_d,
            )

        # Submit sample Leave, Overtime & Field Duty requests
        submit_leave_application(
            company=company,
            employee=employees[2],
            leave_type=lt_casual,
            start_date=date(2026, 11, 2),
            end_date=date(2026, 11, 3),
            days_requested=Decimal("2.00"),
            reason="Family event in Rajshahi",
            reference_no=f"LR-{company.code}-2026-154",
        )
        OvertimeRequest.objects.create(
            company=company,
            employee=employees[2],
            work_date=today - timedelta(days=2),
            requested_hours=Decimal("3.00"),
            approved_hours=Decimal("3.00"),
            rate_multiplier=Decimal("2.0000"),
            reason="Shipment container release deadline",
            status=OvertimeRequest.Status.APPROVED,
        )
        FieldDutyMovement.objects.create(
            company=company,
            employee=employees[1],
            movement_type="FIELD_VISIT",
            work_date=today,
            client_or_location="Motijheel Commercial Bank Branch & EPZ Office",
            latitude=Decimal("23.7330"),
            longitude=Decimal("90.4172"),
            status=FieldDutyMovement.Status.APPROVED,
        )

        # Phase 3: Salary Components, Structures, Statutory Scheme (NIS), Tax Slabs, Payroll Run & Payslips
        for code, name, name_bn, ctype, formula, rate in [
            ("BASIC", "Basic Salary (50% of Gross)", "মূল বেতন", SalaryComponent.ComponentType.EARNING, "PCT_OF_GROSS", Decimal("50.0000")),
            ("HRA", "House Rent Allowance (25% of Gross)", "বাড়ি ভাড়া ভাতা", SalaryComponent.ComponentType.EARNING, "PCT_OF_GROSS", Decimal("25.0000")),
            ("MED", "Medical Allowance (10% of Gross)", "চিকিৎসা ভাতা", SalaryComponent.ComponentType.EARNING, "PCT_OF_GROSS", Decimal("10.0000")),
            ("CONV", "Conveyance Allowance (10% of Gross)", "যাতায়াত ভাতা", SalaryComponent.ComponentType.EARNING, "PCT_OF_GROSS", Decimal("10.0000")),
            ("ENT", "Entertainment Allowance (5% of Gross)", "আপ্যায়ন ভাতা", SalaryComponent.ComponentType.EARNING, "PCT_OF_GROSS", Decimal("5.0000")),
            ("PF_EMP", "Provident Fund Employee (2.5% of Basic)", "ভবিষ্যৎ তহবিল (কর্মী)", SalaryComponent.ComponentType.DEDUCTION, "PCT_OF_BASIC", Decimal("2.5000")),
            ("STAMP", "Revenue Stamp (10 BDT)", "রাজস্ব স্ট্যাম্প", SalaryComponent.ComponentType.DEDUCTION, "FIXED_AMOUNT", Decimal("10.0000")),
        ]:
            SalaryComponent.objects.create(
                company=company, code=code, name=name, name_bn=name_bn, component_type=ctype, formula_type=formula, rate_or_amount=rate
            )

        for emp in employees[:10]:
            g = emp.gross_salary_bdt
            EmployeeSalaryStructure.objects.create(
                company=company,
                employee=emp,
                gross_amount=g,
                basic_amount=g * Decimal("0.50"),
                house_rent_amount=g * Decimal("0.25"),
                medical_amount=g * Decimal("0.10"),
                conveyance_amount=g * Decimal("0.10"),
                entertainment_amount=g * Decimal("0.05"),
                effective_from=emp.joining_date,
                change_reason="Initial structure assignment",
            )

        StatutoryScheme.objects.create(
            company=company,
            name="National Insurance / Social Security Scheme (NIS)",
            code="NIS",
            employee_rate_pct=Decimal("1.0000"),
            employer_rate_pct=Decimal("2.0000"),
            wage_ceiling_bdt=Decimal("100000.00"),
            wage_floor_bdt=Decimal("10000.00"),
            effective_from=date(2026, 1, 1),
            review_flag="Needs review by a local payroll/legal professional",
        )

        for order, thresh, rate in [
            (1, Decimal("350000.00"), Decimal("0.0000")),
            (2, Decimal("450000.00"), Decimal("5.0000")),
            (3, Decimal("850000.00"), Decimal("10.0000")),
            (4, Decimal("1350000.00"), Decimal("15.0000")),
        ]:
            TaxSlab.objects.create(
                company=company,
                income_year="2026-2027",
                slab_order=order,
                threshold_amount_bdt=thresh,
                tax_rate_pct=rate,
                review_flag="Needs review by a local HR/tax professional",
            )

        period = PayrollPeriod.objects.create(
            company=company,
            name="October 2026",
            year=2026,
            month=10,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
        )
        generate_company_payroll_run(
            company=company,
            period=period,
            run_number=f"PR-{company.code}-202610",
        )

        BonusRun.objects.create(
            company=company,
            name="Eid-ul-Fitr Festival Bonus 2026",
            bonus_type="FESTIVAL_EID",
            effective_date=date(2026, 3, 18),
            pct_of_basic=Decimal("100.0000"),
            total_amount_bdt=Decimal("825000.00"),
            status="PAID",
        )
        ExpenseClaim.objects.create(
            company=company,
            reference_no=f"EXP-{company.code}-0042",
            employee=employees[2],
            category="TRANSPORT",
            claim_date=today - timedelta(days=4),
            amount_bdt=Decimal("2450.00"),
            description="Client factory inspection travel & toll receipts",
            status=ExpenseClaim.Status.APPROVED,
        )
        loan = EmployeeLoan.objects.create(
            company=company,
            loan_number=f"LN-{company.code}-0019",
            employee=employees[2],
            loan_type="SALARY_ADVANCE",
            principal_bdt=Decimal("30000.00"),
            monthly_installment_bdt=Decimal("5000.00"),
            total_installments=6,
            disbursed_on=date(2026, 8, 1),
            status=EmployeeLoan.Status.APPROVED,
        )
        LoanLedger.objects.create(
            loan=loan,
            employee=employees[2],
            amount=Decimal("30000.00"),
            reason="Loan principal disbursement",
            source_type="DISBURSEMENT",
        )
        LoanLedger.objects.create(
            loan=loan,
            employee=employees[2],
            amount=Decimal("-5000.00"),
            reason="September 2026 payroll installment recovery",
            source_type="INSTALLMENT_RECOVERY",
        )

        # Phase 4 & 5: Talent Lifecycle, Relations, Assets, Exit & Helpdesk
        for d in depts[:3]:
            ManpowerPlan.objects.create(
                company=company,
                department=d,
                fiscal_year="2026-2027",
                approved_headcount=d.approved_headcount,
                current_headcount=d.employees.count(),
                open_vacancies=max(1, d.approved_headcount - d.employees.count()),
                annual_budget_bdt=Decimal("9600000.00"),
            )

        req = JobRequisition.objects.create(
            company=company,
            requisition_no=f"REQ-{company.code}-2026-08",
            department=depts[0],
            designation=designations[-1],
            title=f"Senior {designations[-1].title}",
            vacancies_count=2,
            min_salary_bdt=Decimal("50000.00"),
            max_salary_bdt=Decimal("80000.00"),
            status=JobRequisition.Status.APPROVED,
        )
        for stg, cand_en, cand_bn, score in [
            (JobApplicant.Stage.APPLIED, "Naimur Rahman", "নাইমুর রহমান", Decimal("79.00")),
            (JobApplicant.Stage.SCREENING, "Maliha Islam", "মালিহা ইসলাম", Decimal("84.50")),
            (JobApplicant.Stage.INTERVIEW, "Zahin Chowdhury", "জাহিন চৌধুরী", Decimal("91.00")),
            (JobApplicant.Stage.OFFERED, "Rifat Hossain", "রিফাত হোসেন", Decimal("94.00")),
        ]:
            app_obj = JobApplicant.objects.create(
                company=company,
                requisition=req,
                full_name=cand_en,
                full_name_bn=cand_bn,
                email=f"{cand_en.split()[0].lower()}@applicant.bd",
                phone="+8801755001122",
                stage=stg,
                evaluation_score=score,
            )
            if stg in (JobApplicant.Stage.INTERVIEW, JobApplicant.Stage.OFFERED):
                Interview.objects.create(
                    company=company,
                    applicant=app_obj,
                    interviewer=employees[0],
                    round_name="Technical & Culture Panel",
                    scheduled_at=timezone.now() - timedelta(days=3),
                    rating_score=Decimal("88.50"),
                    feedback="Strong domain expertise in Bangladesh labour compliance.",
                    status="COMPLETED",
                )
            if stg == JobApplicant.Stage.OFFERED:
                Offer.objects.create(
                    company=company,
                    applicant=app_obj,
                    offer_number=f"OFR-{company.code}-2026-01",
                    offered_gross_bdt=Decimal("68000.00"),
                    currency="BDT",
                    joining_date=today + timedelta(days=15),
                    status="ACCEPTED",
                )

        OnboardingChecklist.objects.create(
            company=company,
            employee=employees[-1],
            tasks_json=[
                {"task": "National ID (NID) & TIN Verification", "done": True},
                {"task": "Signed Appointment Letter & NDA", "done": True},
                {"task": "BRAC Bank Salary Account Opening", "done": True},
                {"task": "Laptop & Biometric Access Card Handover", "done": False},
            ],
            completion_pct=75,
        )
        ProbationReview.objects.create(
            company=company,
            employee=employees[-1],
            probation_end_date=today + timedelta(days=30),
            supervisor_rating=Decimal("4.45"),
            recommendation="CONFIRM",
            status=ProbationReview.Status.SUBMITTED,
        )
        ReviewCycle.objects.create(
            company=company,
            name="Annual Appraisal 2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            include_360_survey=True,
            status="ACTIVE",
        )
        Goal.objects.create(
            company=company,
            employee=employees[2],
            title="Maintain 99.5% Payroll & Statutory NIS Accuracy",
            weight_pct=Decimal("50.0000"),
            target_metric="Zero audit discrepancies across monthly runs",
            achievement_pct=Decimal("94.0000"),
            status="ON_TRACK",
        )
        appraisal_obj = PerformanceAppraisal.objects.create(
            company=company,
            employee=employees[2],
            review_cycle="Annual Appraisal 2026",
            stage=PerformanceAppraisal.Stage.CONFIRMED,
            self_score=Decimal("89.00"),
            manager_score=Decimal("92.50"),
            peer_360_score=Decimal("90.00"),
            final_rating="Outstanding (Band A)",
        )
        AppraisalSurvey.objects.create(
            company=company,
            appraisal=appraisal_obj,
            reviewer=employees[1],
            relationship_type="MANAGER",
            score=Decimal("92.50"),
            responses_json={
                "strengths": "Proactive ownership and cross-functional collaboration.",
                "improvements": "Delegate routine reporting tasks earlier.",
            },
        )
        CareerMovement.objects.create(
            company=company,
            employee=employees[1],
            movement_type="INCREMENT_AND_PROMOTION",
            new_designation=designations[0],
            previous_gross_bdt=employees[1].gross_salary_bdt - Decimal("8000.00"),
            revised_gross_bdt=employees[1].gross_salary_bdt,
            effective_from=date(2026, 7, 1),
            change_reason="Annual merit increment and leadership promotion",
        )
        prog = TrainingProgram.objects.create(
            company=company,
            title="Bangladesh Labour Compliance & Workplace Safety Certification",
            category="Compliance & EHS",
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=12),
            enrolled_count=16,
            cost_bdt=Decimal("45000.00"),
        )
        TrainingNomination.objects.create(
            company=company,
            program=prog,
            employee=employees[2],
            attended=True,
            assessment_score=Decimal("92.00"),
            certificate_issued=True,
        )
        GrievanceCase.objects.create(
            company=company,
            case_number=f"GRV-{company.code}-003",
            complainant=employees[4],
            assigned_handler=employees[0],
            category="Shift Roster Scheduling",
            is_confidential=True,
            status="RESOLVED",
            resolution_summary="Adjusted rotating shift schedule with mutual agreement.",
        )
        DisciplinaryCase.objects.create(
            company=company,
            case_number=f"DSC-{company.code}-001",
            employee=employees[5],
            incident_date=today - timedelta(days=20),
            allegation_summary="Repeated unnotified late arrival exceeding grace period",
            action_taken="VERBAL_COUNSELING_RECORDED",
            status="CLOSED",
        )
        asset = CompanyAsset.objects.create(
            company=company,
            asset_tag=f"AST-{company.code}-LPT-01",
            name="ThinkPad T14 Gen 4 Business Laptop",
            category="IT Equipment",
            serial_number=f"SN-{company.code}-99812",
            assigned_to=employees[2],
            value_bdt=Decimal("135000.00"),
        )
        AssetMovementLedger.objects.create(
            asset=asset,
            employee=employees[2],
            quantity=Decimal("1.0000"),
            reason="Assigned upon joining IT department",
            source_type="HANDOVER",
        )
        HealthSafetyRecord.objects.create(
            company=company,
            employee=employees[2],
            record_type="OCCUPATIONAL_HEALTH_CHECKUP",
            incident_or_checkup_date=today - timedelta(days=15),
            restricted_medical_notes="Blood pressure 118/78, vision 20/20, fit for all duties.",
            corrective_action="Ergonomic workstation check completed.",
        )
        resig = ResignationRequest.objects.create(
            company=company,
            employee=employees[-2],
            notice_given_date=today - timedelta(days=30),
            last_working_day=today + timedelta(days=30),
            notice_period_days=60,
            reason="Pursuing postgraduate studies abroad",
            exit_interview_completed=True,
            status=ResignationRequest.Status.APPROVED,
        )
        settlement = FinalSettlement.objects.create(
            company=company,
            employee=employees[-2],
            resignation=resig,
            unpaid_salary_bdt=employees[-2].gross_salary_bdt,
            leave_encashment_bdt=Decimal("18500.00"),
            pf_and_gratuity_bdt=Decimal("64000.00"),
            loan_recovery_bdt=Decimal("0.00"),
            asset_deduction_bdt=Decimal("0.00"),
            net_settlement_bdt=employees[-2].gross_salary_bdt + Decimal("82500.00"),
            all_departments_cleared=True,
            status="READY_FOR_PAYOUT",
        )
        for dept_label in ("IT & Assets", "Finance & Loans", "HR & Admin"):
            ClearanceItem.objects.create(
                company=company,
                settlement=settlement,
                department_name=dept_label,
                checklist_item=f"{dept_label} clearance & asset return",
                is_cleared=True,
                cleared_at=timezone.now(),
                remarks=f"{dept_label} handover verified.",
            )
        HelpdeskTicket.objects.create(
            company=company,
            ticket_number=f"TKT-{company.code}-2026-091",
            requester=employees[2],
            category="Salary & Tax Certificate",
            subject="Request for FY 2025-2026 Income Tax Deduction Certificate",
            priority="NORMAL",
            sla_hours=24,
            status="IN_PROGRESS",
        )

        ReportDefinition.objects.get_or_create(
            code="monthly-department-payroll-cost",
            defaults={
                "name": "Departmental Payroll, Overtime & NIS Statutory Summary",
                "module_number": 38,
                "category": "Payroll & Finance",
                "columns_config": ["department", "headcount", "gross_bdt", "pf_bdt", "nis_days", "net_bdt"],
                "default_filters": {"year": 2026, "month": 10},
                "schedule_cron": "0 8 1 * *",
            },
        )

    def _create_user(
        self,
        *,
        email: str,
        full_name: str,
        full_name_bn: str,
        tenant: Tenant,
        default_company: Company,
        allowed_companies: list[Company],
        mode: str,
        can_view_salary: bool,
        has_approval: bool,
    ) -> User:
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "full_name": full_name,
                "full_name_bn": full_name_bn,
                "tenant": tenant,
                "default_company": default_company,
                "experience_mode": mode,
                "can_view_salary": can_view_salary,
                "can_view_medical": can_view_salary,
                "has_approval_authority": has_approval,
                "is_active": True,
            },
        )
        user.set_password("Pass1234!")
        user.save()
        user.allowed_companies.set(allowed_companies)
        Notification.objects.get_or_create(
            recipient=user,
            title="Welcome to NICE HRIS (Light Glassmorphism Edition)",
            defaults={
                "message": f"Signed in to {tenant.name} ({default_company.name}). All 42 HRM modules are active.",
                "action_url": "/m/1/management-dashboard",
            },
        )
        return user

    def _create_roles_and_settings(self, tenant: Tenant, companies: list[Company]) -> None:
        TenantSetting.objects.update_or_create(
            tenant=tenant,
            defaults={
                "statutory_disclaimer": "Bangladesh default statutory config — needs review by a local HR/tax professional.",
                "pf_employee_rate_pct": Decimal("2.5000"),
                "pf_employer_rate_pct": Decimal("2.5000"),
                "revenue_stamp_bdt": Decimal("10.00"),
                "default_salary_breakdown_pct": {
                    "basic_pct_of_gross": 50.0,
                    "house_rent_pct_of_gross": 25.0,
                    "medical_pct_of_gross": 10.0,
                    "conveyance_pct_of_gross": 10.0,
                    "entertainment_pct_of_gross": 5.0,
                },
                "nis_days_rule": {
                    "include_present": True,
                    "include_paid_leave": True,
                    "include_paid_holidays": True,
                    "include_weekends": False,
                    "exclude_unpaid_leave": True,
                    "exclude_absent": True,
                    "note": "Needs review by a local payroll/legal professional",
                },
            },
        )

        self._ensure_seven_role_tabs_and_employee_roles(tenant)

        IntegrationConnectorConfig.objects.get_or_create(
            connector_code="csv_json",
            defaults={
                "name": "Generic CSV / JSON Import & Export Connector",
                "is_enabled": True,
                "schedule_cron": "0 2 * * *",
                "field_mapping": {
                    "emp_no": "employee_code",
                    "name": "full_name",
                    "punch_time": "timestamp",
                },
                "last_run_status": "READY",
            },
        )

        WebhookEndpoint.objects.get_or_create(
            name="ERP Payroll & Employee Sync Webhook",
            defaults={
                "target_url": f"https://hooks.erp-gateway.example.com/{tenant.slug}/hrm-events",
                "events": ["employee.created", "leave.approved", "payroll.run.approved"],
                "signing_secret": "whsec_demo_secret_key_for_hmac_sha256",
            },
        )
        OAuth2Client.objects.get_or_create(
            client_id=f"nhris_cid_{tenant.slug}_erp",
            defaults={
                "name": f"{tenant.name} ERP OAuth2 Service Client",
                "client_secret_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "scopes": ["employees:read", "payroll:read", "attendance:write"],
            },
        )

        AuditLog.objects.create(
            actor_email="system@nicehris.bd",
            action="TENANT_PROVISIONED",
            entity="Tenant",
            entity_id=str(tenant.id),
            new_values={
                "tenant": tenant.name,
                "multi_company_enabled": tenant.multi_company_enabled,
                "companies": [c.name for c in companies],
            },
        )

    def _ensure_seven_role_tabs_and_employee_roles(self, tenant: Tenant) -> None:
        """Seeds the 7 standard role tabs (Super Admin, Admin, Manager, Asst. Manager, Developer, Support, User)
        and links employees and users to their corresponding roles.
        """
        # Clean up legacy role codes if present so the 7 role tabs match the design cleanly
        Role.objects.filter(code__in=["hr-director", "line-manager", "employee-ess"]).delete()

        role_specs = [
            {
                "code": "super-admin",
                "name": "Super Admin",
                "badge_label": "System Superuser",
                "description": "Platform-wide superuser with unrestricted access to all 43 modules, tenants, and system settings",
                "display_order": 1,
                "salary": True,
                "medical": True,
                "approval": True,
                "all_modules": True,
                "modules": {},
            },
            {
                "code": "admin",
                "name": "Admin",
                "badge_label": "Workspace Admin",
                "description": "Workspace-wide settings, user invites, full 43-module access, and permission matrix administration",
                "display_order": 2,
                "salary": True,
                "medical": True,
                "approval": True,
                "all_modules": True,
                "modules": {},
            },
            {
                "code": "manager",
                "name": "Manager",
                "badge_label": "Department Lead",
                "description": "Departmental workforce planning, attendance & leave approvals, performance appraisals, and team reports",
                "display_order": 3,
                "salary": False,
                "medical": False,
                "approval": True,
                "all_modules": False,
                "modules": {
                    m: ["view", "create", "edit", "delete"]
                    for m in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 23, 24, 25, 28, 33, 34, 35, 36, 37, 38]
                },
            },
            {
                "code": "asst-manager",
                "name": "Asst. Manager",
                "badge_label": "Team Supervisor",
                "description": "Shift roster scheduling, daily attendance supervision, leave review, and onboarding coordination",
                "display_order": 4,
                "salary": False,
                "medical": False,
                "approval": True,
                "all_modules": False,
                "modules": {
                    m: ["view", "create", "edit"]
                    for m in [1, 3, 6, 8, 9, 10, 11, 12, 13, 25, 33, 34, 35, 36]
                },
            },
            {
                "code": "developer",
                "name": "Developer",
                "badge_label": "Engineering & IT",
                "description": "API keys, webhooks, biometric/ERP integrations, system settings, and self-service portal access",
                "display_order": 5,
                "salary": False,
                "medical": False,
                "approval": False,
                "all_modules": False,
                "modules": {
                    m: ["view", "create", "edit", "delete"]
                    for m in [1, 10, 11, 13, 28, 32, 34, 35, 36, 38, 41, 42]
                },
            },
            {
                "code": "support",
                "name": "Support",
                "badge_label": "Helpdesk & Ops",
                "description": "HR helpdesk ticket resolution, asset handover, policy documents, announcements, and employee directory",
                "display_order": 6,
                "salary": False,
                "medical": False,
                "approval": False,
                "all_modules": False,
                "modules": {
                    m: ["view", "create", "edit", "delete"]
                    for m in [1, 2, 3, 6, 8, 10, 11, 28, 29, 32, 34, 35, 36]
                },
            },
            {
                "code": "user",
                "name": "User",
                "badge_label": "Standard Employee",
                "description": "Employee Self-Service portal, attendance check-in/out, leave applications, payslips, and helpdesk requests",
                "display_order": 7,
                "salary": False,
                "medical": False,
                "approval": False,
                "all_modules": False,
                "modules": {
                    m: ["view", "create"]
                    for m in [1, 8, 10, 11, 12, 13, 17, 18, 22, 32, 34, 35, 36]
                },
            },
        ]

        roles_by_code: dict[str, Role] = {}
        for spec in role_specs:
            role, _ = Role.objects.update_or_create(
                code=spec["code"],
                defaults={
                    "name": spec["name"],
                    "badge_label": spec["badge_label"],
                    "description": spec["description"],
                    "display_order": spec["display_order"],
                    "is_system_role": True,
                    "can_view_confidential_salary": spec["salary"],
                    "can_view_confidential_medical": spec["medical"],
                    "has_approval_authority": spec["approval"],
                },
            )
            roles_by_code[spec["code"]] = role
            for mod_num in range(1, 44):
                if spec["all_modules"]:
                    acts = ["view", "create", "edit", "delete"]
                else:
                    acts = spec["modules"].get(mod_num, [])
                RolePermission.objects.update_or_create(
                    role=role,
                    module_number=mod_num,
                    defaults={"actions": acts},
                )

        # Ensure demo logins exist for Asst. Manager, Developer, and Support in Jamuna Group so all 7 roles are testable
        if tenant.slug == "jamuna-group":
            extra_demo_specs = [
                ("JTSL-0004", "asst.manager@jamunagroup.bd", User.ExperienceMode.MANAGER, "asst-manager"),
                ("JTSL-0005", "developer@jamunagroup.bd", User.ExperienceMode.EMPLOYEE, "developer"),
                ("JTSL-0006", "support@jamunagroup.bd", User.ExperienceMode.EMPLOYEE, "support"),
            ]
            for emp_code, demo_email, exp_mode, _role_key in extra_demo_specs:
                emp_obj = Employee.objects.filter(employee_code=emp_code).first()
                if emp_obj:
                    demo_u, created_u = User.objects.update_or_create(
                        email=demo_email,
                        defaults={
                            "full_name": emp_obj.full_name,
                            "full_name_bn": emp_obj.full_name_bn,
                            "tenant": tenant,
                            "default_company": emp_obj.company,
                            "experience_mode": exp_mode,
                            "can_view_salary": False,
                            "can_view_medical": False,
                            "has_approval_authority": exp_mode in (User.ExperienceMode.ADMIN, User.ExperienceMode.MANAGER),
                            "is_active": True,
                        },
                    )
                    if created_u:
                        demo_u.set_password("Pass1234!")
                        demo_u.save()
                    demo_u.allowed_companies.set(list(Company.objects.all()))
                    if emp_obj.user_id != demo_u.id:
                        emp_obj.user = demo_u
                        Employee.unscoped_objects.filter(pk=emp_obj.pk).update(user=demo_u)

        # Assign roles to existing employees and users in this tenant
        all_emps = list(Employee.objects.select_related("user").all())
        for idx, emp in enumerate(all_emps):
            u_email = (emp.user.email.lower() if emp.user and emp.user.email else "")
            if u_email.startswith("hr.admin@") or u_email.startswith("group.hr@"):
                assigned_role = roles_by_code["admin"]
            elif u_email.startswith("manager@") or u_email.startswith("line.manager@"):
                assigned_role = roles_by_code["manager"]
            elif u_email.startswith("asst.manager@"):
                assigned_role = roles_by_code["asst-manager"]
            elif u_email.startswith("developer@"):
                assigned_role = roles_by_code["developer"]
            elif u_email.startswith("support@"):
                assigned_role = roles_by_code["support"]
            elif u_email.startswith("employee@"):
                assigned_role = roles_by_code["user"]
            elif idx == 0:
                assigned_role = roles_by_code["admin"]
            elif idx == 1:
                assigned_role = roles_by_code["manager"]
            elif idx == 2:
                assigned_role = roles_by_code["user"]
            elif idx % 6 == 0:
                assigned_role = roles_by_code["asst-manager"]
            elif idx % 5 == 0:
                assigned_role = roles_by_code["developer"]
            elif idx % 4 == 0:
                assigned_role = roles_by_code["support"]
            else:
                assigned_role = roles_by_code["user"]

            if emp.role_id != assigned_role.id:
                emp.role = assigned_role
                Employee.unscoped_objects.filter(pk=emp.pk).update(role=assigned_role)

            if emp.user_id:
                DataScope.unscoped_objects.filter(user_id=emp.user_id).exclude(role=assigned_role).delete()
                DataScope.unscoped_objects.update_or_create(
                    tenant=tenant,
                    user_id=emp.user_id,
                    role=assigned_role,
                    defaults={
                        "scope_type": DataScope.ScopeType.ALL_TENANT,
                        "company_ids": [str(emp.company_id)],
                    },
                )
