import React, { useState } from "react";
import {
  CheckCircle2,
  ChevronRight,
  Clock,
  FileUp,
  Inbox,
  Search,
  Sparkles,
  X,
  AlertTriangle,
  XCircle,
} from "lucide-react";

/**
 * 1. GlassCard (Light Glass surface for shell, dashboard cards, side panels)
 */
export const GlassCard: React.FC<{
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
}> = ({ children, className = "", hover = false, onClick }) => (
  <div
    onClick={onClick}
    className={`glass p-3.5 ${hover ? "glass-hover cursor-pointer" : ""} ${className}`}
  >
    {children}
  </div>
);

/**
 * 2. GlassPanel (Strong Glass >= 0.80 alpha for dense tables, forms, payroll grids, modals)
 */
export const GlassPanel: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = "" }) => (
  <div className={`glass-strong p-4 ${className}`}>{children}</div>
);

/**
 * 3. Button (primary, secondary, ghost, danger)
 */
export const Button: React.FC<
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "primary" | "secondary" | "ghost" | "danger";
    size?: "sm" | "md" | "lg";
  }
> = ({
  children,
  variant = "primary",
  size = "md",
  className = "",
  ...props
}) => {
  const variants: Record<string, string> = {
    primary:
      "bg-primary text-white hover:bg-indigo-700 shadow-sm focus-visible:ring-2 focus-visible:ring-indigo-500",
    secondary:
      "bg-secondary text-white hover:bg-sky-600 shadow-sm focus-visible:ring-2 focus-visible:ring-sky-500",
    ghost:
      "bg-white/60 text-ink hover:bg-white/90 border border-white/80 focus-visible:ring-2 focus-visible:ring-indigo-400",
    danger:
      "bg-danger text-white hover:bg-red-600 shadow-sm focus-visible:ring-2 focus-visible:ring-red-500",
  };
  const sizes: Record<string, string> = {
    sm: "px-3 py-1.5 text-xs min-h-[34px]",
    md: "px-4 py-2 text-sm min-h-[40px]",
    lg: "px-5 py-2.5 text-base min-h-[44px]",
  };
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 font-medium rounded-control transition-all disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

/**
 * 4. Input & DatePicker
 */
export const Input: React.FC<
  React.InputHTMLAttributes<HTMLInputElement> & {
    label?: string;
    error?: string;
  }
> = ({ label, error, className = "", id, ...props }) => {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-xs font-semibold text-ink-2">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`w-full px-3.5 py-2 text-sm bg-white/85 border border-slate-200/90 rounded-control text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary ${className}`}
        {...props}
      />
      {error && <span className="text-xs text-danger font-medium">{error}</span>}
    </div>
  );
};

export const DatePicker: React.FC<
  React.InputHTMLAttributes<HTMLInputElement> & { label?: string }
> = (props) => <Input type="date" {...props} />;

/**
 * 5. Select
 */
export const Select: React.FC<
  React.SelectHTMLAttributes<HTMLSelectElement> & {
    label?: string;
    options: { value: string; label: string }[];
  }
> = ({ label, options, className = "", id, ...props }) => {
  const selectId = id || label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={selectId} className="text-xs font-semibold text-ink-2">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`px-3.5 py-2 text-sm bg-white/85 border border-slate-200/90 rounded-control text-ink focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary ${className}`}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
};

/**
 * 6. StatusPill / Badge (Never conveys status by colour alone — includes icon + text)
 */
export const StatusPill: React.FC<{
  status: string;
  tone?: "success" | "warning" | "danger" | "info" | "neutral";
}> = ({ status, tone }) => {
  const s = (status || "").toUpperCase();
  const resolvedTone =
    tone ||
    (["APPROVED", "ACTIVE", "PRESENT", "PAID", "DONE", "PERMANENT", "HIRED", "DELIVERED", "CONFIRMED", "READY", "RECONCILED"].includes(s)
      ? "success"
      : ["PENDING", "DRAFT", "PROBATION", "LATE", "IN_PROGRESS", "IN_REVIEW", "SUBMITTED", "TO_CONFIRM", "SCREENING", "INTERVIEW", "TRIAL"].includes(s)
      ? "warning"
      : ["REJECTED", "ABSENT", "FAILED", "SUSPENDED", "SEPARATED"].includes(s)
      ? "danger"
      : "info");

  const styles: Record<string, string> = {
    success: "bg-emerald-500/15 text-emerald-800 border-emerald-500/30",
    warning: "bg-amber-500/15 text-amber-800 border-amber-500/30",
    danger: "bg-red-500/15 text-red-800 border-red-500/30",
    info: "bg-indigo-500/15 text-indigo-800 border-indigo-500/30",
    neutral: "bg-slate-500/15 text-slate-700 border-slate-400/30",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-semibold border rounded-pill ${styles[resolvedTone]}`}
    >
      {resolvedTone === "success" && <CheckCircle2 className="w-3.5 h-3.5" />}
      {resolvedTone === "warning" && <Clock className="w-3.5 h-3.5" />}
      {resolvedTone === "danger" && <XCircle className="w-3.5 h-3.5" />}
      {resolvedTone === "info" && <Sparkles className="w-3.5 h-3.5" />}
      <span>{status}</span>
    </span>
  );
};

/**
 * 7. Avatar
 */
export const Avatar: React.FC<{ name: string; size?: "sm" | "md" | "lg" }> = ({
  name,
  size = "md",
}) => {
  const initials = (name || "HR")
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  const dims = {
    sm: "w-8 h-8 text-xs",
    md: "w-10 h-10 text-sm",
    lg: "w-14 h-14 text-lg",
  }[size];
  return (
    <div
      className={`${dims} rounded-full bg-gradient-to-br from-indigo-600 to-sky-500 text-white font-bold flex items-center justify-center shadow-sm shrink-0`}
    >
      {initials}
    </div>
  );
};

/**
 * 8. KPITile
 */
export const KPITile: React.FC<{
  label: string;
  value: string | number;
  subtitle?: string;
  badge?: string;
  icon?: React.ReactNode;
}> = ({ label, value, subtitle, badge, icon }) => (
  <GlassCard hover className="flex flex-col justify-between gap-1 py-2.5 px-3.5">
    <div className="flex items-center justify-between">
      <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-2">
        {label}
      </span>
      {icon && (
        <div className="p-1.5 rounded-lg bg-indigo-500/10 text-primary">{icon}</div>
      )}
    </div>
    <div className="text-xl font-bold text-ink tracking-tight leading-tight">{value}</div>
    <div className="flex items-center justify-between text-[11px] text-muted">
      <span className="truncate">{subtitle}</span>
      {badge && <StatusPill status={badge} />}
    </div>
  </GlassCard>
);

/**
 * 9. Stepper (e.g. Draft > Confirmed > Approved)
 */
export const Stepper: React.FC<{
  steps: string[];
  currentStep: string;
}> = ({ steps, currentStep }) => {
  const currentIdx = Math.max(
    0,
    steps.findIndex((s) => s.toUpperCase() === (currentStep || "").toUpperCase())
  );
  return (
    <div className="flex items-center flex-wrap gap-2">
      {steps.map((step, idx) => {
        const isDone = idx < currentIdx;
        const isCurrent = idx === currentIdx;
        return (
          <React.Fragment key={step}>
            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-pill text-xs font-semibold border transition-all ${
                isCurrent
                  ? "bg-primary text-white border-primary shadow-sm"
                  : isDone
                  ? "bg-emerald-500/15 text-emerald-800 border-emerald-500/30"
                  : "bg-white/60 text-muted border-slate-200"
              }`}
            >
              <span className="w-4 h-4 rounded-full bg-black/10 flex items-center justify-center text-[10px]">
                {idx + 1}
              </span>
              <span>{step}</span>
            </div>
            {idx < steps.length - 1 && (
              <ChevronRight className="w-4 h-4 text-muted" />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

/**
 * 10. Tabs
 */
export const Tabs: React.FC<{
  tabs: { id: string; label: string; count?: number }[];
  activeTab: string;
  onChange: (id: string) => void;
}> = ({ tabs, activeTab, onChange }) => (
  <div className="flex items-center gap-1.5 p-1 bg-white/50 border border-white/80 rounded-control overflow-x-auto">
    {tabs.map((tab) => {
      const active = tab.id === activeTab;
      return (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-3.5 py-1.5 rounded-[10px] text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
            active
              ? "bg-primary text-white shadow-sm"
              : "text-ink-2 hover:bg-white/70"
          }`}
        >
          <span>{tab.label}</span>
          {tab.count !== undefined && (
            <span
              className={`px-1.5 py-0.2 rounded-pill text-[10px] ${
                active ? "bg-white/20 text-white" : "bg-slate-200/80 text-ink-2"
              }`}
            >
              {tab.count}
            </span>
          )}
        </button>
      );
    })}
  </div>
);

/**
 * 11. Dense Data Table (Sits on strong glass, never blurs individual rows per docs/03)
 */
export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  searchPlaceholder = "Filter records...",
  emptyMessage = "No matching records found.",
}: {
  columns: {
    key: string;
    header: string;
    render?: (row: T) => React.ReactNode;
  }[];
  data: T[];
  searchPlaceholder?: string;
  emptyMessage?: string;
}) {
  const [query, setQuery] = useState("");
  const filtered = data.filter((row) =>
    !query
      ? true
      : Object.values(row)
          .join(" ")
          .toLowerCase()
          .includes(query.toLowerCase())
  );

  return (
    <GlassPanel className="p-0 overflow-hidden flex flex-col">
      <div className="px-3.5 py-2 border-b border-slate-200/70 flex flex-wrap items-center justify-between gap-2 bg-white/40 shrink-0">
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-muted absolute left-2.5 top-2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full pl-8 pr-3 py-1 text-xs bg-white/90 border border-slate-200 rounded-control focus:outline-none focus:ring-2 focus:ring-primary/40"
          />
        </div>
        <span className="text-[11px] font-medium text-ink-2">
          Showing <strong>{filtered.length}</strong> of {data.length} records
        </span>
      </div>
      <div className="overflow-auto max-h-[calc(100dvh-19.5rem)]">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 z-10 bg-slate-100/95 backdrop-blur-sm">
            <tr className="border-b border-slate-200/80 text-[11px] font-bold uppercase tracking-wider text-ink-2">
              {columns.map((col) => (
                <th key={col.key} className="py-2 px-3.5">
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200/60 text-xs bg-white/80">
            {filtered.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="py-6 text-center text-muted text-xs"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              filtered.map((row, rIdx) => (
                <tr
                  key={row.id || rIdx}
                  className="hover:bg-indigo-50/50 transition-colors"
                >
                  {columns.map((col) => (
                    <td key={col.key} className="py-2 px-3.5 text-ink">
                      {col.render ? col.render(row) : String(row[col.key] ?? "—")}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </GlassPanel>
  );
}

/**
 * 12. Modal & ConfirmDialog & Drawer
 */
export const Modal: React.FC<{
  open: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}> = ({ open, title, onClose, children }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40">
      <GlassPanel className="w-full max-w-lg animate-in fade-in zoom-in-95">
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-200/80">
          <h3 className="text-base font-bold text-ink">{title}</h3>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-200/60 text-ink-2"
            aria-label="Close modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        {children}
      </GlassPanel>
    </div>
  );
};

export const Drawer: React.FC<{
  open: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}> = ({ open, title, onClose, children }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/30">
      <GlassPanel className="w-full max-w-md h-full rounded-none rounded-l-card overflow-y-auto">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-200/80">
          <h3 className="text-base font-bold text-ink">{title}</h3>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-200/60 text-ink-2"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        {children}
      </GlassPanel>
    </div>
  );
};

/**
 * 13. EmptyState & Skeleton
 */
export const EmptyState: React.FC<{
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}> = ({ title, description, actionLabel, onAction }) => (
  <GlassCard className="flex flex-col items-center justify-center text-center py-10 gap-3">
    <div className="p-3 rounded-full bg-indigo-500/10 text-primary">
      <Inbox className="w-6 h-6" />
    </div>
    <h4 className="text-base font-bold text-ink">{title}</h4>
    <p className="text-xs text-muted max-w-md">{description}</p>
    {actionLabel && onAction && (
      <Button size="sm" onClick={onAction}>
        {actionLabel}
      </Button>
    )}
  </GlassCard>
);

export const Skeleton: React.FC<{ className?: string }> = ({
  className = "h-12 w-full",
}) => (
  <div
    className={`animate-pulse bg-white/60 border border-white/80 rounded-control ${className}`}
  />
);

/**
 * 14. Timeline
 */
export const Timeline: React.FC<{
  items: { title: string; subtitle: string; timestamp: string; status?: string }[];
}> = ({ items }) => (
  <div className="space-y-4">
    {items.map((item, idx) => (
      <div key={idx} className="flex items-start gap-3">
        <div className="w-2.5 h-2.5 rounded-full bg-primary mt-1.5 shrink-0 ring-4 ring-indigo-500/15" />
        <div className="flex-1 bg-white/70 border border-white/80 rounded-control p-3">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-bold text-ink">{item.title}</span>
            <span className="text-[11px] text-muted">{item.timestamp}</span>
          </div>
          <p className="text-xs text-ink-2 mt-1">{item.subtitle}</p>
        </div>
      </div>
    ))}
  </div>
);

/**
 * 15. KanbanBoard (Used for Recruitment Pipeline & Leave Requests per docs/06)
 */
export const KanbanBoard: React.FC<{
  columns: {
    id: string;
    title: string;
    cards: {
      id: string;
      title: string;
      subtitle: string;
      badge: string;
      meta?: string;
    }[];
  }[];
}> = ({ columns }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    {columns.map((col) => (
      <GlassCard key={col.id} className="p-3.5 flex flex-col gap-3">
        <div className="flex items-center justify-between border-b border-white/70 pb-2">
          <span className="text-xs font-bold uppercase tracking-wider text-ink-2">
            {col.title}
          </span>
          <span className="px-2 py-0.5 text-xs font-bold rounded-pill bg-indigo-500/10 text-primary">
            {col.cards.length}
          </span>
        </div>
        <div className="space-y-2.5">
          {col.cards.map((card) => (
            <div
              key={card.id}
              className="p-3 rounded-control bg-white/85 border border-white/90 shadow-sm space-y-1.5"
            >
              <div className="font-semibold text-sm text-ink">{card.title}</div>
              <div className="text-xs text-ink-2">{card.subtitle}</div>
              <div className="flex items-center justify-between pt-1">
                <StatusPill status={card.badge} />
                {card.meta && (
                  <span className="text-[11px] font-medium text-muted">
                    {card.meta}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    ))}
  </div>
);

/**
 * 16. OrgChartNode, FileUploader & SignatureBlock (Reference Screens docs/06)
 */
export const OrgChartNode: React.FC<{
  name: string;
  nameBn?: string;
  title: string;
  department: string;
  code: string;
}> = ({ name, nameBn, title, department, code }) => (
  <div className="p-3.5 rounded-card bg-white/85 border border-indigo-200/80 shadow-sm flex items-center gap-3 min-w-[230px]">
    <Avatar name={name} size="sm" />
    <div className="min-w-0">
      <div className="text-xs font-bold text-ink truncate">{name}</div>
      {nameBn && <div className="text-[11px] text-ink-2 truncate">{nameBn}</div>}
      <div className="text-[11px] font-medium text-primary truncate">{title}</div>
      <div className="text-[10px] text-muted">
        {code} • {department}
      </div>
    </div>
  </div>
);

export const FileUploader: React.FC<{ label?: string }> = ({
  label = "Upload supporting receipt or signed PDF (Max 10MB, virus-scan enabled)",
}) => (
  <div className="border-2 border-dashed border-indigo-300/80 rounded-card p-5 text-center bg-white/50 hover:bg-white/75 transition-colors cursor-pointer">
    <FileUp className="w-6 h-6 text-primary mx-auto mb-1.5" />
    <p className="text-xs font-semibold text-ink">{label}</p>
    <p className="text-[11px] text-muted mt-0.5">
      Stored in S3/MinIO private bucket with signed URL access logging
    </p>
  </div>
);

export const SignatureBlock: React.FC = () => (
  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-8 mt-6 border-t border-slate-300/80 text-center">
    {["Prepared By (HR)", "Checked By (Audit)", "Authorized By (Finance)", "Approved By (MD / Director)"].map(
      (role) => (
        <div key={role} className="pt-8 border-t border-slate-400/70">
          <span className="text-xs font-semibold text-ink-2">{role}</span>
        </div>
      )
    )}
  </div>
);

export const StatutoryDisclaimerBanner: React.FC<{ text?: string }> = ({
  text = "Bangladesh editable statutory configuration — flagged 'needs review by a local HR/tax professional' per AGENTS.md Section 2.7.",
}) => (
  <div className="flex items-center gap-3 px-4 py-3 rounded-control bg-amber-500/15 border border-amber-500/35 text-amber-900 text-xs font-medium">
    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
    <span>{text}</span>
  </div>
);

/**
 * 17. ConfirmDialog (Destructive / Irreversible Action Confirmation per docs/03)
 */
export const ConfirmDialog: React.FC<{
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}> = ({
  open,
  title,
  description,
  confirmLabel = "Confirm Action",
  onConfirm,
  onCancel,
}) => (
  <Modal open={open} title={title} onClose={onCancel}>
    <div className="space-y-4">
      <p className="text-xs text-ink-2">{description}</p>
      <div className="flex justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button variant="danger" size="sm" onClick={onConfirm}>
          {confirmLabel}
        </Button>
      </div>
    </div>
  </Modal>
);

/**
 * 18. ApprovalInboxCard (Used in Dashboard & Workflow Inbox per docs/03)
 */
export const ApprovalInboxCard: React.FC<{
  title: string;
  requester: string;
  moduleLabel: string;
  stepText: string;
  status: string;
  onApprove?: () => void;
  onReject?: () => void;
}> = ({
  title,
  requester,
  moduleLabel,
  stepText,
  status,
  onApprove,
  onReject,
}) => (
  <GlassCard className="p-4 flex flex-wrap items-center justify-between gap-3">
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="text-xs font-bold text-ink">{title}</span>
        <StatusPill status={status} />
      </div>
      <div className="text-[11px] text-ink-2">
        Requester: <strong>{requester}</strong> • {moduleLabel} • {stepText}
      </div>
    </div>
    {onApprove && onReject && status !== "APPROVED" && status !== "REJECTED" && (
      <div className="flex items-center gap-2">
        <Button size="sm" onClick={onApprove}>
          Approve
        </Button>
        <Button size="sm" variant="danger" onClick={onReject}>
          Reject
        </Button>
      </div>
    )}
  </GlassCard>
);

/**
 * 19. PivotTable (Multi-dimensional cross-tabulation for Leave & Payroll per docs/03 & docs/06)
 */
export const PivotTable: React.FC<{
  title: string;
  rowLabel: string;
  columns: string[];
  rows: { rowKey: string; values: Record<string, string | number> }[];
}> = ({ title, rowLabel, columns, rows }) => (
  <GlassPanel className="p-0 overflow-hidden">
    <div className="p-4 border-b border-slate-200/70 bg-white/40 flex items-center justify-between">
      <span className="text-xs font-bold uppercase tracking-wider text-ink">
        {title}
      </span>
      <StatusPill status="Pivot Matrix" tone="info" />
    </div>
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-200/80 bg-slate-50/70 text-[11px] font-bold uppercase tracking-wider text-ink-2">
            <th className="py-3 px-4">{rowLabel}</th>
            {columns.map((c) => (
              <th key={c} className="py-3 px-4 text-right">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200/60 text-xs bg-white/80">
          {rows.map((r) => (
            <tr key={r.rowKey} className="hover:bg-indigo-50/50">
              <td className="py-2.5 px-4 font-bold text-ink">{r.rowKey}</td>
              {columns.map((c) => (
                <td key={c} className="py-2.5 px-4 text-right font-mono text-ink-2">
                  {r.values[c] ?? "0"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </GlassPanel>
);

/**
 * 20. CalendarGrid (Monthly Attendance / Leave / Holiday Calendar Grid per docs/03 & docs/06)
 */
export const CalendarGrid: React.FC<{
  monthLabel: string;
  events: { day: number; title: string; status: string }[];
}> = ({ monthLabel, events }) => {
  const days = Array.from({ length: 31 }, (_, i) => i + 1);
  const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri (Off)", "Sat"];
  return (
    <GlassPanel className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-ink">{monthLabel}</h3>
        <StatusPill status="Friday Weekly Off (BD)" tone="info" />
      </div>
      <div className="grid grid-cols-7 gap-1.5 text-center text-[11px] font-bold text-ink-2">
        {weekDays.map((wd) => (
          <div key={wd} className="py-1.5 bg-slate-100/80 rounded">
            {wd}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1.5">
        {days.map((d) => {
          const dayEvents = events.filter((e) => e.day === d);
          const isFriday = d % 7 === 6;
          return (
            <div
              key={d}
              className={`min-h-[68px] p-1.5 rounded-control border text-xs flex flex-col justify-between ${
                isFriday
                  ? "bg-amber-50/60 border-amber-200/70 text-amber-900"
                  : "bg-white/80 border-slate-200/70 text-ink"
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="font-bold text-[11px]">{d}</span>
                {isFriday && (
                  <span className="text-[9px] uppercase font-bold text-amber-700">
                    Off
                  </span>
                )}
              </div>
              <div className="space-y-1">
                {dayEvents.map((ev, idx) => (
                  <div
                    key={idx}
                    className="px-1.5 py-0.5 rounded bg-indigo-500/15 text-primary text-[10px] font-semibold truncate"
                    title={ev.title}
                  >
                    {ev.title}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </GlassPanel>
  );
};
