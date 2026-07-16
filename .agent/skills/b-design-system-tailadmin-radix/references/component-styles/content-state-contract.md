# 数据状态与内容契约

技术栈：**React + shadcn/ui + Radix + Tailwind v4**。本文件定义 TailAdmin-Radix 通用后台 **Query Shell**、**DataTableCard**、**KPI 指标** 与 **内容三态/四态** 契约，供列表页、详情页、Hub 页复用。

## 读取顺序

1. `component-index.md` → Data State 行
2. 本文件选能力族
3. 对应 `templates/ui/*.tsx` 可复制模板
4. `state-index.md` 查数据状态覆盖
5. `preview.html#data-state-contract` 视觉验收

## Primary / Secondary Query

| 层级 | 典型用途 | 状态独立 |
|---|---|---|
| **Primary** | 主列表、详情主体、图表序列 | `loading` / `empty` / `error` / `success` |
| **Secondary** | KPI 行、筛选元数据、侧栏摘要 | 可与 primary 不同；`refetching` 常见 |

**规则**：

- Primary `loading`/`pending`：整块替换为骨架或 Spinner，**禁止**空表头下大面积留白。
- Primary `empty`：居中 `ContentState`，最小高度 `min-h-[240px]`，带 CTA。
- Primary `error`：使用 `ErrorState` 三段式（原因 + 下一步 + 可选深链）。
- `refetching`：保留已渲染内容 + 半透明 overlay + 小 Spinner。
- `partial`：顶部 warning banner + 保留 stale 数据。

## Query Shell

**模板**：`templates/ui/query-shell.tsx`

| status | 表现 | 禁止 |
|---|---|---|
| `pending` / `loading` | 居中 Spinner 或 skeleton | 空白卡片 |
| `empty` | `ContentState` empty + CTA | 全宽无内容 |
| `error` | `ErrorState` | 仅 toast 无内联 |
| `success` | 渲染 children | — |
| `refetching` | children + overlay | 整页闪烁 |
| `partial` | banner + children | 静默失败 |

```tsx
<QueryShell
  status={query.status}
  secondaryStatus={kpiQuery.status}
  emptyTitle="No endpoints yet"
  emptyAction={<Button>Add endpoint</Button>}
  error={{
    reason: "Failed to load endpoints",
    nextStep: "Check network or retry in a moment.",
    primaryAction: { label: "Retry", onClick: () => refetch() },
    deepLink: { label: "View status page", href: "/status" },
  }}
>
  <DataTable>...</DataTable>
</QueryShell>
```

## ContentState / ErrorState

**模板**：`templates/ui/content-state.tsx`

| variant | 图标 | 场景 |
|---|---|---|
| `loading` | Spinner | 内联块级加载 |
| `empty` | Inbox | 无数据 |
| `error` | AlertCircle | 接口失败 |
| `forbidden` | Lock | 无权限 |
| `partial` | RefreshCw | 局部刷新提示 |

### 错误文案结构

1. **用户可读原因**（`reason` / title）— 不用 HTTP 码作为主文案
2. **下一步动作**（`nextStep` / description）— Retry、检查配置、联系管理员
3. **可选深链**（`deepLink`）— 状态页、文档、工单

## DataTableCard

**模板**：`templates/ui/data-table-card.tsx`

| 区域 | 规则 |
|---|---|
| Header | `CardTitle` + 可选 `CardAction`（Add / Import） |
| Toolbar | Search `max-w-xs` + Filter / Export outline |
| Bulk bar | 选中后 `bg-brand-50` 条 + destructive outline |
| Table body | **flush** `CardContent p-0`；表头 `bg-gray-50 dark:bg-white/[0.02]` |
| Footer | Pagination 或 row count |
| Dense | `dense` prop 缩小 `th/td` padding |

**禁止**：表格外再套 `rounded-xl border` 造成双层表头（见 `gateway-visual.md`）。

```tsx
<DataTableCard
  title="API Keys"
  status={listQuery.status}
  selectedCount={selection.length}
  bulkActions={<Button variant="destructive">Revoke</Button>}
  footer={<Pagination>...</Pagination>}
>
  <Table>...</Table>
</DataTableCard>
```

## StatMetric（KPI）

**模板**：`templates/ui/stat-metric.tsx`

| status | 展示 | 说明 |
|---|---|---|
| `ready` | 数值 + 可选 delta | `tabular-nums` |
| `loading` | Skeleton | 不显示 0 |
| `zero` | 灰色 `0` | 真实零值，非错误 |
| `error` | `—` 红色 | 指标拉取失败 |
| `forbidden` | `•••` | 无权限掩码 |
| `partial` | 数值 + 小 Spinner | 后台刷新 |

## 与布局模式联动

- 列表页：`layout-patterns/table-list.md` + `DataTableCard`
- 运维 Hub：`ops-monitoring.md` + KPI 行 `StatMetric` + `QueryShell`
- 详情页：主区 primary query；侧栏 summary secondary query

## Preview 验收

- section：`preview.html#data-state-contract`
- 截图：`preview-screenshots/data-state-*.png`
- 必含：empty（无大面积空白）、error（Retry）、loading skeleton、DataTableCard toolbar + bulk bar

## 源采样

- `tables/DataTables/*` — 高密度表格与分页
- `tables/BasicTables/*` — 空态居中
- Gateway 需求：三态契约、列表 Hub 全宽
