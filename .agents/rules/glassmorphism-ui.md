# Rule: Light glassmorphism UI (always on when editing frontend/)
- Read `docs/03-design-system.md` before writing UI.
- Use only design tokens (CSS variables / Tailwind theme). No hard-coded colours.
- Dense data (tables, forms, payroll grids, modals) sits on strong glass (alpha >= 0.80). Light glass only for shell and dashboard cards.
- Max two overlapping blur layers; never blur table rows.
- Always provide `@supports not (backdrop-filter)`, reduced-transparency and reduced-motion fallbacks.
- Reuse components from the library; add new ones to `/design-system` first.
- Text contrast AA; status never by colour alone.
