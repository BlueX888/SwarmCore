# Chart 主题 — ApexCharts

独立 Chart 主题 shard。源：`components/charts/bar/BarChartOne.tsx`、`index.css` `.apexcharts-*`。

可复制模板：`templates/lib/chart-theme.ts`

## 检索别名

| 意图 | 读本节 |
|---|---|
| 柱状图主题 | `#bar-chart` |
| 折线图主题 | `#line-chart` |
| 环形图主题 | `#donut-chart` |
| 暗色 tooltip/grid | `#dark-mode-css` |
| 加载/空态/错误 | `#data-states` |
| 容器布局 | `#chart-container` |

## 色板

对齐 `token-index.md` 与 example app / 宿主项目 `:root` CSS 变量：

| Token | Hex | CSS 变量 | 用途 |
|---|---|---|---|
| brand-500 | `#465fff` | `--brand-500` | 主系列 |
| theme-purple-500 | `#7a5af8` | `--purple-500` | 次系列 |
| success-500 | `#12b76a` | `--success-500` | 正向指标 |
| blue-light-500 | `#0ba5ec` | `--blue-light-500` | 信息系列 |
| theme-pink-500 | `#ee46bc` | — | 强调系列 |

```ts
import {
  chartColors,
  chartPalette,
  chartPaletteCssVars,
  getBaseChartOptions,
  createBarChartOptions,
} from "@/lib/chart-theme";
```

### CSS Variables

ApexCharts options 需 hex 常量（`chartPalette`）；纯 CSS/HTML mock 使用 `chartPaletteCssVars`：

```ts
// CSS mock / Tailwind arbitrary: chartPaletteCssVars.brand → var(--brand-500)
const barColor = chartPaletteCssVars.purple;
```

宿主项目应在 `@theme` 或 `:root` 定义与 `token-index.md` 一致的变量；`examples/b-design-system-tailadmin-radix` 为参考实现。

## Bar Chart

源默认：`columnWidth: "39%"`、`borderRadius: 5`、`toolbar: false`、`height: 180`。

```tsx
import Chart from "react-apexcharts";
import { createBarChartOptions } from "@/lib/chart-theme";

const options = createBarChartOptions([
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]);

const series = [{ name: "Sales", data: [168, 385, 201, 298, 187, 195, 291, 110, 215, 390, 280, 112] }];

<ComponentCard title="Monthly Sales">
  <div className="min-h-[180px] overflow-x-auto custom-scrollbar">
    <div className="min-w-[1000px]">
      <Chart options={options} series={series} type="bar" height={180} />
    </div>
  </div>
</ComponentCard>
```

## Line Chart

```tsx
import { createLineChartOptions } from "@/lib/chart-theme";

const options = createLineChartOptions(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], {
  stroke: { curve: "smooth", width: 2 },
});
```

- 多系列时 `colors` 自动取 `chartColors` 前 N 项
- 面积填充可选 `fill: { type: "gradient", gradient: { opacityFrom: 0.35, opacityTo: 0.05 } }`

## Donut Chart

```tsx
import { createDonutChartOptions } from "@/lib/chart-theme";

const options = createDonutChartOptions();
const series = [44, 55, 13, 33];
```

- `plotOptions.pie.donut.size: "70%"`
- 中心 total label 使用 `text-gray-500` / `text-gray-900`

## Chart Container

- 外包 `ComponentCard`（`rounded-2xl border-gray-200 p-6`）
- 图表区 `min-h-[180px]`–`min-h-[320px]`
- 宽表格类图表：`overflow-x-auto` + 内层 `min-w-[1000px]`
- 卡内标题 `text-theme-sm font-medium text-gray-800`

见 `layout-patterns/dashboard.md`。

## Dark Mode CSS

`tooltip.theme: "light"` 固定；暗色由 CSS 覆盖。复制 `templates/lib/chart-theme.ts` 中 `apexChartsCssOverrides` 到宿主 `src/index.css`：

- tooltip：`rounded-lg border-gray-800 bg-gray-900 shadow-theme-sm`
- gridline：`stroke-gray-800`
- legend/text：`fill-gray-400` / `text-gray-400`

源证据：TailAdmin React Pro v2.3.1 `index.css` L334–374（已内化至 `chart-theme.ts` 与 example runtime）。

## Data States

| 状态 | 模式 | 实现 |
|---|---|---|
| loading | 数据请求中 | `Skeleton` 覆盖 chart 区 `min-h-[180px]` + `aria-busy="true"` |
| empty | 无数据 | Card 内居中 `text-gray-500` + outline `Button` 刷新 |
| error | 请求失败 | `Alert variant="error"` 替换 chart 区，保留卡壳 |

禁止用装饰性动画掩盖空数据；业务密度优先。

## 工程约束

- 保留 `react-apexcharts`；不替换为 recharts
- 禁止在 options 内硬编码非 Token hex（使用 `chartPalette`）
- 字体 `Outfit, sans-serif` 与全局一致
- 图表页路由见 `route-index.md` Charts & Maps（业务层，非 DS 核心 primitive）

## 与 third-party-template 关系

`third-party-template.md#charts` 保留简要入口；本 shard 为 Chart 深化参考。Agent 任务涉及仪表盘/analytics 时优先读本文件。
