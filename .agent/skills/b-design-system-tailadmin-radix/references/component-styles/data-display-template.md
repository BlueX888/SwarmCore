# Data Display — Table / Card / Progress

## Table

**Primitives**：`ui/table/index.tsx`  
**页面模式**：`tables/BasicTables/BasicTableOne.tsx`

```tsx
// wrapper: overflow-hidden rounded-xl border border-gray-200 bg-white
//          dark:border-white/[0.05] dark:bg-white/[0.03]
// thead th: px-5 py-3 text-theme-xs font-medium text-gray-500
// tbody td: px-5 py-4 text-theme-sm text-gray-800 dark:text-white/90
// tbody tr: divide-y divide-gray-100 dark:divide-white/[0.05]
```

shadcn `Table` + 上述 className 在 `TableHeader`/`TableCell`。

可复制模板：`templates/ui/table.tsx`（含 wrapper `rounded-xl border`）

复选框列：自定义 `tableCheckbox` 样式（见 `index.css`）或 shadcn `Checkbox`。

## ComponentCard

**源**：`common/ComponentCard.tsx`

- 外框：`rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]`
- 标题区：`px-6 py-5` + 可选右侧 actions（`CardAction`）
- 内容：`p-6 pt-0`（`CardContent`）
- 页脚：`border-t border-gray-100 px-6 py-4`（`CardFooter`）

可复制模板：`templates/ui/card.tsx`（含 Card、CardHeader、CardTitle、CardDescription、CardAction、CardContent、CardFooter）

Card 表面变体：

- `variant`: elevated | outlined（默认 outlined）
- `elevation`: 0 | 1 | 2 | 4 | 8（映射 `shadow-theme-xs/sm/md/lg`）
- `square`: 直角卡片

**`.card-surface` utility**（替代历史 `card-glass` / `gradient-hero` 默认卡片）：

```css
@layer utilities {
  .card-surface {
    border: 1px solid var(--gray-200);
    background: var(--white);
    box-shadow: var(--shadow-theme-xs);
  }
  .dark .card-surface {
    border-color: color-mix(in srgb, white 5%, transparent);
    background: color-mix(in srgb, white 3%, transparent);
  }
  .card-surface--interactive:hover {
    box-shadow: var(--shadow-theme-sm);
  }
}
```

列表页 Card 工具栏 + flush table：`Card` 根节点加 `card-surface overflow-hidden rounded-xl`，`CardContent p-0`。

用作仪表盘区块、表单分组、图表容器。

## ProgressBar

**源**：`ui/progressbar/ProgressBar.tsx`

- 轨道：`h-2 rounded-full bg-gray-200 dark:bg-gray-800`
- 填充：`bg-brand-500 rounded-full` + `transition-all duration-300`
- shadcn `Progress` + `className` 覆盖

可复制模板：`templates/ui/progress.tsx`（Radix `@radix-ui/react-progress` + `value` prop）

preview 对齐：`preview.html` Data Display 卡片（62% / 38% / 100% 进度条 + `role="progressbar"`）。

## Stat 指标卡

**模板**：`templates/ui/stat-metric.tsx`  
**契约**：`content-state-contract.md#statmetrickpi`

| status | 展示 |
|---|---|
| ready | 数值 + delta |
| loading | Skeleton |
| zero | 灰色 `0` |
| error | `—` |
| forbidden | `•••` |
| partial | 数值 + Spinner |

数字：`text-title-sm font-semibold tabular-nums text-gray-800 dark:text-white/90`  
标签：`text-theme-sm text-gray-500`  
变化率：success/error 色 + 箭头图标

## DataTableCard

**模板**：`templates/ui/data-table-card.tsx`  
**契约**：`content-state-contract.md#datatablecard`

- flush 表格、`QueryShell` 内联三态
- toolbar / bulk / pagination 见 `table-list.md`
- 内置 `DataTable` 编排：传入 `columns` + `dataSource` 时自动渲染表格；`rowSelection` / `expandable` / `onTableChange` / `showSizeChanger` 透传

## DataTable 编排契约 {#datatable-contract}

**模板**：`templates/ui/data-table.tsx`（编排层）· `templates/ui/table.tsx`（primitives）

`onChange` 统一 payload：

```tsx
type DataTableChangePayload = {
  pagination: { current: number; pageSize: number; total?: number };
  filters: Record<string, unknown>;
  sorter: { field: string; order: "asc" | "desc" } | null;
};
```

| 能力 | props | 说明 |
|---|---|---|
| 行选择 | `rowSelection` | `checkbox` 全选/半选；`radio` 单选 |
| 展开行 | `expandable` | `expandedRowRender` + `expandedKeys` |
| 分页联动 | `pagination` + `onChange` | 排序/分页变化均回调 `onChange` |
| 汇总行 | `summary` | `TableSummary` 行组件 |
| 列头筛选 | `columns[].filter` / `filteredValue` | select / text Popover；见 `#datatable-column-filter` |
| 尺寸/变体 | `size` / `variant` / `stickyHeader` | 透传 Table primitives |

```tsx
<DataTableCard
  title="租户列表"
  columns={columns}
  dataSource={rows}
  rowSelection={{
    type: "checkbox",
    selectedKeys,
    onChange: setSelectedKeys,
    getRowKey: (row) => row.id,
  }}
  pagination={{ current: 1, pageSize: 20, total: 128 }}
  showSizeChanger
  onTableChange={({ pagination }) => setPage(pagination.current)}
/>
```

## DataTable 列头筛选 {#datatable-column-filter}

**模板**：`templates/ui/data-table-column-filter.tsx` · 集成于 `templates/ui/data-table.tsx`

antd `Table.filterDropdown` 等价。

| prop | 类型 | 说明 |
|---|---|---|
| `filter` | `ColumnFilterConfig` | `{ type: "select", options }` 或 `{ type: "text", placeholder? }` |
| `filteredValue` | `unknown?` | 受控筛选值 |
| `onChange` payload.filters | `Record<string, unknown>` | 列 key → 筛选值 |

Filter 图标 active 时 `text-brand-500`；Popover 内 Apply 触发 `onApply`。

**约束**：`virtual={true}` 时列 filter 被忽略并 `console.warn` — 大数据列表用 toolbar 全局筛选。

```tsx
const columns = [
  { key: "status", title: "状态", filter: { type: "select", options: [{ label: "启用", value: "on" }] } },
  { key: "name", title: "名称", filter: { type: "text", placeholder: "搜索名称" } },
];
```

## TreeTable {#treetable}

**模板**：`templates/ui/tree-table.tsx` · 内核 `templates/lib/flatten-tree-rows.ts` · 页壳 `layout-patterns/tree-table.md`

PrimeVue TreeTable / antd 层级资源表对标。

| prop | 说明 |
|---|---|
| `dataSource` | `HierarchicalNode[]` |
| `columns` | 与 DataTable 同构；树名列可用 `treeColumnTitle` |
| `expandedKeys` / `checkable` / `loadData` | 复用 hierarchical-picker 语义 |
| `pagination` / `onChange` | 对扁平可见行分页 |

**约束**：F1 不含 virtual / 列头 filter；与 `rowSelection` 和 `checkable` 互斥时 rowSelection 优先。

## StatTrend {#stattrend}

**模板**：`templates/ui/stat-trend.tsx` · 组合：`StatMetric` `trend` slot

| prop | 类型 | 说明 |
|---|---|---|
| `direction` | `"up" \| "down" \| "flat"` | 涨跌/持平 |
| `value` | `ReactNode` | 如 `+12.5%`、`-3` |

语义色：`up` → success-500；`down` → error-500；`flat` → gray-500。

```tsx
<StatMetric label="月活用户" value="12,480" trend={<StatTrend direction="up" value="+8.2%" />} />
```

## ImagePreview {#imagepreview}

**模板**：`templates/ui/image-preview.tsx`

antd `Image.preview` 等价 — 缩略图点击打开 Dialog 大图。

| prop | 类型 | 说明 |
|---|---|---|
| `src` / `alt` | `string` | 图片地址与替代文本 |
| `preview` | `boolean?` | 是否可点击灯箱；默认 `true` |
| `fallback` | `ReactNode?` | 加载失败占位 |
| `thumbnailClassName` | `string?` | 缩略图尺寸/圆角 override |

缩略图默认 `size-12 rounded-lg`；大图 `max-h-[min(80vh,720px)] object-contain`。

## Transfer {#transfer}

**模板**：`templates/ui/transfer.tsx`

| prop | 类型 | 说明 |
|---|---|---|
| `dataSource` | `TransferItem[]` | 候选集 `{ key, title, description?, disabled? }` |
| `targetKeys` / `onChange` | `string[]` | 受控右侧 key 列表 |
| `titles` | `[string, string]?` | 双栏标题 |
| `showSearch` | `boolean?` | 栏内搜索 |
| `oneWay` | `boolean?` | 单向穿梭（隐藏移回） |
| `render` | `(item) => ReactNode?` | 自定义行渲染 |

## Timeline {#timeline}

**模板**：`templates/ui/timeline.tsx`

| prop | 类型 | 说明 |
|---|---|---|
| `items` | `TimelineItem[]` | `{ id, title, description?, timestamp?, icon?, status? }` |
| `mode` | `"left" \| "alternate" \| "right"?` | 时间轴布局；默认 `left` |
| `pending` | `ReactNode?` | 末尾 pending 节点文案 |
| `size` | `"sm" \| "md"?` | 密度；默认 `md` |

status 映射：`default` / `success` / `error` / `warning` / `pending`（pending 内嵌 Spinner）。

领域包装：`ApprovalTimeline` 将审批事件映射为 `TimelineItem` 后渲染 `<Timeline size="sm" />`。

## List {#list}

**模板**：`templates/ui/list.tsx`

| prop | 类型 | 说明 |
|---|---|---|
| `density` | `"comfortable" \| "compact"?` | 行高；默认 `comfortable` |
| `divided` | `boolean?` | 行间 `Separator` |

Slot 导出：`List` / `ListItem` / `ListItemIcon` / `ListItemText` / `ListItemTrailing`。

`ListItem` 支持 `onClick`、`destructive`；尾部 Switch 等放 `ListItemTrailing`。

## Query Shell / Content State

**模板**：`templates/ui/query-shell.tsx` · `templates/ui/content-state.tsx`  
**契约**：`content-state-contract.md`
