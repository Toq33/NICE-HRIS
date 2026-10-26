# 03. Design System: Light Glassmorphism

Bright, airy, calm, professional. Frosted translucent panels float above a soft pastel gradient. Modern but readable: this is a data-heavy business product.

## Tokens (define as CSS variables AND Tailwind theme values)
```css
:root {
  --bg-1:#EEF2FF; --bg-2:#F5F3FF; --bg-3:#ECFEFF;
  --blob-indigo:rgba(79,70,229,.25); --blob-teal:rgba(20,184,166,.25); --blob-pink:rgba(236,72,153,.25);
  --glass:rgba(255,255,255,.55);
  --glass-strong:rgba(255,255,255,.80);
  --glass-border:rgba(255,255,255,.70);
  --blur:blur(16px) saturate(160%);
  --shadow:0 8px 32px rgba(31,38,135,.10);
  --highlight:inset 0 1px 0 rgba(255,255,255,.8);
  --radius-card:20px; --radius-control:12px; --radius-pill:999px;
  --text:#1E293B; --text-2:#475569; --text-muted:#64748B;
  --primary:#4F46E5; --secondary:#0EA5E9;
  --success:#10B981; --warning:#F59E0B; --danger:#EF4444;
  --motion:200ms ease-out;
}
body{background:linear-gradient(135deg,var(--bg-1),var(--bg-2),var(--bg-3)) fixed;font-family:Inter,'Noto Sans Bengali',system-ui,sans-serif;color:var(--text)}
.glass{background:var(--glass);backdrop-filter:var(--blur);-webkit-backdrop-filter:var(--blur);
  border:1px solid var(--glass-border);border-radius:var(--radius-card);box-shadow:var(--shadow),var(--highlight)}
.glass-strong{background:var(--glass-strong)}
@supports not (backdrop-filter: blur(1px)){.glass{background:#fff}}
@media (prefers-reduced-transparency: reduce){.glass{background:#fff;backdrop-filter:none}}
@media (prefers-reduced-motion: reduce){*{transition:none!important;animation:none!important}}
```
Page background also has 2 or 3 large blurred blobs (indigo, teal, pink) fixed behind content.

## Rules
1. **Readability first.** WCAG AA (4.5:1 body text). Never put small text directly on a busy blurred area.
2. **Dense data uses strong glass (>= .80).** Tables, long forms, payroll grids, modals. Light glass is for shell, dashboard cards, side panels.
3. **Limit stacked blurs:** at most two overlapping glass layers; no blur per table row (performance on low-end laptops).
4. Fallbacks and reduced-motion/transparency support are mandatory.
5. Motion 150-250 ms ease-out, subtle hover lift on cards. Nothing heavy.
6. Radius 20 / 12 / pill. Font Inter or Plus Jakarta Sans; Noto Sans Bengali for Bangla.

## Component library (build FIRST, before module screens)
GlassCard, GlassPanel, Button (primary, secondary, ghost, danger), Input, Select, DatePicker, Table (sortable, filterable, paginated), Tabs, Modal, Drawer, Toast, Badge/StatusPill, Avatar, EmptyState, Skeleton, Stepper, Timeline, KPI tile, Chart wrapper, ConfirmDialog.
Add extras the reference screens need: Kanban board, Pivot table, Calendar, Approval inbox card, Org chart node, File uploader, Signature/acknowledge block.
Hidden `/design-system` page shows every component and every state (default, hover, focus, disabled, loading, error, empty).

## App shell
- Floating glass **sidebar**: collapsible, grouped by module group, icons, search-to-jump.
- **Top bar:** global search, company switcher (shown ONLY for multi-company tenants), branch filter, notifications bell, help, profile menu.
- Content area on the gradient.
- **Role-aware navigation.** Three experiences, one app: Admin/HR, Manager (module 33), Employee (module 32). Users see only permitted, tenant-enabled modules.

## Standard screen patterns
List page (filters, saved views, bulk actions, export) / Detail page (summary header + tabs; "smart button" counters such as Documents, Contract, Goals, Org chart) / Create-edit as drawer or stepper / Approval inbox / History timeline on every record.
Status flows are shown with a visible stepper (e.g. Draft > Confirmed > Approved).

## Responsive and mobile (decision: responsive web app, native later)
Mobile-first for the employee and manager experiences; desktop-first layouts for HR admin screens. Build as an installable PWA (manifest, service worker, offline shell, add-to-home-screen). Bottom tab bar on phones (Home, Attendance, Leaves, Directory, More), sidebar on desktop. Touch targets >= 44px, safe-area insets, geolocation and camera via browser APIs. Keep all business logic in the API so a native app can be added later with no backend change; avoid browser-only assumptions in the API.

## Quality of life
Global search (employees, requests, documents), keyboard shortcuts (search, new record), clear empty/loading/error states, undo toast for destructive actions.

## Localisation
All strings via i18next. Dates/numbers per locale. BDT with lakh grouping as a selectable option (1,25,000). Amount in words (Taka) on salary sheets.

## Accessibility checklist (per screen)
Keyboard reachable, visible focus ring, labels on inputs, contrast AA, no information by colour alone (status pills carry text).
