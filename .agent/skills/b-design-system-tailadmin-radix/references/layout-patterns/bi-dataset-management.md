# 布局模式 — BI 数据源与数据集管理

典型路由：`/bi/datasources`、`/bi/datasets`、`/bi/datasets/:id/fields`

关联：`master-detail-ops.md`、`data-table-card.tsx`、`templates/bi/dataset-browser.tsx`

## 适用场景

- 数据源连接列表（MySQL / PostgreSQL / ClickHouse / API）
- 连接测试与 schema 加载
- 数据集字段浏览（维度 / 指标 / 时间 / 计算字段）
- 权限拒绝与刷新状态

## 结构

```tsx
<AppLayout>
  <PageHeader title="Datasets" breadcrumbs={…} actions={<Button>Add dataset</Button>} />
  <DatasetBrowser
    datasets={datasets}
    selectedId={selectedId}
    onSelect={setSelectedId}
    connectionStatus={connStatus}
    fields={fields}
    fieldsStatus={fieldsStatus}
  />
</AppLayout>
```

## 连接测试状态

| 状态 | 表现 | 组件 |
|---|---|---|
| idle | Test connection 按钮可点 | `Button variant="outline"` |
| testing | Spinner + disabled | `Spinner` + `aria-busy` |
| success | Badge success + schema loaded | `Badge` + `Alert` |
| error | Alert + Retry + 错误码 | `Alert variant="destructive"` |
| forbidden | 字段值 `•••` + tooltip | `StatMetric status="forbidden"` |

## 字段列表分组

| 分组 | 图标色 | 规则 |
|---|---|---|
| Dimensions | `text-brand-500` | 字符串、枚举、地理 |
| Measures | `text-success-500` | 数值、聚合指标 |
| Time | `text-warning-500` | 日期、时间戳 |
| Calculated | `text-purple-500` | 公式字段，带 `ƒ` 标记 |
| Hidden | `opacity-50` | 默认折叠，可展开 |

## 视觉规则

- 左侧数据集列表 `min-w-[280px] max-w-[34%]`，右侧字段面板全宽
- 字段行 `text-theme-sm`，类型 badge `light` variant
- schema loading 时字段区 Skeleton 行，禁止空白
- permission denied 整页 `ContentState` + 联系管理员 CTA

## 截图验收

- desktop 1440px：列表 + 字段双栏占满宽度
- 连接失败态有明确错误文案，非空框
- 字段类型标签不裁切
