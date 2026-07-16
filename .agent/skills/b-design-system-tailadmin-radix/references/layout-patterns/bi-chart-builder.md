# 布局模式 — BI 图表构建器

典型路由：`/bi/charts/new`、`/bi/charts/:id/edit`

关联：`bi-dataset-management.md`、`chart-theme.md`、`templates/bi/chart-builder-layout.tsx`

## 适用场景

- 字段拖拽到编码槽位（X / Y / Color / Size / Filter / Sort / Limit）
- 图表类型切换（柱 / 折 / 面积 / 饼 / 雷达 / 漏斗 / 表格）
- 实时预览与查询状态

## 结构

```tsx
<AppLayout>
  <ChartBuilderLayout
    mode="edit"
    fields={fieldGroups}
    chartType={chartType}
    onChartTypeChange={setChartType}
    encodings={encodings}
    onEncodingChange={setEncodings}
    previewStatus={queryStatus}
    preview={<ChartPanel status={queryStatus} chartType={chartType} />}
    configPanel={<ChartConfigPanel encodings={encodings} />}
  />
</AppLayout>
```

## 三栏比例

| 区域 | 宽度 | 内容 |
|---|---|---|
| FieldListPanel | 240–280px | 维度/指标/时间分组 |
| ChartPanel | flex-1 min-w-0 | 预览 + legend/axis |
| ChartConfigPanel | 280–320px | 编码槽位 + 图表选项 |

mobile：降级为分步（选字段 → 选类型 → 预览），不三栏挤压。

## 编码槽位

| 槽位 | 必填 | 说明 |
|---|---|---|
| X | 多数图表 | 维度或时间 |
| Y | 柱/折/面积 | 指标，支持多系列 |
| Color | 可选 | 系列分组 |
| Size | 可选 | 气泡图 |
| Filter | 可选 | 局部筛选 chips |
| Sort | 可选 | asc/desc |
| Limit | 可选 | Top N |

## 预览状态

| 状态 | 表现 |
|---|---|
| loading | ChartPanel 内 Spinner + skeleton axis |
| empty | ContentState「Drag fields to build chart」 |
| error | Alert + Retry + 查询 ID |
| no_permission | 模糊图表 + lock icon |
| data_ready | 完整图表 + legend 不裁切 |

## 视觉规则

- ChartTypePicker 横向图标条，`min-h-[44px]` touch target
- legend 放底部或右侧，长指标名 `truncate` + tooltip
- axis label `text-theme-xs text-gray-500`，旋转 ≤ 45°
- 预览区 `min-h-[360px]`，禁止空框

## 截图验收

- 三栏 builder 占满容器，预览区有 mock 数据柱
- loading/empty/error 至少演示一种
- legend 与 axis 标签无裁切
