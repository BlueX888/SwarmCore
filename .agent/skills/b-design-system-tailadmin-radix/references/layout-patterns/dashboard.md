# 布局模式 — Dashboard

典型路由：`/`、`/analytics`、`/crm`、`/saas`

## 结构

```tsx
<AppLayout>
  {/* 可选：PageMeta title */}
  <div className="grid gap-6">
    {/* Row 1: 指标卡 */}
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard />
    </div>
    {/* Row 2: 主图表 + 侧图 */}
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <ComponentCard className="xl:col-span-2">{/* Chart */}</ComponentCard>
      <ComponentCard>{/* Secondary */}</ComponentCard>
    </div>
    {/* Row 3: 表格 */}
    <ComponentCard title="Recent Orders">
      <Table />
    </ComponentCard>
  </div>
</AppLayout>
```

## 指标卡

- `ComponentCard` 或轻量 `rounded-xl border p-5`
- 标签 `text-theme-sm text-gray-500`
- 数值 `text-title-sm font-semibold`
- 环比 Badge `light` variant success/error

## 图表

- 容器：`ComponentCard` + `min-h-[300px]`
- 主题：`references/component-styles/chart-theme.md` · `templates/lib/chart-theme.ts`
- ApexCharts 色板：`brand-500`、`theme-purple-500`、`success-500`
- tooltip/grid 暗色 CSS 见 `chart-theme.md#dark-mode-css`

## 密度

- 区块间距 `gap-6`
- 卡内 chart padding `p-6`
- 移动端指标卡 1 列 → `sm` 2 列 → `xl` 4 列

## 组件清单

Button · Badge · ComponentCard · Table · Chart wrapper · Tabs（可选 ChartTab）
