import React, { useState } from "react";
import {
  ApprovalInboxCard,
  Avatar,
  Button,
  CalendarGrid,
  ConfirmDialog,
  DataTable,
  DatePicker,
  Drawer,
  EmptyState,
  FileUploader,
  GlassCard,
  GlassPanel,
  Input,
  KanbanBoard,
  KPITile,
  Modal,
  OrgChartNode,
  PivotTable,
  Select,
  SignatureBlock,
  Skeleton,
  StatusPill,
  StatutoryDisclaimerBanner,
  Stepper,
  Tabs,
  Timeline,
} from "../components/glass";
import { Sparkles, Users, ShieldCheck, Wallet } from "lucide-react";

export const DesignSystemPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("tokens");
  const [modalOpen, setModalOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="h-full flex flex-col gap-3 overflow-y-auto pr-0.5">
      <GlassCard className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <h1 className="text-xl font-bold text-ink">
              Light Glassmorphism Design System (/design-system)
            </h1>
          </div>
          <p className="text-xs text-ink-2 mt-1">
            Official token palette, translucent surfaces, strong-glass data grids, steppers, kanban, org nodes & WCAG AA fallbacks (docs/03-design-system.md).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => setModalOpen(true)}>
            Preview Glass Modal
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setDrawerOpen(true)}>
            Preview Glass Drawer
          </Button>
        </div>
      </GlassCard>

      <StatutoryDisclaimerBanner />

      <Tabs
        tabs={[
          { id: "tokens", label: "Surfaces & Buttons" },
          { id: "inputs", label: "Inputs, Badges & Steppers" },
          { id: "data", label: "Strong-Glass Tables & Kanban" },
          { id: "states", label: "Org Chart, Timeline & States" },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {activeTab === "tokens" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <KPITile
              label="Primary Indigo (#4F46E5)"
              value="৳ 1,65,000.00"
              subtitle="Lakh-grouped BDT currency"
              badge="APPROVED"
              icon={<Wallet className="w-4 h-4" />}
            />
            <KPITile
              label="Sky Accent (#0EA5E9)"
              value="97.4%"
              subtitle="Attendance compliance"
              badge="PRESENT"
              icon={<Users className="w-4 h-4" />}
            />
            <KPITile
              label="Strong Glass (>= 0.80)"
              value="WCAG AA"
              subtitle="4.5:1 minimum contrast"
              badge="ACTIVE"
              icon={<ShieldCheck className="w-4 h-4" />}
            />
            <KPITile
              label="NIS Insurable Days"
              value="26 Days"
              subtitle="Social Security Basis"
              badge="CONFIRMED"
            />
          </div>

          <GlassPanel className="space-y-4">
            <h2 className="text-sm font-bold text-ink">Button Variants & Interactive States</h2>
            <div className="flex flex-wrap items-center gap-3">
              <Button variant="primary">Primary Action</Button>
              <Button variant="secondary">Secondary Sky</Button>
              <Button variant="ghost">Ghost Glass</Button>
              <Button variant="danger">Danger / Reject</Button>
              <Button variant="primary" disabled>
                Disabled State
              </Button>
            </div>
          </GlassPanel>
        </div>
      )}

      {activeTab === "inputs" && (
        <GlassPanel className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input label="Employee Name (English)" placeholder="e.g. Nusrat Jahan" defaultValue="Nusrat Jahan" />
            <Input label="কর্মীর নাম (বাংলা ইউনিকোড)" placeholder="নুসরাত জাহান" defaultValue="নুসরাত জাহান" />
            <DatePicker label="Effective From Date" defaultValue="2026-10-01" />
            <Select
              label="Weekly Off Configuration"
              options={[
                { value: "FRI", label: "Friday Only (Bangladesh Default)" },
                { value: "FRI_SAT", label: "Friday & Saturday" },
              ]}
            />
            <Input
              label="Error Validation State"
              defaultValue="http://127.0.0.1/hook"
              error="Webhook URLs must use HTTPS and cannot target loopback IPs."
            />
          </div>

          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase text-ink-2">Status Pills (Icon + Text for Colour-Blind Safety)</h3>
            <div className="flex flex-wrap gap-2">
              <StatusPill status="APPROVED" />
              <StatusPill status="CONFIRMED" />
              <StatusPill status="PENDING" />
              <StatusPill status="LATE" />
              <StatusPill status="REJECTED" />
              <StatusPill status="ABSENT" />
              <StatusPill status="PROBATION" />
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase text-ink-2">Workflow Status Stepper</h3>
            <Stepper steps={["Draft", "Confirmed", "Approved", "Locked"]} currentStep="Confirmed" />
          </div>
        </GlassPanel>
      )}

      {activeTab === "data" && (
        <div className="space-y-6">
          <DataTable
            columns={[
              { key: "code", header: "Code" },
              { key: "name", header: "Component" },
              { key: "formula", header: "Formula (BD Standard)" },
              {
                key: "status",
                header: "State",
                render: (r) => <StatusPill status={r.status} />,
              },
            ]}
            data={[
              { id: "1", code: "BASIC", name: "Basic Salary", formula: "50% of Gross", status: "ACTIVE" },
              { id: "2", code: "HRA", name: "House Rent Allowance", formula: "25% of Gross", status: "ACTIVE" },
              { id: "3", code: "MED", name: "Medical Allowance", formula: "10% of Gross", status: "ACTIVE" },
              { id: "4", code: "CONV", name: "Conveyance Allowance", formula: "10% of Gross", status: "ACTIVE" },
              { id: "5", code: "ENT", name: "Entertainment Allowance", formula: "5% of Gross", status: "ACTIVE" },
            ]}
          />

          <KanbanBoard
            columns={[
              {
                id: "applied",
                title: "Applied",
                cards: [{ id: "c1", title: "Naimur Rahman", subtitle: "Senior Engineer", badge: "APPLIED", meta: "Score 79%" }],
              },
              {
                id: "screening",
                title: "Screening",
                cards: [{ id: "c2", title: "Maliha Islam", subtitle: "Senior Engineer", badge: "SCREENING", meta: "Score 84.5%" }],
              },
              {
                id: "interview",
                title: "Interview",
                cards: [{ id: "c3", title: "Zahin Chowdhury", subtitle: "Senior Engineer", badge: "INTERVIEW", meta: "Score 91%" }],
              },
              {
                id: "offered",
                title: "Offer Extended",
                cards: [{ id: "c4", title: "Rifat Hossain", subtitle: "Senior Engineer", badge: "OFFERED", meta: "৳ 75,000" }],
              },
            ]}
          />

          <PivotTable
            title="Department × Leave Type Pivot Matrix"
            rowLabel="Department"
            columns={["Casual Leave", "Sick Leave", "Earned Leave", "Total Days"]}
            rows={[
              { rowKey: "Human Resources & Admin", values: { "Casual Leave": 6, "Sick Leave": 4, "Earned Leave": 10, "Total Days": 20 } },
              { rowKey: "Garment Production & QA", values: { "Casual Leave": 14, "Sick Leave": 9, "Earned Leave": 18, "Total Days": 41 } },
            ]}
          />

          <CalendarGrid
            monthLabel="October 2026 Leave & Holiday Calendar"
            events={[
              { day: 4, title: "Casual Leave (Sabbir)", status: "APPROVED" },
              { day: 16, title: "Earned Leave (Nusrat)", status: "APPROVED" },
            ]}
          />

          <ApprovalInboxCard
            title="Leave Request LR-PAD-2026-154"
            requester="Sabbir Ahmed"
            moduleLabel="Module 10 • Leave"
            stepText="Step 1 of 2 (Line Manager)"
            status="PENDING"
            onApprove={() => {}}
            onReject={() => {}}
          />
          <ConfirmDialog
            open={false}
            title="Confirm Lock"
            description="Locking a payroll run is irreversible."
            onConfirm={() => {}}
            onCancel={() => {}}
          />
        </div>
      )}

      {activeTab === "states" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <GlassCard className="space-y-3">
              <h3 className="text-xs font-bold uppercase text-ink-2">Effective-Dated Org Chart Node & Avatar</h3>
              <div className="flex items-center gap-4">
                <Avatar name="Farhana Rahman" size="lg" />
                <OrgChartNode
                  name="Farhana Rahman"
                  nameBn="ফারহানা রহমান"
                  title="Group HR Director"
                  department="People & Culture"
                  code="JTSL-0001"
                />
              </div>
              <FileUploader />
            </GlassCard>

            <GlassCard className="space-y-3">
              <h3 className="text-xs font-bold uppercase text-ink-2">Audit & Workflow History Timeline</h3>
              <Timeline
                items={[
                  {
                    title: "Monthly Attendance Summary Approved",
                    subtitle: "NIS Days verified (26 days) for October 2026 payroll period.",
                    timestamp: "Today, 10:15 AM",
                  },
                  {
                    title: "Leave Application LR-2026-154 Submitted",
                    subtitle: "Routed to Line Manager via Workflow Engine (Module 37).",
                    timestamp: "Yesterday, 04:40 PM",
                  },
                ]}
              />
            </GlassCard>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <EmptyState
              title="Empty State Component"
              description="Displayed when a filter or module query returns zero records."
              actionLabel="Reset Filters"
              onAction={() => {}}
            />
            <GlassCard className="space-y-3">
              <h3 className="text-xs font-bold uppercase text-ink-2">Loading Skeletons</h3>
              <Skeleton className="h-8 w-1/2" />
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </GlassCard>
          </div>

          <GlassPanel>
            <h3 className="text-xs font-bold uppercase text-ink-2">Salary Sheet Signature Footer Block</h3>
            <SignatureBlock />
          </GlassPanel>
        </div>
      )}

      <Modal open={modalOpen} title="Strong-Glass Modal Preview" onClose={() => setModalOpen(false)}>
        <p className="text-sm text-ink-2 mb-4">
          Modals use strong glass (<code>rgba(255,255,255,0.84)</code>) to guarantee crisp contrast over the pastel gradient background.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setModalOpen(false)}>
            Close
          </Button>
          <Button onClick={() => setModalOpen(false)}>Confirm Action</Button>
        </div>
      </Modal>

      <Drawer open={drawerOpen} title="Create / Edit Record Drawer" onClose={() => setDrawerOpen(false)}>
        <div className="space-y-4">
          <Input label="Record Title" defaultValue="Sample HR Record" />
          <Input label="বাংলা শিরোনাম" defaultValue="নমুনা এইচআর রেকর্ড" />
          <Button className="w-full" onClick={() => setDrawerOpen(false)}>
            Save Changes
          </Button>
        </div>
      </Drawer>
    </div>
  );
};
