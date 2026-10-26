# Rule: Backend standards (always on when editing backend/)
- Read `docs/02-architecture-and-database.md`.
- Every tenant model extends TenantModel; never query without the tenant manager.
- Business logic in `services/`, not views or serializers.
- Money NUMERIC(14,2) + currency; no floats. Soft delete only. Ledgers append-only.
- Approvals via Workflow Engine; audit automatic. Salary/medical/bank fields need explicit permission, masked in lists and exports.
- Every new endpoint: permission class, data scope, OpenAPI docs, tests. Every migration: indexes, reviewed, never edit applied ones.
- Legal/statutory values are config data with Bangladesh defaults flagged "needs professional review".
