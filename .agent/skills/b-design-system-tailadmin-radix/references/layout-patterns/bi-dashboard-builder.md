# 布局模式 — BI 仪表盘构建器

典型路由：`/bi/dashboards`、`/bi/dashboards/:id/edit`、`/bi/dashboards/:id/view`

关联：`dashboard.md`、`chart-theme.md`、`templates/bi/dashboard-grid.tsx`

## 适用场景

- 可编辑仪表盘：拖拽卡片、resize、全局筛选
- 查看模式：只读 + 下钻入口
- 发布预览：edit / preview / view 三模式

## 结构

```tsx
<AppLayout>
  <DashboardToolbar mode={mode} onModeChange={setMode} filters={globalFilters} />
  <FilterBar filters={globalFilters} onChange={setGlobalFilters} />
  <DashboardGrid
    mode={mode}
    items={widgets}
    onLayoutChange={setLayout}
    renderWidget={(item) => (
      <ChartPanel title={item.title} status={item.status} actions={…} />
    )}
  />
</AppLayout>
```

## 三模式

| 模式 | 顶栏 | 网格 | 筛选 |
|---|---|---|---|
| edit | Save / Preview / Publish | 可拖拽 resize handles | 可编辑 |
| preview | Back to edit | 只读，显示发布效果 | 可交互 |
| view | Share / Export | 只读 | 可交互，无编辑入口 |

## 卡片类型

| 类型 | 最小尺寸 | 组件 |
|---|---|---|
| MetricCard | 3×2 grid units | `MetricCard` |
| ChartPanel | 6×4 | `ChartPanel` |
| TableWidget | 6×5 | `DataTableCard` flush |
| TextNote | 3×2 | `Card` + markdown |

## 空态

- 新 dashboard：`ContentState`「Add your first widget」+ 模板库 CTA
- 禁止大面积无意义空白；空槽位显示虚线 placeholder

## 视觉规则

- 栅格 `gap-4`，卡片 `rounded-xl border`
- resize 后内容 `overflow-hidden`，图表 `min-h-0` 自适应
- 全局 FilterBar sticky 在工具栏下，`z-10`
- KPI 行 `grid-cols-2 sm:grid-cols-4`

## 截图验收

- viewer 模式四 KPI + 双图表 + 表格，全宽利用
- builder 模式可见拖拽手柄
- 空 dashboard 有 CTA，非空白
