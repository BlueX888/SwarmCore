# DataView 资源墙

grid / list 切换 + 分页的标准组合（对标 PrimeVue DataView）：

```
PageHeader
├── SegmentedControl（grid | list）
├── FilterBar（可选）
├── grid 模式：Card 网格 + Masonry（可选）
├── list 模式：DataTable 或 DataTableCard
└── PaginationBar
```

## 示例组合

| 模式 | 组件 |
|---|---|
| 卡片墙 | `Masonry` + `MetricCard` / 自定义 Card |
| 列表 | `DataTableCard` + `rowSelection` |
| 切换 | `SegmentedControl` 受控 `layout` state |

## 决策

- 需要列排序/筛选 → list 模式用 `DataTable`
- 纯视觉资源浏览 → grid + `Masonry`
- 与 BI 仪表盘区分：DataView 偏 **PaaS 资源目录**，非图表联动
