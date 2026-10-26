import React, { useEffect, useState } from "react";
import {
  Button,
  DataTable,
  Drawer,
  GlassCard,
  GlassPanel,
  Input,
  KPITile,
  Select,
  StatusPill,
} from "../components/glass";
import { apiFetch } from "../lib/api";
import { formatBDT } from "../i18n";
import { Building2, CheckSquare, Plus, ShieldCheck, Layers } from "lucide-react";

export const PlatformAdminPage: React.FC = () => {
  const [plans, setPlans] = useState<any[]>([]);
  const [tenants, setTenants] = useState<any[]>([]);
  const [selectedTenant, setSelectedTenant] = useState<any | null>(null);
  const [tenantModules, setTenantModules] = useState<any[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [newTenantName, setNewTenantName] = useState("");
  const [newTenantSlug, setNewTenantSlug] = useState("");
  const [newTenantMulti, setNewTenantMulti] = useState("false");
  const [toast, setToast] = useState<string | null>(null);

  const loadPlatform = async () => {
    try {
      const [p, t] = await Promise.all([
        apiFetch("/platform/plans/"),
        apiFetch("/platform/tenants/"),
      ]);
      setPlans(Array.isArray(p) ? p : p?.results || []);
      const tList = Array.isArray(t) ? t : t?.results || [];
      setTenants(tList);
      if (tList[0] && !selectedTenant) {
        loadTenantModules(tList[0]);
      }
    } catch {
      // Non-platform user fallback
    }
  };

  const loadTenantModules = async (tenant: any) => {
    setSelectedTenant(tenant);
    try {
      const mods = await apiFetch(`/platform/tenants/${tenant.id}/modules/`);
      setTenantModules(mods);
    } catch {
      setTenantModules([]);
    }
  };

  useEffect(() => {
    loadPlatform();
  }, []);

  const handleToggleModule = async (modNumber: number, currentEnabled: boolean) => {
    if (!selectedTenant) return;
    const updated = await apiFetch(`/platform/tenants/${selectedTenant.id}/modules/`, {
      method: "PATCH",
      body: JSON.stringify({
        modules: [{ module_number: modNumber, is_enabled: !currentEnabled }],
      }),
    });
    setTenantModules(updated);
    setToast(`Module #${modNumber} ${!currentEnabled ? "enabled" : "disabled"} for ${selectedTenant.name}`);
    setTimeout(() => setToast(null), 3000);
  };

  const handleCreateTenant = async () => {
    if (!newTenantName || !newTenantSlug || !plans[0]) return;
    await apiFetch("/platform/tenants/", {
      method: "POST",
      body: JSON.stringify({
        name: newTenantName,
        slug: newTenantSlug,
        plan: plans[0].id,
        multi_company_enabled: newTenantMulti === "true",
      }),
    });
    setDrawerOpen(false);
    setNewTenantName("");
    setNewTenantSlug("");
    loadPlatform();
  };

  return (
    <div className="h-full flex flex-col gap-3 overflow-y-auto pr-0.5">
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 glass-strong px-4 py-3 border-l-4 border-l-primary text-xs font-bold text-ink">
          {toast}
        </div>
      )}

      <GlassCard className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-primary" />
            <h1 className="text-xl font-bold text-ink">
              Platform Administration (Above Tenants)
            </h1>
          </div>
          <p className="text-xs text-ink-2 mt-1">
            Manage SaaS subscription plans, provision Single-Company or Multi-Company Tenants, and toggle enabled modules per tenant (docs/01-modules.md).
          </p>
        </div>
        <Button size="sm" onClick={() => setDrawerOpen(true)}>
          <Plus className="w-4 h-4" />
          <span>Provision New Tenant</span>
        </Button>
      </GlassCard>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KPITile
          label="Active Client Tenants"
          value={tenants.length}
          subtitle="Shared schema, strict tenant_id isolation"
          badge="ACTIVE"
          icon={<Building2 className="w-4 h-4" />}
        />
        <KPITile
          label="Subscription Plans"
          value={plans.length}
          subtitle="Single-Entity & Multi-Company Group"
          badge="BDT"
          icon={<Layers className="w-4 h-4" />}
        />
        <KPITile
          label="HRM Module Catalog"
          value="42 Modules"
          subtitle="Per-tenant endpoint & nav gating"
          badge="VERIFIED"
          icon={<CheckSquare className="w-4 h-4" />}
        />
      </div>

      <DataTable
        columns={[
          {
            key: "name",
            header: "Tenant Organization",
            render: (r) => (
              <div>
                <div className="font-bold text-ink">{r.name}</div>
                <div className="text-xs text-muted">{r.name_bn}</div>
              </div>
            ),
          },
          { key: "slug", header: "Subdomain / Slug" },
          { key: "plan_name", header: "Subscription Plan" },
          {
            key: "multi_company_enabled",
            header: "Company Mode",
            render: (r) => (
              <StatusPill
                status={
                  r.multi_company_enabled
                    ? `Multi-Company (${r.company_count} Entities)`
                    : "Single-Company"
                }
                tone={r.multi_company_enabled ? "info" : "neutral"}
              />
            ),
          },
          {
            key: "usage",
            header: "Employee Usage",
            render: (r) => `${r.employee_count} / ${r.employee_limit}`,
          },
          {
            key: "enabled_module_count",
            header: "Enabled Modules",
            render: (r) => `${r.enabled_module_count} / 42`,
          },
          {
            key: "status",
            header: "Status",
            render: (r) => <StatusPill status={r.status} />,
          },
          {
            key: "manage",
            header: "Module Matrix",
            render: (r) => (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => loadTenantModules(r)}
              >
                Configure Modules
              </Button>
            ),
          },
        ]}
        data={tenants}
      />

      {selectedTenant && tenantModules.length > 0 && (
        <GlassPanel className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-ink">
                42-Module Enablement Matrix for: {selectedTenant.name}
              </h3>
              <p className="text-xs text-muted">
                Per AGENTS.md Section 4: Only modules enabled for a tenant expose API endpoints and navigation items.
              </p>
            </div>
            <StatusPill status={selectedTenant.slug} />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {tenantModules.map((m) => (
              <div
                key={m.module_number}
                onClick={() => handleToggleModule(m.module_number, m.is_enabled)}
                className={`p-3 rounded-control border flex items-center justify-between cursor-pointer transition-all ${
                  m.is_enabled
                    ? "bg-white/90 border-indigo-200 shadow-sm"
                    : "bg-slate-100/60 border-slate-200 opacity-60"
                }`}
              >
                <div className="min-w-0">
                  <div className="text-xs font-bold text-ink truncate">
                    #{m.module_number}. {m.module_name}
                  </div>
                  <div className="text-[10px] text-muted">
                    {m.module_group} • Phase {m.phase}
                  </div>
                </div>
                <StatusPill status={m.is_enabled ? "ON" : "OFF"} />
              </div>
            ))}
          </div>
        </GlassPanel>
      )}

      <Drawer
        open={drawerOpen}
        title="Provision New Client Tenant"
        onClose={() => setDrawerOpen(false)}
      >
        <div className="space-y-4">
          <Input
            label="Organization Name"
            value={newTenantName}
            onChange={(e) => setNewTenantName(e.target.value)}
            placeholder="e.g. Meghna Knitwear Ltd."
          />
          <Input
            label="Tenant Slug / Subdomain"
            value={newTenantSlug}
            onChange={(e) => setNewTenantSlug(e.target.value)}
            placeholder="e.g. meghna-knitwear"
          />
          <Select
            label="Company Architecture Mode"
            value={newTenantMulti}
            onChange={(e) => setNewTenantMulti(e.target.value)}
            options={[
              { value: "false", label: "Single-Company Tenant (No Company Switcher)" },
              { value: "true", label: "Multi-Company Group (Enables Company Switcher & Transfers)" },
            ]}
          />
          <Button className="w-full" onClick={handleCreateTenant}>
            Create Tenant & Seed Master Fixtures
          </Button>
        </div>
      </Drawer>
    </div>
  );
};
