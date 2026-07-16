# 布局模式 — Table List（ListSearchFilterToolbar）

典型路由：`/products-list`、`/invoices`、`/support-tickets`

关联：`data-display-template.md` · `content-state-contract.md` · `list-search-filter-toolbar.md`

## 工具栏契约（2026-06+）

| 区域 | 内容 |
|------|------|
| 左 | `ListSearchInput`（300ms debounce + Enter 立即搜索）+ 可选 `ListFilterPanel`（筛选图标 suffix + 活跃数角标） |
| 右 | 主操作（新建 / 导出等 `Button`） |
| 卡片底 | `Pagination` / `PaginationBar` |
| 卡片上横幅（可选） | 只读提示、分组 Tabs 等 — **禁止**与 inline 多 Select 混用 |

**禁止**在列表工具栏 inline 堆叠多个 `Label + Select`；筛选字段放入 Popover（≤3 字段）或 Drawer（复杂）。

## 结构

```tsx
<AppLayout>
  <div className="flex flex-col gap-6">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-xl font-semibold text-gray-800 dark:text-white/90">Products</h1>
        <p className="text-theme-sm text-gray-500">Manage catalog</p>
      </div>
    </div>

    <Card className="card-surface overflow-hidden rounded-xl">
      <CardContent className="p-0">
        <div className="flex items-center justify-between gap-2 border-b border-gray-200 px-4 py-3 dark:border-gray-800">
          <ListSearchFilterToolbar
            search={{
              placeholder: "搜索...",
              value: searchDraft,
              onChange: setSearchDraft,
              onSearch: (q) => { setAppliedQuery(q); setPage(1); },
            }}
            filter={{
              fields: STATUS_FIELDS,
              values: appliedFilters,
              panel: "popover",
              onApply: (v) => { setAppliedFilters(v); setPage(1); },
            }}
          />
          <Button variant="primary">新建</Button>
        </div>
        <QueryShell status={query.status}>
          <Table>...</Table>
        </QueryShell>
        <div className="border-t border-gray-200 px-4 py-3 dark:border-gray-800">
          <Pagination />
        </div>
      </CardContent>
    </Card>
  </div>
</AppLayout>
```

## 筛选面板选型

| 场景 | `panel` | Sheet 配置 |
|------|---------|------------|
| 1–3 个字段（状态、格式） | `popover` | — |
| 4+ 字段或工作项多维筛选 | `drawer` | `modal={false}` + `showOverlay={false}`（列表背景保持可见） |

点「应用」后才更新 query key / API 参数；「重置」清空 draft，「取消」关闭不提交。

## 表格样式

见 `data-display-template.md#table`

## 分页

**源**：`ui/pagination/PaginationWithIcon.tsx`

- 当前页：`bg-brand-500 text-white rounded-lg`
- 其他：`text-gray-700 hover:bg-gray-100`

## 数据状态（Query Shell）

列表页必须使用 `QueryShell` + `DataTableCard`（或等价 Table 壳），禁止裸 Table 无状态处理。

| 状态 | 表现 |
|---|---|
| loading | `QueryShell status="loading"` 或表内 Skeleton 行 |
| empty | `ContentState` 居中，`min-h-[240px]`，带 CTA |
| error | `ErrorState`：原因 + Retry + 可选深链 |
| refetching | 保留表格 + 半透明 overlay |

契约详情：`component-styles/content-state-contract.md`

## DataTableCard

**模板**：`templates/ui/data-table-card.tsx`

- Header：标题 + 右侧 Add/Import（或外层 Card 工具栏）
- Toolbar：优先 `ListSearchFilterToolbar` + actions
- Bulk bar：选中后 `bg-brand-50` 条
- Table：**flush** `CardContent p-0`，禁止双层表头边框
- Footer：Pagination

```tsx
<DataTableCard title="Invoices" status={query.status} footer={<Pagination />}>
  <Table>...</Table>
</DataTableCard>
```

## 空态

无数据时使用 `QueryShell` + `ContentState`，**禁止**大面积无意义空白：

```tsx
<QueryShell
  status="empty"
  emptyTitle="No items yet"
  emptyAction={<Button variant="primary">Create first</Button>}
/>
```

## 批量选择

表头 Checkbox + 选中后 `DataTableCard` bulk bar 显示批量操作（outline + destructive）。

## 模板文件

| 文件 | 说明 |
|------|------|
| `templates/ui/list-search-filter-toolbar.tsx` | 工具栏组合 |
| `templates/ui/list-search-input.tsx` | debounce 搜索框 |
| `templates/ui/list-filter-panel.tsx` | Popover / Drawer 筛选 |
| `templates/ui/list-filter-types.ts` | 声明式配置类型 |
| `templates/ui/list-filter-utils.ts` | 活跃筛选计数 |
| `templates/lib/use-debounced-value.ts` | 搜索 debounce hook |

复制到项目时放入 `components/ui/` 或 `components/devops/`（保持 `@/` 路径一致）。
