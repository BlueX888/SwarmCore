# Merge Options 选型指南

> G50 DOCS-002 产物。Agent 在覆盖第三方 theme lib 的 `options` 前，先读本指南判断**浅 merge 是否足够**，避免嵌套对象丢子 key。

## 读取顺序

1. 本指南 — 判断浅 merge / deep merge
2. `api-override-recipes.md` — 可复制 override 片段
3. `scenario-override-recipes.md` — BI/DevOps/PaaS 场景组合
4. `api-contracts.md` — helper 稳定性与导出名

## 决策矩阵

| 场景 | 推荐 helper | 原因 |
|---|---|---|
| 仅改顶层标量（`zoom`、`scrollWheelZoom`、`delay`） | 浅 merge 或 helper 自带 `overrides` | 无嵌套对象，spread 安全 |
| 改嵌套对象的部分子 key（`navigation.nextEl`、`headerToolbar.right`、`chart.toolbar`） | `deepMergeOptions` 或组件专用 `*Deep` | 浅 merge 会整体替换嵌套对象 |
| Swiper preset 上改 `autoplay.delay` 但保留 `navigation` 选择器 | `mergeSwiperOptionsDeep` | `mergeSwiperOptions` 会丢 `navigation` |
| Chart / FullCalendar 工厂函数 | `getBaseChartOptions` / `getDefaultFullCalendarOptions` | 内部已 deep merge（G49） |
| MapLibre / Leaflet 仅改 `center` / `zoom` | `mergeMapLibreOptions` / `mergeLeafletOptions` | 默认 options 扁平，浅 merge 足够 |
| 跨组件场景组合（BI 联动、DevOps 看板、PaaS 地图） | `scenario-override-recipes.md` SOR-01～03 | 多 helper 联动，先场景后单组件 |

## Helper 对照表

| Helper | 深度 | 适用组件 | 何时不用 |
|---|---|---|---|
| `deepMergeOptions` | deep | 通用 | 仅需替换整个嵌套对象时可直接 spread |
| `getBaseChartOptions(overrides?)` | deep | ApexCharts | 仅改颜色 token 时用 `chartPaletteCssVars` |
| `getDefaultFullCalendarOptions(overrides?)` | deep | FullCalendar | 仅改 `eventContent` className 时直接传 props |
| `mergeSwiperOptionsDeep` | deep | Swiper | — |
| `mergeSwiperOptions` | **浅** | Swiper | **禁止**用于含 `navigation`/`pagination` 的 preset |
| `mergeMapLibreOptions` | 浅 | MapLibre | 未来若 options 嵌套化，改用 `deepMergeOptions` |
| `mergeLeafletOptions` | 浅 | Leaflet | 同上 |

## 正例

### Swiper — 保留 navigation，只改 autoplay

```ts
import { mergeSwiperOptionsDeep, withControlSwiperOptions } from "@/lib/carousel-theme";

const options = mergeSwiperOptionsDeep(withControlSwiperOptions, {
  autoplay: { delay: 8000 },
});
// ✅ navigation.nextEl / prevEl 仍来自 withControlSwiperOptions
```

### FullCalendar — 只改 headerToolbar.right

```ts
import { getDefaultFullCalendarOptions } from "@/lib/fullcalendar-theme";

const options = getDefaultFullCalendarOptions({
  headerToolbar: { right: "timeGridWeek,listWeek" },
});
// ✅ left / center 保留 base 默认值
```

### MapLibre — 扁平 center/zoom

```ts
import { mergeMapLibreOptions } from "@/lib/maps-theme";

const options = mergeMapLibreOptions({
  center: [116.4074, 39.9042],
  zoom: 11,
});
// ✅ 浅 merge 足够，无嵌套子 key 风险
```

## 反例

### ❌ Swiper 浅 merge 丢 navigation

```ts
import { mergeSwiperOptions, withControlSwiperOptions } from "@/lib/carousel-theme";

const bad = mergeSwiperOptions(withControlSwiperOptions, {
  autoplay: { delay: 8000 },
});
// ❌ autoplay 整体替换后 navigation 仍在，但若 overrides 含 navigation 子 key 会丢另一侧
const worse = mergeSwiperOptions(withControlSwiperOptions, {
  navigation: { nextEl: ".custom-next" },
});
// ❌ prevEl 丢失，轮播只剩下一侧箭头
```

**修复**：改用 `mergeSwiperOptionsDeep`。

### ❌ 手写 spread 覆盖嵌套对象

```ts
const bad = {
  ...withControlSwiperOptions,
  navigation: { nextEl: ".custom-next" },
};
// ❌ 与 mergeSwiperOptions 相同问题
```

## 迁移路径

| 旧写法 | 新写法 | 说明 |
|---|---|---|
| `mergeSwiperOptions(base, { autoplay: { delay: N } })` | `mergeSwiperOptionsDeep(base, { autoplay: { delay: N } })` | 保留 preset navigation/pagination |
| `{ ...getBaseChartOptions(), chart: { toolbar: { show: true } } }` | `getBaseChartOptions({ chart: { toolbar: { show: true } } })` | 工厂已 deep merge |
| 场景内多组件 override | `scenario-override-recipes.md` SOR-01～03 | 避免各组件各自浅 merge |

`mergeSwiperOptions` **保留**用于向后兼容（G45 additive API），新代码默认 `mergeSwiperOptionsDeep`。

## 检索入口

| 意图 | 读 |
|---|---|
| 单组件 override 片段 | `api-override-recipes.md` |
| 场景组合 override | `scenario-override-recipes.md` |
| 契约与稳定性 | `api-contracts.md` |
| 扩展性审计 | `extension-audit.md` |
