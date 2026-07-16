# 布局模式 — BI 下钻、钻取与明细查看

典型路由：`/bi/dashboards/:id/view`、`/bi/explore/drill`

关联：`bi-filter-linkage.md`、`bi-dashboard-builder.md`、`templates/bi/drill-breadcrumb.tsx`、`templates/bi/drill-detail-table.tsx`、`templates/bi/drill-down-dashboard.tsx`

## 适用场景

- **Drill down**：在同一仪表盘内，点击图表扇区/柱子进入更细粒度维度或明细表
- **Drill through**：从汇总图表跳转到独立明细页或 Drawer，保留筛选上下文
- **查看明细**：订单明细、交易流水、日志条目等行级数据
- **面包屑返回**：逐级返回汇总视图，global/cross-filter 不丢失

## 下钻路径模型

| 层级 | 视图 | 触发 | 面包屑示例 |
|---|---|---|---|
| L0 | 仪表盘汇总 | 初始 | 经营分析仪表盘 |
| L1 | 维度下钻 | 点击图表柱子/扇区 | 经营分析 > 华东区 |
| L2 | 明细表 | 点击「查看明细」或二次下钻 | 经营分析 > 华东区 > 订单明细 |

**筛选上下文保留规则**：

- Global / Cross-filter chips 在 drill 全程可见（FilterBar sticky）
- 下钻仅追加 `DrillBreadcrumb` 层级，不重置 global 筛选
- 返回上一级时，恢复该层图表状态与 local 筛选默认值
- Drill through 外链/新页时，URL query 携带 `filters` 序列化参数

## 结构

```tsx
<DrillDownDashboard
  title="经营分析"
  filterChips={chips}
  breadcrumb={drillPath}
  view="chart" // chart | detail
  onDrill={(payload) => pushDrillLevel(payload)}
  onBreadcrumbNavigate={(level) => popToLevel(level)}
  renderChart={() => <ChartPanel … />}
  renderDetail={() => (
    <DrillDetailTable
      columns={columns}
      rows={rows}
      status="success"
      onExport={handleExport}
    />
  )}
/>
```

或组合式：

```tsx
<DrillBreadcrumb items={path} onNavigate={setLevel} />
<FilterBar chips={allChips} … />
{view === "chart" ? <DashboardGrid … /> : <DrillDetailTable … />}
```

## 明细表能力

| 能力 | 说明 |
|---|---|
| 分页 | 服务端分页 preferred；页码 + 每页条数 + 总数 |
| 导出 | CSV/Excel；exporting / queued / failed / ready 状态 |
| 字段隐藏 | 列显隐菜单，至少保留 1 列可见 |
| 权限错误 | `status="forbidden"` + 申请权限入口 |
| 空态 | 当前筛选无明细 + 建议放宽筛选 |
| 加载/错误 | QueryShell loading / error + retry |

## 交互模式

1. **Chart click → L1**：高亮选中扇区，面包屑追加维度值，KPI 重算
2. **「查看明细」→ L2**：切换 `view="detail"`，表格继承 L0+L1 筛选
3. **面包屑点击**：pop 到指定层级，detail 切回 chart 若目标非 L2
4. **Drill through**：行内「详情」跳转 MasterDetail 或新 Tab，query 带 filters

## 视觉规则

- `DrillBreadcrumb` 在 FilterBar 上方或标题行内，`text-theme-sm`，末级 `font-medium`
- 图表下钻态：选中扇区 `ring-2 ring-brand-500`，其他扇区 `opacity-60`
- 明细表使用 `DataTableCard` flush 模式，toolbar 含搜索 + 导出 + 列设置
- 移动端：面包屑可折叠为「← 返回上一级」+ 当前层级标题

## 选型（decision-matrix）

| 意图 | 使用 | 不要用 |
|---|---|---|
| 图表点击看更细汇总 | `DrillDownDashboard` view=chart | 直接跳明细表丢上下文 |
| 行级明细 | `DrillDetailTable` | 普通 Table 无分页导出 |
| 下钻路径导航 | `DrillBreadcrumb` | 仅浏览器后退 |
| 跨页明细 | Drill through + URL filters | 手写 state 无恢复 |
| CRUD 列表 | `DataTableCard` | BI DrillDetailTable |

## 截图验收

- 仪表盘 + 点击下钻后面包屑 L1
- 明细表 view + 分页 + 导出按钮
- 面包屑返回后图表与筛选恢复
- light/dark 下面包屑与表格可读
