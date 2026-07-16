# API Override 可复制食谱

> AUDIT-002 / G45 产物。Agent 在封装第三方主题或复杂组件前，先读本文件获取**可复制 override 片段**，再查 `api-contracts.md` 确认稳定性。

## 使用顺序

1. `merge-options-guide.md` — 判断浅 merge / deep merge（**嵌套 options 必读**）
2. 本文件 — 找 override 片段与降级路径
3. `extension-audit.md` — 确认审计状态与门控
4. `api-contracts.md` — 确认导出名与破坏性风险
5. 对应 `component-styles/*-theme.md` — 视觉与状态矩阵

## 门控

| 场景 | 要求 |
|---|---|
| 仅改颜色/密度 | 优先 token override（`chartPaletteCssVars`、Tailwind class） |
| 改行为/数据 | 使用 helper 的 `overrides` 参数或受控 props |
| 嵌套对象（Swiper navigation） | 先读 `merge-options-guide.md`；使用 `mergeSwiperOptionsDeep` 或 `deepMergeOptions`；**禁止**对含 navigation/pagination 的 preset 用 `mergeSwiperOptions` |
| 第三方缺失 | 必须走降级食谱，不得静默失败 |

## 嵌套 Deep Merge

**模板**：`templates/lib/merge-options.ts`

```ts
import { deepMergeOptions } from "@/lib/merge-options";
import { mergeSwiperOptionsDeep } from "@/lib/carousel-theme";

// Chart：仅打开 toolbar，保留 fontFamily/animations
const chartOpts = getBaseChartOptions({
  chart: { toolbar: { show: true } },
});

// FullCalendar：仅改 headerToolbar.right，保留 left/center
const fcOpts = getDefaultFullCalendarOptions({
  headerToolbar: { right: "timeGridWeek,listWeek" },
});

// Swiper：仅改 autoplay.delay，保留 navigation 选择器
const swiperOpts = mergeSwiperOptionsDeep(withControlSwiperOptions, {
  autoplay: { delay: 8000 },
});
```

**场景级组合 override**（BI/DevOps/PaaS 多组件联动）见 `scenario-override-recipes.md`（SOR-01～03）。

---

## Chart (ApexCharts)

**模板**：`templates/lib/chart-theme.ts`

```ts
import {
  getBaseChartOptions,
  createBarChartOptions,
  chartPaletteCssVars,
} from "@/lib/chart-theme";

// 1) 基础 options 覆盖 toolbar / 动画
const options = getBaseChartOptions({
  chart: { id: "revenue-trend", toolbar: { show: true } },
  colors: [chartPaletteCssVars.brand, chartPaletteCssVars.success],
});

// 2) 柱状图工厂 + 系列数据
const barOptions = createBarChartOptions({
  series: [{ name: "收入", data: [12, 19, 15, 22] }],
  xaxis: { categories: ["一月", "二月", "三月", "四月"] },
});

// 3) 降级：无 ApexCharts 时用 StatMetric + MetricCard 静态 KPI
```

**常见 override**：`colors`、`chart.height`、`xaxis.categories`、`yaxis.labels.formatter`、`legend.position`。

---

## FullCalendar

**模板**：`templates/lib/fullcalendar-theme.ts`

```ts
import {
  getDefaultFullCalendarOptions,
  getEventContentClassName,
} from "@/lib/fullcalendar-theme";

// 周视图 + 可编辑 + 中文按钮
const options = getDefaultFullCalendarOptions({
  initialView: "timeGridWeek",
  editable: true,
  customButtons: {
    addEventButton: { text: "新建日程 +" },
  },
  events: [
    { title: "发布窗口", start: "2026-06-25", extendedProps: { level: "Primary" } },
  ],
  eventContent: (arg) => ({
    html: `<div class="${getEventContentClassName(arg.event.extendedProps.level)}">${arg.event.title}</div>`,
  }),
});

// 降级：table/list 日程列表
```

**常见 override**：`initialView`、`headerToolbar`、`editable`、`events`、`eventContent`、`slotMinTime`。

---

## Kanban

**模板**：`templates/ui/kanban-board.tsx`

```tsx
import { KanbanBoard, type KanbanColumnData } from "@/components/ui/kanban-board";

const [columns, setColumns] = useState<KanbanColumnData[]>(initial);

<KanbanBoard
  columns={columns}
  loading={isLoading}
  error={error?.message}
  onTaskMove={(taskId, from, to) => moveTask(taskId, from, to)}
  onColumnAction={(columnId, action) => handleColumnMenu(columnId, action)}
  onAddTask={(columnId) => openCreateTask(columnId)}
  className="min-h-[480px]"
/>

// 降级：Table + 状态列
```

**常见 override**：受控 `columns`、`className`、列菜单 `onColumnAction`、loading/error 文案。

---

## Maps (MapLibre / Leaflet / iframe)

**模板**：`templates/lib/maps-theme.ts`

```ts
import {
  mapCardShellClass,
  mapContainerClass,
  mergeMapLibreOptions,
  mergeLeafletOptions,
  createLeafletDivIcon,
  leafletMarkerSvgs,
} from "@/lib/maps-theme";

// MapLibre：业务坐标 override
const mapOptions = mergeMapLibreOptions({
  center: [116.4074, 39.9042],
  zoom: 10,
});

// Leaflet：禁用滚轮 + 自定义 zoom
const leafletOptions = mergeLeafletOptions({ scrollWheelZoom: true });

// Leaflet marker HTML override
const homeIcon = createLeafletDivIcon("总部", leafletMarkerSvgs.home);

// 降级：静态地图截图 Card + 链接
```

**常见 override**：`center`、`zoom`、`style`（MapLibre）、`scrollWheelZoom`、marker HTML。

---

## Vector Maps (jVectorMap)

**模板**：`templates/lib/vector-map-theme.ts`

```ts
import {
  globalMarkerRegionStyle,
  trafficRegionStyle,
  createTrafficRegionStyleInjector,
  createVectorMapZoomHandlers,
} from "@/lib/vector-map-theme";

const { onRegionTipShow, onRegionSelected } = createTrafficRegionStyleInjector();
const zoomHandlers = createVectorMapZoomHandlers(mapRef);

// region 色阶 override：复制 preset 后改 fill
const customRegionStyle = {
  ...trafficRegionStyle,
  CN: { fill: "#465FFF" },
};

// 降级：表格地区分布
```

**常见 override**：`regionStyle` preset、`onRegionTipShow`、zoom handler ref 注入。

---

## Editor (Prism)

**模板**：`templates/ui/code-editor.tsx`、`templates/ui/code-block.tsx`

```tsx
import { CodeEditor } from "@/components/ui/code-editor";
import { CodeBlock } from "@/components/ui/code-block";

// 受控编辑 + 语言/mode override
<CodeEditor
  value={source}
  onChange={setSource}
  language="tsx"
  mode="split"
  dirty={dirty}
  onSave={handleSave}
  className="min-h-[360px]"
/>

// 只读 + 复制/跳转编辑
<CodeBlock
  code={snippet}
  language="bash"
  showLineNumbers
  onCopy={copyToClipboard}
  onEdit={() => setEditing(true)}
/>

// 降级：<pre><code className={getPrismLanguageClass('tsx')}>
```

**常见 override**：`value`/`onChange`、`language`、`mode`（edit/preview/split）、`className`、`onSave`。

---

## Carousel (Swiper)

**模板**：`templates/lib/carousel-theme.ts`

```ts
import {
  withControlSwiperOptions,
  mergeSwiperOptionsDeep,
  carouselNavPrevClass,
} from "@/lib/carousel-theme";

// 基于 preset 覆盖 autoplay 延迟（嵌套 key 用 deep merge）
const options = mergeSwiperOptionsDeep(withControlSwiperOptions, {
  autoplay: { delay: 8000, disableOnInteraction: true },
});

// navigation 选择器必须与 DOM class 一致（见 carouselNavPrevClass）
// 降级：水平 overflow-x-auto 图片列表
```

**常见 override**：`autoplay.delay`、`slidesPerView`、`navigation` 选择器、`pagination.el`。

---

## DatePicker

**模板**：`templates/ui/date-picker.tsx`

```tsx
<DatePicker
  label="生效日期"
  mode="range"
  value={range}
  onValueChange={setRange}
  placeholder="选择日期范围"
  error={errors.effectiveDate}
  disabled={isReadonly}
  className="max-w-md"
/>

// 降级：<input type="date" />
```

**常见 override**：`mode`、`value`/`onValueChange`、`error`、`disabled`、`placeholder`、`className`。

---

## MultiSelect

**模板**：`templates/ui/multi-select.tsx`

```tsx
<MultiSelect
  label="告警级别"
  value={levels}
  onValueChange={setLevels}
  options={levelOptions}
  maxVisibleTags={3}
  searchPlaceholder="搜索级别…"
  emptyMessage="无匹配项"
  disabled={!canEdit}
/>

// 降级：Checkbox 组 + 滚动容器
```

**常见 override**：受控 `value`、`options`、`maxVisibleTags`、搜索/空态文案、`disabled`。

---

## FileUpload / FileDropzone

```tsx
// 单文件
<FileUpload
  label="许可证文件"
  hint="支持 PDF，最大 10MB"
  error={errors.license}
  variant={errors.license ? "error" : "default"}
  disabled={uploading}
/>

// 多文件拖拽
<FileDropzone
  files={files}
  onFilesSelected={appendFiles}
  onRemoveFile={removeFile}
  maxSizeMb={10}
  multiple
  disabled={uploading}
/>

// 降级：原生 <input type="file" />
```

---

## ThemeToggle

```tsx
<ThemeToggle className="size-9" aria-label="切换深浅色主题" />
```

**常见 override**：`className`、`aria-label`；依赖 `ThemeProvider`。

---

## Command Palette / Combobox

```tsx
<SearchCommand
  open={open}
  onOpenChange={setOpen}
  groups={navGroups}
  placeholder="搜索页面或操作…"
/>

// 降级：简单 <Input type="search" />
```

**常见 override**：受控 `open`、`groups`/`items`、`placeholder`、shortcut 映射。

---

## Header Dropdowns

```tsx
<UserDropdown
  menuItems={profileMenu}
  onOpenChange={setUserMenuOpen}
/>

<NotificationDropdown
  items={notifications}
  badge={unreadCount}
  onOpenChange={setNotifyOpen}
/>

// 降级：Avatar 直链 profile
```

**常见 override**：`menuItems`/`items`、`onOpenChange`、`badge`、空态文案。

---

## 检索入口

| 意图 | 读 |
|---|---|
| override 片段 | 本文件对应章节 |
| 场景组合 override | `scenario-override-recipes.md`（SOR-01～03） |
| 嵌套 deep merge | `templates/lib/merge-options.ts` |
| 审计总表 | `extension-audit.md` |
| 契约稳定性 | `api-contracts.md` |
| 第三方总览 | `component-styles/third-party-template.md` |
