import React, { useEffect, useMemo, useState } from "react";
import {
  ALL_42_MODULES_CATALOG,
  ModuleMeta,
  apiFetch,
} from "../lib/api";
import { Button, Input, Modal, Select } from "./glass";
import {
  BarChart3,
  Briefcase,
  Check,
  Clock,
  Code2,
  Headphones,
  Layers,
  Plus,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Trash2,
  User,
  UserCheck,
  Users,
  Wallet,
} from "lucide-react";

interface RolePermEntry {
  id?: string;
  module_number: number;
  actions: string[];
}

interface RoleItem {
  id: string;
  name: string;
  code: string;
  badge_label: string;
  description: string;
  display_order: number;
  is_system_role: boolean;
  can_view_confidential_salary: boolean;
  can_view_confidential_medical: boolean;
  has_approval_authority: boolean;
  permissions: RolePermEntry[];
}

const ACTIONS = ["view", "create", "edit", "delete"] as const;

export const RolesPermissionsMatrixView: React.FC<{
  onNotify: (msg: string) => void;
  onPermissionsChanged?: () => void;
}> = ({ onNotify, onPermissionsChanged }) => {
  const [roles, setRoles] = useState<RoleItem[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [togglingKey, setTogglingKey] = useState<string | null>(null);

  // + Add Role Modal state
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [newRoleName, setNewRoleName] = useState("");
  const [newRoleBadge, setNewRoleBadge] = useState("Custom Role");
  const [newRoleDesc, setNewRoleDesc] = useState("");
  const [newRoleTemplate, setNewRoleTemplate] = useState("user");
  const [newRoleSalary, setNewRoleSalary] = useState(false);
  const [newRoleApproval, setNewRoleApproval] = useState(false);
  const [creatingRole, setCreatingRole] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Delete Role state
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deletingRole, setDeletingRole] = useState(false);

  const loadRoles = async (preferRoleId?: string) => {
    setLoading(true);
    try {
      const res = await apiFetch("/accounts/roles/");
      const list: RoleItem[] = Array.isArray(res) ? res : res?.results || [];
      setRoles(list);
      if (preferRoleId && list.some((r) => r.id === preferRoleId)) {
        setSelectedRoleId(preferRoleId);
      } else if (!selectedRoleId && list.length > 0) {
        const adminRole = list.find((r) => r.code === "admin") || list[0];
        setSelectedRoleId(adminRole.id);
      }
    } catch (err: any) {
      onNotify(err.message || "Failed to load roles");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRoles();
  }, []);

  const selectedRole = useMemo(
    () => roles.find((r) => r.id === selectedRoleId) || roles[0] || null,
    [roles, selectedRoleId]
  );

  const permMap = useMemo(() => {
    const map: Record<number, Set<string>> = {};
    if (!selectedRole) return map;
    for (const p of selectedRole.permissions || []) {
      map[p.module_number] = new Set((p.actions || []).map((a) => a.toLowerCase()));
    }
    return map;
  }, [selectedRole]);

  const totalPossibleActions = ALL_42_MODULES_CATALOG.length * ACTIONS.length;

  const grantedActionsCount = useMemo(() => {
    let count = 0;
    for (const mod of ALL_42_MODULES_CATALOG) {
      const set = permMap[mod.number];
      if (!set) continue;
      for (const act of ACTIONS) {
        if (set.has(act)) count += 1;
      }
    }
    return count;
  }, [permMap]);

  const coveragePct = useMemo(() => {
    if (totalPossibleActions === 0) return 0;
    return Math.round((grantedActionsCount / totalPossibleActions) * 100);
  }, [grantedActionsCount, totalPossibleActions]);

  const groupedModules = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    const filtered = ALL_42_MODULES_CATALOG.filter((m) => {
      if (!q) return true;
      return (
        m.name.toLowerCase().includes(q) ||
        m.group.toLowerCase().includes(q) ||
        m.submodules.some((s) => s.toLowerCase().includes(q))
      );
    });
    const groups: { group: string; modules: ModuleMeta[] }[] = [];
    for (const m of filtered) {
      let existing = groups.find((g) => g.group === m.group);
      if (!existing) {
        existing = { group: m.group, modules: [] };
        groups.push(existing);
      }
      existing.modules.push(m);
    }
    return groups;
  }, [searchQuery]);

  const getRoleTabIcon = (code: string) => {
    switch (code) {
      case "super-admin":
        return <ShieldCheck className="w-4 h-4" />;
      case "admin":
        return <Shield className="w-4 h-4" />;
      case "manager":
        return <UserCheck className="w-4 h-4" />;
      case "asst-manager":
        return <Users className="w-4 h-4" />;
      case "developer":
        return <Code2 className="w-4 h-4" />;
      case "support":
        return <Headphones className="w-4 h-4" />;
      default:
        return <User className="w-4 h-4" />;
    }
  };

  const getGroupIcon = (group: string) => {
    switch (group) {
      case "Overview":
        return <BarChart3 className="w-4 h-4 text-indigo-600" />;
      case "Core HR":
        return <Users className="w-4 h-4 text-indigo-600" />;
      case "Time & Presence":
        return <Clock className="w-4 h-4 text-indigo-600" />;
      case "Payroll & Compensation":
        return <Wallet className="w-4 h-4 text-indigo-600" />;
      case "Talent Lifecycle":
        return <Briefcase className="w-4 h-4 text-indigo-600" />;
      case "Relations, Assets & Exit":
        return <ShieldAlert className="w-4 h-4 text-indigo-600" />;
      default:
        return <Layers className="w-4 h-4 text-indigo-600" />;
    }
  };

  const handleToggleAction = async (moduleNumber: number, action: string) => {
    if (!selectedRole) return;
    const key = `${moduleNumber}-${action}`;
    setTogglingKey(key);
    try {
      const updatedRole: RoleItem = await apiFetch(
        `/accounts/roles/${selectedRole.id}/toggle-permission/`,
        {
          method: "POST",
          body: JSON.stringify({ module_number: moduleNumber, action }),
        }
      );
      setRoles((prev) =>
        prev.map((r) => (r.id === updatedRole.id ? updatedRole : r))
      );
      onPermissionsChanged?.();
    } catch (err: any) {
      onNotify(err.message || "Failed to update permission");
    } finally {
      setTogglingKey(null);
    }
  };

  const handleBulkGroup = async (modules: ModuleMeta[], grant: boolean) => {
    if (!selectedRole) return;
    const moduleNumbers = modules.map((m) => m.number);
    try {
      const updatedRole: RoleItem = await apiFetch(
        `/accounts/roles/${selectedRole.id}/bulk-group-permissions/`,
        {
          method: "POST",
          body: JSON.stringify({ module_numbers: moduleNumbers, grant }),
        }
      );
      setRoles((prev) =>
        prev.map((r) => (r.id === updatedRole.id ? updatedRole : r))
      );
      onNotify(
        `${grant ? "Granted" : "Revoked"} all permissions in group for ${selectedRole.name}`
      );
      onPermissionsChanged?.();
    } catch (err: any) {
      onNotify(err.message || "Failed to update group permissions");
    }
  };

  const handleCreateRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRoleName.trim()) {
      setCreateError("Role name is required.");
      return;
    }
    setCreatingRole(true);
    setCreateError(null);
    try {
      const created: RoleItem = await apiFetch("/accounts/roles/", {
        method: "POST",
        body: JSON.stringify({
          name: newRoleName.trim(),
          badge_label: newRoleBadge.trim() || "Custom Role",
          description:
            newRoleDesc.trim() ||
            `Custom access role for ${newRoleName.trim()}`,
          display_order: roles.length + 1,
          can_view_confidential_salary: newRoleSalary,
          has_approval_authority: newRoleApproval,
          template_role_code: newRoleTemplate,
        }),
      });
      setAddModalOpen(false);
      setNewRoleName("");
      setNewRoleBadge("Custom Role");
      setNewRoleDesc("");
      onNotify(`Created role "${created.name}"! You can now customize its module permissions or assign it to employees.`);
      await loadRoles(created.id);
      onPermissionsChanged?.();
    } catch (err: any) {
      setCreateError(err.message || "Failed to create role");
    } finally {
      setCreatingRole(false);
    }
  };

  const isProtectedRole =
    selectedRole?.code === "super-admin" || selectedRole?.code === "admin";

  const handleDeleteRole = async () => {
    if (!selectedRole || isProtectedRole) return;
    setDeletingRole(true);
    try {
      await apiFetch(`/accounts/roles/${selectedRole.id}/`, {
        method: "DELETE",
      });
      onNotify(`Role "${selectedRole.name}" deleted successfully.`);
      setDeleteConfirmOpen(false);
      const remaining = roles.filter((r) => r.id !== selectedRole.id);
      setRoles(remaining);
      const nextRole = remaining.find((r) => r.code === "admin") || remaining[0];
      if (nextRole) {
        setSelectedRoleId(nextRole.id);
      }
      onPermissionsChanged?.();
    } catch (err: any) {
      onNotify(err.message || "Failed to delete role.");
    } finally {
      setDeletingRole(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Header Bar Matching Reference Screenshot */}
      <div className="glass-strong p-4 rounded-card border border-white/80 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold tracking-tight text-slate-900">
            <span className="bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
              Roles &amp;
            </span>{" "}
            Permissions
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage access levels, granular module boundaries, and permission matrix.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter permissions..."
              className="pl-8 pr-3 py-1.5 text-xs rounded-control bg-white/90 border border-slate-200/90 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 w-56"
            />
          </div>
          <Button
            size="sm"
            onClick={() => {
              setCreateError(null);
              setAddModalOpen(true);
            }}
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Role</span>
          </Button>
        </div>
      </div>

      {/* Horizontal Role Tabs Bar */}
      <div className="glass-strong px-4 pt-2 rounded-card border border-white/80 flex items-center gap-6 overflow-x-auto">
        {roles.map((role) => {
          const active = selectedRole?.id === role.id;
          return (
            <button
              key={role.id}
              type="button"
              onClick={() => setSelectedRoleId(role.id)}
              className={`flex items-center gap-2 pb-2.5 pt-1 text-xs font-semibold border-b-2 transition-all whitespace-nowrap ${
                active
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              {getRoleTabIcon(role.code)}
              <span>{role.name}</span>
            </button>
          );
        })}
      </div>

      {/* Selected Role Summary Banner Card + Access Coverage % */}
      {selectedRole && (
        <div className="glass-strong p-4 rounded-card border border-white/80 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-600 shrink-0">
              {getRoleTabIcon(selectedRole.code)}
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="text-base font-extrabold text-slate-900">
                  {selectedRole.name}
                </h3>
                <span className="px-2.5 py-0.5 rounded-pill text-[11px] font-bold bg-indigo-500/10 text-indigo-600 border border-indigo-500/20">
                  {selectedRole.badge_label || "Workspace Role"}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {selectedRole.description ||
                  "Configure module view, create, edit, and delete permissions for this role."}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {!isProtectedRole && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => setDeleteConfirmOpen(true)}
                className="gap-1.5"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Role</span>
              </Button>
            )}
            <div className="px-4 py-2.5 rounded-xl bg-slate-50/90 border border-slate-200/80 text-right min-w-[155px]">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                ACCESS COVERAGE
              </div>
              <div className="text-xl font-black text-indigo-600 leading-tight mt-0.5">
                {coveragePct}%
              </div>
              <div className="text-[11px] text-slate-400 font-medium">
                {grantedActionsCount} of {totalPossibleActions} actions
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2-Column Category Grid of Module Permission Cards */}
      {loading ? (
        <div className="glass-strong p-8 rounded-card text-center text-xs text-slate-500">
          Loading permission matrix...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {groupedModules.map(({ group, modules }) => {
            const allGrantedInGroup = modules.every((m) => {
              const s = permMap[m.number];
              return s && ACTIONS.every((a) => s.has(a));
            });

            return (
              <div
                key={group}
                className="glass-strong p-4 rounded-card border border-white/80 flex flex-col"
              >
                {/* Card Header */}
                <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-200/70">
                  <div className="flex items-center gap-2">
                    {getGroupIcon(group)}
                    <h4 className="text-xs font-extrabold text-slate-900">
                      {group}
                    </h4>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleBulkGroup(modules, !allGrantedInGroup)}
                    className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-white hover:bg-indigo-50 text-slate-600 hover:text-indigo-600 border border-slate-200/90 transition-colors"
                  >
                    {allGrantedInGroup ? "Revoke All" : "Grant All"}
                  </button>
                </div>

                {/* Column Headers */}
                <div className="grid grid-cols-[1fr_52px_52px_52px_52px] items-center gap-1 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100">
                  <div>MODULE / SCOPE</div>
                  <div className="text-center">VIEW</div>
                  <div className="text-center">CREATE</div>
                  <div className="text-center">EDIT</div>
                  <div className="text-center">DELETE</div>
                </div>

                {/* Module Rows */}
                <div className="divide-y divide-slate-100">
                  {modules.map((mod) => {
                    const activeSet = permMap[mod.number] || new Set<string>();
                    return (
                      <div
                        key={mod.number}
                        className="grid grid-cols-[1fr_52px_52px_52px_52px] items-center gap-1 py-2.5"
                      >
                        <div className="pr-2 min-w-0">
                          <div className="text-xs font-bold text-slate-900 truncate">
                            {mod.name}
                          </div>
                          <div className="text-[11px] text-slate-400 truncate mt-0.5">
                            {mod.submodules.slice(0, 4).join(", ")}
                          </div>
                        </div>

                        {ACTIONS.map((act) => {
                          const isChecked = activeSet.has(act);
                          const isBusy = togglingKey === `${mod.number}-${act}`;
                          return (
                            <div
                              key={act}
                              className="flex items-center justify-center"
                            >
                              <button
                                type="button"
                                disabled={isBusy}
                                onClick={() =>
                                  handleToggleAction(mod.number, act)
                                }
                                title={`${isChecked ? "Revoke" : "Grant"} ${act.toUpperCase()} on ${mod.name}`}
                                className={`w-7 h-7 rounded-lg flex items-center justify-center transition-all ${
                                  isChecked
                                    ? "bg-indigo-600 text-white shadow-sm hover:bg-indigo-700"
                                    : "bg-white/90 border border-slate-200 text-slate-300 hover:border-indigo-400 hover:text-indigo-500"
                                }`}
                              >
                                {isChecked ? (
                                  <Check className="w-3.5 h-3.5 stroke-[2.8]" />
                                ) : (
                                  <span className="w-1 h-1 rounded-full bg-slate-300" />
                                )}
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* + Add Role Modal */}
      <Modal
        open={addModalOpen}
        title="Create New Role (+ Add Role)"
        onClose={() => setAddModalOpen(false)}
      >
        <form onSubmit={handleCreateRole} className="space-y-3.5">
          <Input
            label="Role Name *"
            placeholder="e.g. Payroll Specialist / Branch HR"
            value={newRoleName}
            onChange={(e) => {
              setNewRoleName(e.target.value);
              setCreateError(null);
            }}
          />
          <Input
            label="Role Badge Label"
            placeholder="e.g. Finance & Payroll Team"
            value={newRoleBadge}
            onChange={(e) => setNewRoleBadge(e.target.value)}
          />
          <Input
            label="Role Description"
            placeholder="e.g. Manages monthly payroll runs, tax slabs, and employee records"
            value={newRoleDesc}
            onChange={(e) => setNewRoleDesc(e.target.value)}
          />
          <Select
            label="Copy Initial Permissions From"
            value={newRoleTemplate}
            onChange={(e) => setNewRoleTemplate(e.target.value)}
            options={[
              { value: "user", label: "User (Standard Employee Self-Service)" },
              { value: "support", label: "Support (Helpdesk & Operations)" },
              { value: "developer", label: "Developer (IT & Integrations)" },
              { value: "asst-manager", label: "Asst. Manager (Team Supervisor)" },
              { value: "manager", label: "Manager (Department Lead)" },
              { value: "admin", label: "Admin (100% Full Workspace Access)" },
            ]}
          />

          <div className="grid grid-cols-2 gap-3 pt-1">
            <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={newRoleSalary}
                onChange={(e) => setNewRoleSalary(e.target.checked)}
                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span>Can View Confidential Salary</span>
            </label>
            <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={newRoleApproval}
                onChange={(e) => setNewRoleApproval(e.target.checked)}
                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span>Has Workflow Approval Authority</span>
            </label>
          </div>

          {createError && (
            <div className="p-2.5 rounded-control bg-red-500/15 border border-red-500/30 text-xs font-semibold text-red-800">
              {createError}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setAddModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={creatingRole}>
              <Sparkles className="w-3.5 h-3.5" />
              <span>{creatingRole ? "Creating..." : "Create Role"}</span>
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Role Confirmation Modal */}
      <Modal
        open={deleteConfirmOpen}
        title={`Delete Role: ${selectedRole?.name || ""}`}
        onClose={() => setDeleteConfirmOpen(false)}
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-600 leading-relaxed">
            Are you sure you want to delete the role{" "}
            <strong className="text-slate-900">{selectedRole?.name}</strong>?
          </p>
          <div className="p-3 rounded-control bg-amber-500/10 border border-amber-500/25 text-amber-900 space-y-1">
            <div className="font-bold flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              <span>Automatic Employee Fallback</span>
            </div>
            <p className="text-[11px] text-amber-800">
              Any employees currently assigned to this role will automatically revert to
              the standard <strong>User</strong> role without losing any employee or
              payroll data.
            </p>
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-200/80">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setDeleteConfirmOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="danger"
              size="sm"
              disabled={deletingRole}
              onClick={handleDeleteRole}
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{deletingRole ? "Deleting..." : "Confirm Delete"}</span>
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
