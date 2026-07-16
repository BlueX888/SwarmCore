# 布局模式 — BI 数据大屏

典型路由：`/bi/screens/:id`、`/bi/screens/:id/preview`

关联：`ops-monitoring.md`、`chart-theme.md`、`templates/bi/data-screen-canvas.tsx`、`templates/bi/screen/` Layer0 主题

## Layer0 路径（G128+）

| 路径 | 说明 |
|------|------|
| `templates/bi/screen/theme/screen-tokens.ts` | 面板背景、边框发光、字号阶梯 |
| `templates/bi/screen/theme/chart-theme-screen-dark.ts` | ApexCharts 深色大屏主题 |
| `templates/bi/screen/theme/chart-theme-screen-light.ts` | L4 浅色大屏主题 |
| `templates/bi/screen/screen-shell.tsx` | 16:9 画布壳 + 时钟 + 刷新徽章 |

**禁止**在 scenario 页面内联 Apex `colors: ['#xxx']`；必须经 `applyScreenChartTheme`。

## 适用场景

- 驾驶舱、能源、园区、交通、生产监控全屏大屏
- 固定画布比例（16:9、1920×1080、超宽屏）
- 缩放预览、自动刷新、地图/KPI/轮播

## 结构

```tsx
<DataScreenCanvas
  aspectRatio="16:9"
  scaleMode="fit"
  theme="dark"
  refreshStatus={{ lastAt, interval, state }}
>
  <DataScreenHeader title="Operations Cockpit" />
  <div className="grid grid-cols-12 grid-rows-6 gap-3 p-4">
    <BigNumberTile colSpan={3} … />
    <GeoMapPanel colSpan={6} rowSpan={4} fallback="mock" />
    <ChartPanel colSpan={3} … />
  </div>
  <RefreshStatusBadge />
</DataScreenCanvas>
```

## 画布比例

| 比例 | 基准 | 用途 |
|---|---|---|
| 16:9 | 1920×1080 | 标准大屏 |
| 21:9 | 2560×1080 | 超宽指挥席 |
| 32:9 | 3840×1080 | 三联屏 |

缩放预览：`transform: scale()` 居中，`transform-origin: center top`。

## 组件

| 组件 | 说明 |
|---|---|
| `BigNumberTile` | 大数字 + 单位 + 同比箭头 |
| `GeoMapPanel` | 区域热力 / 点位 / 飞线，无数据时 mock 水印 |
| `ChartPanel` | 深色背景适配，grid 线 `opacity-20` |
| `RefreshStatusBadge` | 上次刷新 + 倒计时 + 失败态 |

## 视觉规则

- 深色大屏背景 `#0f172a` 层级，非纯黑炫光
- 数值 `text-title-lg font-bold tabular-nums`
- 地图无真实数据：`GeoMapPanel fallback="mock"` + 「Sample data」水印
- 标签 `text-theme-xs`，对比度 ≥ 4.5:1

## 截图验收

- 16:9 画布完整 framing，无裁切
- KPI 数字、图例、地图标注可读
- mock 数据有明确 fallback 标记
