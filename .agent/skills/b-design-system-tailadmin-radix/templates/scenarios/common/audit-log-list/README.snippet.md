# S01-C08 审计日志列表

## 复制入口

```tsx
import { AuditLogListPage } from "@/templates/scenarios/common/audit-log-list";
```

## 组件组合

- `ListSearchFilterToolbar` + `ListFilterPanel`（筛选面板）
- `AuditLogTable` 列配置参考 `templates/governance/audit-log-table.tsx`
- `DataTableCard` + `PaginationBar`（完整列表页壳）

## PRD

`docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S01-common.md#s01-c08`

## Example 路由

`showcase-scenario-audit-log-list`
