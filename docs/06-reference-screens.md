# 06. Reference Screens (UX patterns from the current Odoo-based system)

Source: the owner's existing HRM deck. We are **not** using Odoo; we rebuild these capabilities natively and improve them in the glass UI. Use as functional reference, not pixel reference.

## Employee and organization
- **Employee form:** header card with photo, name, job title; fields: work email/phone/mobile, joining date, tags (e.g. Permanent), department, job position, manager, coach; smart buttons: Documents, "In contract since", Goals, Org chart; record pager (81/168).
- **Employee dashboard:** filters (date range, department, job position, company); KPI tiles: Employees, New employees, Departures, Turnover rate, Avg contract duration, Contracts; charts: employees variation by month (bar), turnover by month (area); tables: Top departments (hires, employees), Top paid job positions (contracts, avg salary).
- **Employee analysis:** headcount over time by department, job position, contract type, status; measures, chart-type switch, pivot view, export.

## Shift, roster, attendance
- **Shift batch:** batch name, shift name, period, company, employee list with per-employee effective from/to; "Assign employee" action.
- **Attendance list:** employee, check-in, check-out, worked time, extra hours, overtime status (Approved) with Approve/Refuse actions. Sources: biometric/RFID device sync (ZKTeco and Hikvision-type), manual, mobile.
- **Monthly attendance summary:** stepper Draft > Confirmed > Approved; Generate and Confirm actions; columns: Employee, Department, Salary days, Present days, Weekend, Absent days, Absent deduction, Late days, Holidays, Paid holidays, Unpaid holidays, Late deduction, plus an **NIS Days** column (slide 9, last column): the number of insurable days in the period for National Insurance Scheme / social security calculations (see `02`, Statutory social security). Feeds payroll.

## Leave
- **All time off:** kanban cards (employee, type, date range, days, status Approved/Refused/To Approve) with inline Approve/Refuse; left filters by Status and Department; list, calendar, timeline views.
- **Time off analysis:** pivot by employee and leave type with Left / Taken / Planned measures; period filter.
- Leave types seen: Annual, Short (hour-based), Casual.

## Payroll
- **Contract list:** employee, contract ref, department, job title, start/end, contract type (Probation, Permanent), yearly cost, working schedule (Shift-1/2/Standard), status (New, Running).
- **Payroll dashboard:** warnings: employees with running contracts missing from open batches, without bank account, without ID number, without running contract, new contracts; payroll batches list with status; Employer cost chart (annual/monthly toggle); Employee trends chart.
- **Payslip form:** stepper Draft > Done > Paid; actions Create payment report, Refund, Cancel, Print; header (contract, batch, structure, type, period); tabs Worked days and inputs / Salary computation / Other info; lines with category, quantity, rate %, amount, total.
- **Typical BD salary structure:** Basic 50%, House rent 25%, Medical 10%, Conveyance 10%, Entertainment 5% (of gross), PF company 2.5%, PF employee 2.5%, AIT (tax) deduction, salary advance deduction, revenue stamp (10 BDT), Net salary. Make every percentage configurable.
- **Payslip PDF:** employee info (name, ID, email, job, department, marital status), contract info (wage, pay period, contract start, type, weekly hours), earnings table (overtime hours, attendance days), salary lines, net salary, "To pay on <bank account> of <employee>".
- **Monthly salary sheet:** grouped by department; columns SN, Employee, A/C no, Designation, DOJ, Loan balance, Basic, House rent, Medical, Conveyance, Entertainment, Taxable salary, Total salary, AIT, Stamp, Other deduction, Net salary, Signature; totals; total **in words** ("One Lakh, Sixty-Five Thousand ... Taka"); footer signature blocks: Prepared / Checked / Authorized / Approved.
- **Payroll analysis:** pivot by department with # payslips, net wage, gross wage, paid and unpaid leave days.

## Performance
- **Appraisal form:** stepper To Confirm > Confirmed > Done; Mark as Done, Ask Feedback; manager, appraisal date, next date, template, final rating; tabs Appraisal / Skills / Private note; employee feedback and manager feedback panels with visibility toggles; smart buttons Feedbacks, Goals, Meeting.
- **Appraisal survey and 360 feedback:** customizable questionnaires (single/multi choice, matrix, text); sections About you / About us / Conclusion; registered and participation counters; results view with success rate, average score, pie charts; **appraisal analysis** by month and department.

## Mobile app (employee)
- Home: greeting, Today's status (shift time, check-in pending, location), leave balance (total/used/available + utilization bar), team dashboard (present/on leave/absent), announcements, employee info (ID, department, designation).
- Attendance: tabs Check In/Out, Records, Manual Attendance; big check-in button, current address, geofence badge ("Inside office area"), today's activity; records list with date-range filter, status badges (Late, Present), check-in/out times, "Within geofence" badge.
- Leaves: Request Leave button; tabs Own / Pending (count) / Approved / Rejected / All; filters Date range and State; cards with reference number (LR-2026-154).
- Payroll: tabs Payroll / PF; month and year filters; cards with period, status (paid), gross, deductions, net, paid date, Download PDF.
- Bottom nav: Home, Attendance, Leaves, Directory, More.

## Note
The source deck also contained CRM and Transport screens. The owner confirmed these are unrelated to this product (they came from the file name). Ignore them completely.
