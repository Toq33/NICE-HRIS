import React, { useEffect, useState } from "react";
import {
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  ALL_42_MODULES_CATALOG,
  apiFetch,
  setActiveCompanyHeader,
  setAuthToken,
} from "./lib/api";
import { Avatar, Button, StatusPill } from "./components/glass";
import { DesignSystemPage } from "./pages/DesignSystemPage";
import { ModuleWorkspace } from "./pages/ModuleWorkspace";
import { PlatformAdminPage } from "./pages/PlatformAdminPage";
import {
  Bell,
  Building2,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  Compass,
  Globe,
  Home,
  Layers,
  LayoutDashboard,
  Palette,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

const ModuleRouteWrapper: React.FC<{
  lakhGrouping: boolean;
  activeCompanyId: string | null;
}> = ({ lakhGrouping, activeCompanyId }) => {
  const { num } = useParams<{ num: string }>();
  const modNum = parseInt(num || "1", 10) || 1;
  return (
    <ModuleWorkspace
      moduleNumber={modNum}
      lakhGrouping={lakhGrouping}
      activeCompanyId={activeCompanyId}
    />
  );
};

export const App: React.FC = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [moduleSearch, setModuleSearch] = useState("");
  const searchInputRef = React.useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSidebarCollapsed(false);
        setTimeout(() => searchInputRef.current?.focus(), 50);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
  const [personas, setPersonas] = useState<any[]>([]);
  const [session, setSession] = useState<any>(null);
  const [activeCompanyId, setActiveCompanyId] = useState<string | null>(null);
  const [lakhGrouping, setLakhGrouping] = useState(true);

  const switchPersona = async (email: string) => {
    try {
      const res = await apiFetch("/auth/demo-personas/", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setAuthToken(res.access);
      setSession(res);
      const firstComp = res.active_company_id || res.companies?.[0]?.id || null;
      setActiveCompanyId(firstComp);
      setActiveCompanyHeader(firstComp);
      if (res.user?.is_platform_admin && !res.tenant) {
        navigate("/platform-admin");
      } else if (res.user?.experience_mode === "EMPLOYEE") {
        navigate("/m/32/employee-self-service");
      } else if (res.user?.experience_mode === "MANAGER") {
        navigate("/m/33/manager-self-service");
      } else if (location.pathname === "/platform-admin") {
        navigate("/m/1/management-dashboard");
      }
    } catch (err) {
      console.error("Failed to switch persona:", err);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const listRes = await apiFetch("/auth/demo-personas/");
        const personaList = listRes.personas || [];
        setPersonas(personaList);
        // Default login to Multi-Company Group HR or Single-Company HR Admin so everything is live immediately
        const defaultPersona =
          personaList.find((p: any) => p.email === "group.hr@jamunagroup.bd") ||
          personaList.find((p: any) => p.email === "hr.admin@padmaapparel.bd") ||
          personaList[0];
        if (defaultPersona) {
          await switchPersona(defaultPersona.email);
        }
      } catch (err) {
        console.error("Initial bootstrap error:", err);
      }
    })();
  }, []);

  const enabledSet = new Set<number>(
    session?.enabled_module_numbers || ALL_42_MODULES_CATALOG.map((m) => m.number)
  );

  const visibleModules = ALL_42_MODULES_CATALOG.filter((m) => {
    if (!enabledSet.has(m.number)) return false;
    if (!moduleSearch.trim()) return true;
    const q = moduleSearch.toLowerCase();
    return (
      m.name.toLowerCase().includes(q) ||
      m.group.toLowerCase().includes(q) ||
      String(m.number) === q ||
      m.submodules.some((s) => s.toLowerCase().includes(q))
    );
  });

  const groups = Array.from(new Set(visibleModules.map((m) => m.group)));

  // Per AGENTS.md Section 1 & 4:
  // Single-company tenant NEVER sees company switchers or company filters; multi-company tenant gets them.
  const showCompanySwitcher = Boolean(session?.tenant?.show_company_switcher);

  return (
    <div className="h-dvh max-h-dvh relative overflow-hidden flex flex-col">
      {/* 3 Blurred Pastel Background Blobs (docs/03-design-system.md) */}
      <div
        aria-hidden="true"
        className="fixed inset-0 pointer-events-none -z-10 overflow-hidden"
      >
        <div
          className="absolute -top-24 -left-24 w-[460px] h-[460px] rounded-full blur-3xl"
          style={{ background: "var(--blob-indigo)" }}
        />
        <div
          className="absolute top-1/3 -right-24 w-[420px] h-[420px] rounded-full blur-3xl"
          style={{ background: "var(--blob-teal)" }}
        />
        <div
          className="absolute -bottom-28 left-1/3 w-[440px] h-[440px] rounded-full blur-3xl"
          style={{ background: "var(--blob-pink)" }}
        />
      </div>

      {/* Top Glass Navigation Bar */}
      <header className="shrink-0 z-30 px-4 pt-2.5">
        <div className="glass px-4 py-2 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-secondary text-white font-bold flex items-center justify-center shadow-sm">
              N
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-ink tracking-tight">
                  {t("app_title")}
                </span>
                {session?.tenant ? (
                  <StatusPill
                    status={
                      session.tenant.multi_company_enabled
                        ? t("multi_company_badge")
                        : t("single_company_badge")
                    }
                    tone={session.tenant.multi_company_enabled ? "info" : "success"}
                  />
                ) : (
                  <StatusPill status="Platform Layer" tone="warning" />
                )}
              </div>
              <div className="text-[11px] text-ink-2 font-medium">
                {session?.tenant
                  ? `${session.tenant.name} (${session.tenant.name_bn})`
                  : "Multi-Tenant SaaS Controller"}
              </div>
            </div>
          </div>

          {/* Center Controls: Multi-Company Switcher (ONLY for Multi-Company Tenants!) & Demo Tenant Switcher */}
          <div className="flex flex-wrap items-center gap-2.5">
            {showCompanySwitcher && (
              <div className="flex items-center gap-1.5 bg-indigo-500/10 border border-indigo-500/30 px-2.5 py-1 rounded-control">
                <Building2 className="w-3.5 h-3.5 text-primary" />
                <span className="text-[11px] font-bold text-primary">
                  {t("company_switcher")}:
                </span>
                <select
                  aria-label="Company Switcher"
                  value={activeCompanyId || ""}
                  onChange={(e) => {
                    const val = e.target.value || null;
                    setActiveCompanyId(val);
                    setActiveCompanyHeader(val);
                  }}
                  className="bg-transparent text-xs font-bold text-ink focus:outline-none"
                >
                  <option value="">All Group Entities (Consolidated)</option>
                  {(session?.companies || []).map((c: any) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.code})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Demo Tenant & Experience Switcher */}
            <div className="flex items-center gap-1.5 bg-white/75 border border-white/90 px-2.5 py-1 rounded-control">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              <span className="text-[11px] font-semibold text-ink-2">
                Tenant / Role:
              </span>
              <select
                aria-label="Demo Tenant and Persona Switcher"
                value={session?.user?.email || ""}
                onChange={(e) => switchPersona(e.target.value)}
                className="bg-transparent text-xs font-semibold text-ink focus:outline-none max-w-[240px]"
              >
                {personas.map((p) => (
                  <option key={p.id} value={p.email}>
                    [{p.multi_company_enabled ? "Multi-Co" : p.is_platform_admin ? "Platform" : "Single-Co"}]{" "}
                    {p.tenant_name} — {p.full_name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Right Utilities: Lakh Toggle, Language Toggle, Design System, Platform Admin, User Profile */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setLakhGrouping((v) => !v)}
              className="px-2.5 py-1 text-xs font-semibold rounded-control bg-white/70 border border-white/90 text-ink hover:bg-white"
              title="Toggle Bangladesh Lakh/Crore Number Formatting"
            >
              {lakhGrouping ? "৳ 1,25,000 (Lakh)" : "৳ 125,000"}
            </button>

            <button
              onClick={() =>
                i18n.changeLanguage(i18n.language === "en" ? "bn" : "en")
              }
              className="px-2.5 py-1 text-xs font-semibold rounded-control bg-white/70 border border-white/90 text-ink hover:bg-white flex items-center gap-1"
            >
              <Globe className="w-3.5 h-3.5 text-primary" />
              <span>{i18n.language === "en" ? "বাংলা" : "EN"}</span>
            </button>

            <Link
              to="/design-system"
              className="px-2.5 py-1 text-xs font-semibold rounded-control bg-white/70 border border-white/90 text-ink hover:bg-white flex items-center gap-1"
            >
              <Palette className="w-3.5 h-3.5 text-primary" />
              <span className="hidden sm:inline">{t("design_system")}</span>
            </Link>

            <Link
              to="/platform-admin"
              className="px-2.5 py-1 text-xs font-semibold rounded-control bg-indigo-500/10 border border-indigo-400/30 text-primary hover:bg-indigo-500/20 flex items-center gap-1"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{t("platform_admin")}</span>
            </Link>

            {session?.user && (
              <div className="flex items-center gap-2 pl-1">
                <Avatar name={session.user.full_name} size="sm" />
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Layout: Floating Glass Sidebar + Workspace */}
      <div className="flex-1 min-h-0 flex gap-3.5 px-4 pt-3 pb-16 md:pb-3 overflow-hidden">
        {/* Floating Collapsible Glass Sidebar */}
        <aside
          className={`hidden md:flex flex-col glass shrink-0 transition-all ${
            sidebarCollapsed ? "w-20" : "w-68"
          } p-3 h-full overflow-hidden`}
        >
          <div className="flex items-center justify-between gap-2 pb-3 mb-2 border-b border-white/70">
            {!sidebarCollapsed && (
              <div className="relative flex-1">
                <Search className="w-3.5 h-3.5 text-muted absolute left-2.5 top-2.5" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={moduleSearch}
                  onChange={(e) => setModuleSearch(e.target.value)}
                  placeholder="Jump to 42 modules (Ctrl+K)..."
                  className="w-full pl-8 pr-2.5 py-1.5 text-xs bg-white/85 border border-slate-200 rounded-control focus:outline-none focus:ring-2 focus:ring-primary/40"
                />
              </div>
            )}
            <button
              onClick={() => setSidebarCollapsed((c) => !c)}
              className="p-1.5 rounded-lg bg-white/70 hover:bg-white text-ink-2 mx-auto"
              aria-label="Toggle Sidebar"
            >
              {sidebarCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronLeft className="w-4 h-4" />
              )}
            </button>
          </div>

          <nav className="flex-1 overflow-y-auto space-y-4 pr-1">
            {groups.map((grp) => (
              <div key={grp} className="space-y-1">
                {!sidebarCollapsed && (
                  <div className="px-2 text-[10px] font-bold uppercase tracking-wider text-muted">
                    {grp}
                  </div>
                )}
                {visibleModules
                  .filter((m) => m.group === grp)
                  .map((m) => {
                    const path = `/m/${m.number}/${m.slug}`;
                    const active = location.pathname.startsWith(`/m/${m.number}/`);
                    return (
                      <Link
                        key={m.number}
                        to={path}
                        className={`flex items-center gap-2.5 px-2.5 py-2 rounded-control text-xs font-medium transition-all ${
                          active
                            ? "bg-primary text-white font-semibold shadow-sm"
                            : "text-ink hover:bg-white/70"
                        }`}
                        title={`#${m.number}. ${m.name}`}
                      >
                        <span
                          className={`w-6 h-6 rounded-lg text-[11px] font-bold flex items-center justify-center shrink-0 ${
                            active
                              ? "bg-white/20 text-white"
                              : "bg-indigo-500/10 text-primary"
                          }`}
                        >
                          {m.number}
                        </span>
                        {!sidebarCollapsed && (
                          <span className="truncate">{m.name}</span>
                        )}
                      </Link>
                    );
                  })}
              </div>
            ))}
          </nav>
        </aside>

        {/* Main Route View */}
        <main className="flex-1 min-w-0 min-h-0 h-full overflow-y-auto pr-1">
          <Routes>
            <Route
              path="/"
              element={<Navigate to="/m/1/management-dashboard" replace />}
            />
            <Route path="/design-system" element={<DesignSystemPage />} />
            <Route path="/platform-admin" element={<PlatformAdminPage />} />
            <Route
              path="/m/:num/:slug"
              element={
                <ModuleRouteWrapper
                  lakhGrouping={lakhGrouping}
                  activeCompanyId={activeCompanyId}
                />
              }
            />
          </Routes>
        </main>
      </div>

      {/* Mobile PWA Bottom Navigation Bar (docs/03 & docs/06: Home, Attendance, Leaves, Directory, More) */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 glass-strong rounded-none border-t border-white/80 px-3 py-2 flex items-center justify-around">
        {[
          { to: "/m/32/employee-self-service", label: "Home (ESS)", icon: Home },
          { to: "/m/8/attendance", label: "Attendance", icon: Clock },
          { to: "/m/10/leave", label: "Leaves", icon: Calendar },
          { to: "/m/3/employee-information", label: "Directory", icon: Users },
          { to: "/m/1/management-dashboard", label: "Dashboard", icon: LayoutDashboard },
        ].map((item) => {
          const Icon = item.icon;
          const active = location.pathname === item.to;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-lg text-[11px] font-semibold min-h-[44px] justify-center ${
                active ? "text-primary" : "text-ink-2"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
};
