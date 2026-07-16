# 第三方与复合控件 — Chart / Calendar / DatePicker / MultiSelect

源项目使用第三方库；shadcn 栈下的推荐实现与 TailAdmin 视觉对齐规则。

## 已实现能力复查门控

> **AUDIT-001 审计注册表**：`extension-audit.md`（14 项复杂组件 API/状态/降级逐项记录）。
>
> **可复制 override 食谱**：`api-override-recipes.md`（G45 深化片段）。

每个第三方/复杂组件在标记 95+ 前，必须通过以下复查：

| 检查 | 要求 |
|---|---|
| API 灵活性 | 暴露必要 options、受控值、事件回调、className 或 token override，不把示例数据写死 |
| 状态矩阵 | loading、empty、error、disabled、readonly、permission denied、dark 至少有文档或示例 |
| 数据韧性 | 长文本、大数据量、空数组、局部失败、刷新中状态不破坏布局 |
| 降级方案 | 第三方库缺失、SSR 不可用、移动端不可用或性能不足时有 fallback |
| 主题边界 | CSS override 有明确作用域，不能污染全局 shadcn/Radix 组件 |
| 场景复用 | 能映射到 SaaS、企业、政府、PaaS、DevOps、控制平面至少两个业务域 |
| Preview 证据 | 有 light/dark 或至少 desktop light 截图；复杂组件打开态、滚动区、长内容态必须可见 |

不满足 API 灵活性或降级方案时，扩展性与灵活性不得高于 85；只有静态 mock 而非可复制模板时，不得高于 89。

## DatePicker

**源**：`form/date-picker.tsx`（flatpickr）

| 方案 | 适用 | 说明 |
|---|---|---|
| **A（推荐）** | 新 shadcn 项目 | `Popover` + `Calendar` + `Button` trigger，`h-11 rounded-lg` |
| B | 迁移源项目 | 保留 flatpickr，仅覆盖 `index.css` 中 `.flatpickr-*` 主题 |

### 方案 A 视觉规则

可复制模板：`templates/ui/calendar.tsx` · `templates/ui/date-picker.tsx`

```tsx
<DatePicker
  label="Start date"
  mode="single"
  value={date}
  onValueChange={setDate}
  placeholder="Select date"
/>

<DatePicker selectionMode="multiple" unavailable={blackoutDates} />
```

- Trigger 外观与 `InputField` 一致：`h-11`、`shadow-theme-xs`、`border-gray-300`
- range 模式：`<DatePicker mode="range" />` — 双月 Calendar
- Chakra 风格 API：`selectionMode` 支持 `single` / `range` / `multiple`；`min`、`max`、`unavailable` 映射到 Calendar disabled matcher。
- Calendar 表单内联预览：`<Calendar selectionMode="range" size="sm" />`，与 DatePicker popover 共用 TailAdmin day token。
- 错误态：`error` prop → `border-error-500` + hint
- 禁用：`disabled` → Button `disabled:opacity-40`

## MultiSelect

**源**：`form/MultiSelect.tsx`

**推荐**：`Popover` + `Command`（shadcn）

可复制模板：`templates/ui/multi-select.tsx`（完整复合控件）· `templates/ui/search-command.tsx#ComboboxPanel`（单选 Combobox）

## Charts（ApexCharts）

**源**：`components/charts/bar/BarChartOne.tsx`

深化参考：`chart-theme.md` · 可复制模板：`templates/lib/chart-theme.ts`

```ts
import { createBarChartOptions } from "@/lib/chart-theme";
```

- 色板 `chartColors` 对齐 Token
- 暗色 CSS：`apexChartsCssOverrides` → 宿主 `index.css`
- loading/empty/error 态见 `chart-theme.md#data-states`

## Calendar（FullCalendar）

**源**：`/calendar` 路由 — `@fullcalendar/react`

深化参考：`fullcalendar-theme.md` · 可复制模板：`templates/lib/fullcalendar-theme.ts`

```ts
import {
  getDefaultFullCalendarOptions,
  getEventContentClassName,
  fullCalendarCssOverrides,
} from "@/lib/fullcalendar-theme";

// 默认月视图
<FullCalendar {...getDefaultFullCalendarOptions()} events={events} />

// 业务 override：周视图 + 可编辑（G45）
<FullCalendar
  {...getDefaultFullCalendarOptions({
    initialView: "timeGridWeek",
    editable: true,
  })}
  events={events}
/>
```

- 事件色：`brand-500`、`success-500`、`error-500`、`orange-500`（四级 pill + dot）
- 边框：`border-gray-200 dark:border-gray-800`
- 今日高亮：`bg-gray-100 dark:bg-white/[0.03]`
- loading/empty/error 态见 `fullcalendar-theme.md#data-states`

## Kanban

**源**：`/task-kanban` — `components/task/kanban/*`

深化参考：`kanban-theme.md` · 可复制模板：`templates/ui/kanban-board.tsx` · `templates/ui/kanban-column-menu.tsx`

```tsx
import { KanbanBoard } from "@/components/ui/kanban-board";

<KanbanBoard columns={columns} onTaskMove={moveTask} loading={isLoading} />
```

- 三列 swim-lane：`todo` / `inProgress` / `completed`
- DnD：模板内置 HTML5 drag-and-drop；业务层可换 `react-dnd`
- loading/empty/error 态见 `kanban-theme.md#Data States`
- 审计状态：**pass**（`extension-audit.md`）

## Maps

**源**：`/maps` — MapLibre、iframe、Leaflet

深化参考：`maps-theme.md` · 可复制模板：`templates/lib/maps-theme.ts`

```ts
import {
  mapCardShellClass,
  defaultMapLibreOptions,
  iframeMapClass,
} from "@/lib/maps-theme";
```

- 页面栅格：`grid-cols-1 lg:grid-cols-2 gap-6`
- 地图高度 `h-[300px]`；zoom 控件右上 stack
- loading/error 态见 `maps-theme.md#data-states`

## Vector Maps（jVectorMap）

**源**：`/vector-map` — `@react-jvectormap/core`

深化参考：`vector-map-theme.md` · 可复制模板：`templates/lib/vector-map-theme.ts`

```ts
import {
  globalMarkerRegionStyle,
  trafficRegionStyle,
  createTrafficRegionStyleInjector,
  createVectorMapZoomHandlers,
} from "@/lib/vector-map-theme";
```

- 三卡纵向：`global markers` / `traffic heatmap` / `US state heatmap`
- region 色阶对齐 brand Token（`#465FFF` → `#ADC6FF`）
- 自定义 zoom bottom-right；隐藏库内置 zoom 按钮
- loading/error 态见 `vector-map-theme.md#data-states`

## Editor（Prism Code Block）

**源**：`components/ai/Codeblock.tsx` — AI Code Generator

深化参考：`editor-theme.md` · `code-editor-editable.md` · 可复制模板：`templates/lib/editor-theme.ts`、`templates/ui/code-block.tsx`、`templates/ui/code-editor.tsx`

```ts
import {
  codeBlockShellClass,
  prismCssOverrides,
  getPrismLanguageClass,
} from "@/lib/editor-theme";
```

- 壳层 `rounded-2xl border` + header toolbar 圆形按钮
- Prism token 色对齐 gray/brand 语义
- loading/empty/error 态见 `editor-theme.md#data-states`

## Carousel（Swiper）

**源**：`/carousel` — `components/ui/carousel/*`

深化参考：`carousel-theme.md` · 可复制模板：`templates/lib/carousel-theme.ts`

```ts
import {
  carouselPageGridClass,
  withControlSwiperOptions,
  swiperCssOverrides,
} from "@/lib/carousel-theme";
```

- 四 variant：slide only / controls / indicators / both
- 导航 `backdrop-blur` 圆形按钮；active bullet 拉长
- loading/empty/error 态见 `carousel-theme.md#data-states`

## Skeleton（加载）

shadcn `Skeleton`：

可复制模板：`templates/ui/skeleton.tsx`

```tsx
<div className="animate-pulse space-y-3" aria-busy="true">
  <Skeleton className="h-4 w-1/3 rounded-md" />
  <Skeleton className="h-11 rounded-lg" />
</div>
```

表格加载：重复 `Skeleton className="h-12 rounded-lg"` 行，保留表头。

## 检索别名

| 意图 | 读本节 |
|---|---|
| 日期选择 | DatePicker → 方案 A |
| 多选下拉 | MultiSelect |
| 柱状/折线/饼图 | Charts |
| 日程页 | Calendar（FullCalendar） |
| 代码块 | Editor（Prism） |
| 轮播图 | Carousel（Swiper） |
| 骨架屏 | Skeleton |
