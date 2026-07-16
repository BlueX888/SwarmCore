# 布局模式 — BI 语义层与指标口径

典型路由：`/bi/semantic/metrics`、`/bi/semantic/dimensions`、`/bi/semantic/metrics/:id`

关联：`bi-dataset-management.md`、`bi-chart-builder.md`、`templates/bi/metric-definition-panel.tsx`

## 适用场景

- 指标、维度、计算字段的统一口径管理
- 公式、聚合、单位、粒度、owner 与变更影响范围展示
- 口径冲突、废弃、待审核状态可视化
- 避免多个图表重复定义同一业务指标

## 结构

```tsx
<AppLayout>
  <PageHeader
    title="指标口径"
    breadcrumbs={…}
    actions={<Button>新建指标</Button>}
  />
  <MetricDefinitionPanel
    metrics={metrics}
    dimensions={relatedDimensions}
    selectedMetricId={selectedId}
    onSelectMetric={setSelectedId}
    onReview={handleReview}
  />
</AppLayout>
```

## 指标生命周期状态

| 状态 | Badge | 表现 |
|---|---|---|
| active | default / 已发布 | 可被图表引用，公式只读或受控编辑 |
| draft | secondary / 草稿 | 未发布，影响范围为 0 |
| pending_review | outline / 待审核 | 显示审核 CTA，禁止下游引用 |
| deprecated | secondary / 已废弃 | 灰色文案 + 替代指标链接 |
| conflict | destructive / 口径冲突 | `Alert variant="warning"` + 合并建议 |

## 定义字段

| 字段 | 规则 |
|---|---|
| name | 技术标识，snake_case，全局唯一 |
| displayName | 中文业务名，列表主标题 |
| formula | 等宽字体块，支持 `SUM()`、`COUNT(DISTINCT …)` |
| aggregation | sum / avg / count / max / min / custom |
| unit | 元、%、次、ms 等 |
| granularity | 日 / 周 / 月 / 实时 |
| owner | 口径负责人或团队 |
| impactedCharts | 变更前必须展示影响图表数 |

## 维度关联

- 指标详情底部展示关联维度 Badge 列表
- 维度定义复用 `FieldListPanel` 的分组色：Dimensions / Measures / Time
- 计算维度带 `ƒ` 标记

## 视觉规则

- 左侧指标目录 `min-w-[280px] max-w-[34%]`，右侧详情全宽
- 公式块 `rounded-lg bg-gray-50 font-mono`，禁止裁切长公式
- conflict / pending_review 必须在首屏可见 Alert 或 Badge
- 废弃指标列表项 `opacity-60`，但仍可点击查看历史口径

## 与 Chart Builder 关系

- Chart Builder 的 Measures 槽位应引用语义层 `metricId`，而非重复输入聚合
- 口径变更时，关联图表显示「待刷新」状态（见 BI-006 联动）

## 截图验收

- desktop 1440px：目录 + 详情双栏占满宽度
- 待审核、口径冲突态有明确 Badge 与 Alert
- 公式块与影响范围文案不被裁切
