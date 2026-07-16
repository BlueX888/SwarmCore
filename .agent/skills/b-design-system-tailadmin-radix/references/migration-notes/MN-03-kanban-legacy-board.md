# MN-03 — Kanban 自建板迁移演练

## 元信息

```yaml
component: KanbanBoard
change_type: behavior-change
severity: additive-deprecation
introduced_in: G48-COMPAT-003
compat_until: G50
status: active
scenario_ref: MS-03
```

## 变更摘要

G33 前业务项目可能仅用 `kanban-theme.ts` class 常量自建 DnD 列板。本轮提供 `KanbanLegacyShell` deprecated wrapper，在保留 theme class 的同时引导迁移到受控 `KanbanBoard` API。

## 旧用法

```tsx
import { kanbanBoardGridClass, kanbanColumnClass } from "@/lib/kanban-theme";

<div className={kanbanBoardGridClass}>
  {columns.map((col) => (
    <div key={col.id} className={kanbanColumnClass}>
      {/* 自建卡片 DOM + 手写 DnD */}
    </div>
  ))}
</div>
```

## 新用法

```tsx
import { KanbanBoard, type KanbanColumnData } from "@/components/ui/kanban-board";

<KanbanBoard
  columns={columns}
  onTaskMove={handleMove}
  onColumnAction={handleColumnAction}
/>
```

过渡 wrapper（保留 theme class，受控数据）：

```tsx
import { KanbanLegacyShell } from "@/components/ui/deprecated/kanban-legacy-shell";

<KanbanLegacyShell columns={columns} onTaskMove={handleMove} />
```

## Deprecated Wrapper

```tsx
// templates/ui/deprecated/kanban-legacy-shell.tsx
/** @deprecated 迁移至 KanbanBoard。兼容至 G50，见 MN-03 */
export function KanbanLegacyShell(props: KanbanBoardProps) {
  return <KanbanBoard {...props} />;
}
```

## 影响范围

| 区域 | 是否受影响 | 说明 |
|---|---|---|
| `templates/ui/kanban-board.tsx` | no | API stable |
| `templates/ui/deprecated/` | yes | KanbanLegacyShell |
| `templates/lib/kanban-theme.ts` | no | class 常量仍 stable |
| `preview.html` | no | 已用 KanbanBoard |
| 业务 vendored copy | yes | 自建 DnD 常见 |

## 兼容期与回滚

- **兼容期**：`kanban-theme.ts` 全部 class 常量保持 stable；wrapper 引导至 G50。
- **回滚**：继续使用 theme class 自建 DOM。
- **检测**：`audit_migration_drills.py` + KanbanBoard template 存在性。

## 验证清单

- [x] `KanbanLegacyShell` wrapper 转接 KanbanBoard
- [x] `kanban-theme.ts` class 常量未删除
- [x] `api-contracts.md` Kanban 风险表已引用 MN-03
- [x] `migration-scenarios.md` MS-03 已链接 MN-03
- [x] `scorecard.md` 反向审计已记录
