# 复杂组件扩展性审计注册表

> AUDIT-001 产物。Agent 在封装或评审第三方/复杂组件前，先读本表确认 API 灵活性、状态矩阵、数据韧性与降级方案是否达标。
>
> **可复制 override 片段**：`api-override-recipes.md`（G45 深化的 14 项食谱）。
> **场景级组合 override**：`scenario-override-recipes.md`（G49 SOR-01～03；G51 SOR-04～05；G52 MS-11～13 playbook 路由闭环）。
> **浅 merge / deep merge 选型**：`merge-options-guide.md`（G50 DOCS-002）。

## 审计门控（95+ 前置条件）

| 检查 | 要求 | 未达标封顶 |
|---|---|---|
| API 灵活性 | props、受控值、事件回调、className/token override | 扩展性 ≤ 85 |
| 状态矩阵 | loading/empty/error/disabled/readonly/dark 有文档或示例 | 扩展性 ≤ 88 |
| 数据韧性 | 长文本、空数组、局部失败不破坏布局 | 逻辑完备 ≤ 88 |
| 降级方案 | 第三方库缺失、SSR/移动端不可用时有 fallback | 扩展性 ≤ 85 |
| 可复制模板 | 非仅 CSS mock 或 theme lib | 组件覆盖率 ≤ 89 |
| Preview 证据 | light/dark 截图 + 打开态（适用时） | 综合美学 ≤ 90 |

## 审计总表

| 组件 | 模板/主题 | 审计状态 | API | 状态矩阵 | 数据韧性 | 降级 | 场景复用 |
|---|---|---|---|---|---|---|---|
| Chart (ApexCharts) | `lib/chart-theme.ts` | **pass** | options override、色板 token | loading/empty/error 见 chart-theme#Data States | 宽表 overflow-x-auto | StatCard 静态 KPI | SaaS/BI/PaaS/DevOps |
| FullCalendar | `lib/fullcalendar-theme.ts` | **pass** | options、eventContent className | loading/empty/error 见 fullcalendar-theme#Data States | 长事件标题 truncate | table/list 日程 | 企业/政府排期 |
| Kanban | `ui/kanban-board.tsx` + `ui/kanban-column-menu.tsx` | **pass** | 受控 columns、onTaskMove、列菜单回调 | loading/empty/error 内置 | 长标题 mr-10 truncate | TaskList 表格 | DevOps/任务管理 |
| Maps | `lib/maps-theme.ts` | **pass** | MapLibre/iframe options | loading/error 见 maps-theme#Data States | 固定 h-[300px] | 静态地图图片 Card | 运维/监控 |
| Vector Maps | `lib/vector-map-theme.ts` | **pass** | regionStyle injector、zoom handlers | loading/error 见 vector-map-theme#Data States | 区域 tooltip | 表格地区分布 | BI/安全审计 |
| Editor (Prism) | `ui/code-block.tsx` + `ui/code-editor.tsx` + `lib/editor-theme.ts` | **pass** | 受控 value、mode、language、onSave | loading/empty/error/dirty 内置 | 长代码 scroll | plain `<pre>` | DevOps/AI 代码块 |
| Carousel (Swiper) | `lib/carousel-theme.ts` | **pass** | 4 variant options、CSS overrides | loading/empty 见 carousel-theme#Data States | 图片 lazy | 水平滚动列表 | 营销/产品展示 |
| DatePicker | `ui/date-picker.tsx` | **pass** | single/range、受控、error/disabled | focus/disabled/error | 长 range 文本 | native date input | 全场景表单 |
| MultiSelect | `ui/multi-select.tsx` | **pass** | 受控 value、options、maxVisibleTags | disabled、empty 搜索 | 多标签换行 | Checkbox 组 | 筛选/权限/标签 |
| FileUpload | `ui/file-upload.tsx` | **pass** | label/hint/error、variant | disabled/error | 大文件名 truncate | 原生 file input | 简单单文件 |
| FileDropzone | `ui/file-dropzone.tsx` | **pass** | drag-drop、多文件、进度、onRemove | disabled/error/uploading | 长文件名 truncate | FileUpload 降级 | 批量导入/附件 |
| ThemeToggle | `layout/theme-toggle.tsx` | **pass** | className、aria-label | dark 切换 | — | 系统 prefers-color-scheme | 全局壳层 |
| Command Palette | `ui/command.tsx` + `ui/search-command.tsx` | **pass** | groups、shortcut、受控 open | disabled item、empty | 长列表 scroll | 简单搜索 Input | 全局导航 |
| UserDropdown | `layout/user-dropdown.tsx` | **pass** | menuItems、onOpenChange | open/close/focus | 长邮箱 truncate | 简单 Avatar 链接 | AppHeader |
| NotificationDropdown | `layout/notification-dropdown.tsx` | **pass** | items、onOpenChange、badge | empty、unread | 长通知 truncate | Badge 计数 | AppHeader |

## 分项审计摘要

### Chart (ApexCharts) — pass

- **API**：`getBaseChartOptions(overrides)`、`createBarChartOptions`、`createLineChartOptions`、`createDonutChartOptions`；`chartPalette` / `chartPaletteCssVars` token 对齐。
- **状态**：Skeleton loading、empty 居中文案 + 刷新按钮、error Alert 替换图表区。
- **降级**：`StatMetric` + `MetricCard` 静态 KPI，无 ApexCharts 依赖。
- **风险**：preview 为 CSS bar mock，非 react-apexcharts 运行时。

### FullCalendar — pass

- **API**：`getDefaultFullCalendarOptions(overrides)`、`getEventContentClassName`、`fullCalendarCssOverrides`。
- **状态**：loading Skeleton、empty 无事件提示、error Alert。
- **降级**：table/list 日程视图。
- **风险**：preview 为 CSS 日历格 mock。

### Kanban — pass（G33 补齐）

- **API**：`KanbanBoard` 受控 `columns`、`onTaskMove`、`onColumnAction`；`KanbanColumnMenu` 独立列头菜单。
- **状态**：`loading` 每列 Skeleton、`error` Alert 替换整板、`empty` 列内提示。
- **降级**：`Table` + 状态列替代看板。
- **DnD**：模板提供 callback API；业务层可接 `react-dnd` 或 `@dnd-kit`。

### Maps / Vector Maps — pass

- **API**：`mapCardShellClass`、`defaultMapLibreOptions`、`globalMarkerRegionStyle`、`createVectorMapZoomHandlers`。
- **状态**：loading 遮罩、error Alert + 重试。
- **降级**：静态地图截图 Card。

### Editor (Prism) — pass（G40 editable 补齐）

- **API**：`CodeBlock` 只读；`CodeEditor` 受控 `value`/`onChange`、`mode`、`language`、`dirty`、`onSave`；`AiCodeGeneratorShell` 页面组合。
- **状态**：loading Skeleton、empty 居中文案、error Alert、dirty badge、语法错误底栏。
- **降级**：`<pre><code>` plain text；mobile 降为 edit/preview 单栏。
- **风险**：preview 仍为 CSS mock；React 运行时以模板为准。

### Carousel (Swiper) — pass

- **API**：`withControlSwiperOptions`、`carouselPageGridClass`、`swiperCssOverrides`；4 variant；`mergeSwiperOptionsDeep`（嵌套 override）；`mergeSwiperOptions`（仅顶层标量，见 `merge-options-guide.md`）。
- **状态**：loading Skeleton、empty 占位。
- **降级**：水平 `overflow-x-auto` 图片列表。
- **风险**：对含 `navigation`/`pagination` 的 preset 使用 `mergeSwiperOptions` 会丢子 key；新代码默认 `mergeSwiperOptionsDeep`。

### DatePicker — pass

- **API**：`mode: single | range`、受控 `value`/`onValueChange`、`error`/`disabled`。
- **状态**：error 边框 + hint、disabled opacity、focus ring。
- **降级**：`<input type="date">` native。

### MultiSelect — pass

- **API**：受控 `value`、`options`、`maxVisibleTags`、`searchPlaceholder`、`emptyMessage`。
- **状态**：disabled、empty 搜索无结果、标签溢出 +N。
- **降级**：Checkbox 组 + 滚动容器。

### FileUpload — pass

- **API**：`label`/`hint`/`error`、`variant`、标准 input props。
- **状态**：disabled、error variant。
- **降级**：原生 `<input type="file">`。

### FileDropzone — pass（G35 补齐）

- **API**：`files` 受控列表、`onFilesSelected`、`onRemoveFile`、`maxSizeMb`、`multiple`、drag-drop。
- **状态**：disabled、error、uploading 进度、done/error 文件项。
- **降级**：回退 `FileUpload` 单文件 input。
- **兼容**：additive，不替换 `FileUpload` 公开 API。

### ThemeToggle — pass

- **API**：`className`、`aria-label`；依赖 `ThemeProvider` context。
- **状态**：Sun/Moon 图标 dark 切换。
- **降级**：`prefers-color-scheme` media query 只读。

### Command / Combobox — pass

- **API**：`SearchCommand` groups/items/shortcut；`ComboboxPanel` 单选；底层 `Command` 全量 cmdk props。
- **状态**：disabled item、CommandEmpty、受控 open。
- **降级**：简单 `<Input>` 搜索框。

### Header Dropdowns — pass

- **API**：`UserDropdown` menuItems/onOpenChange；`NotificationDropdown` items/badge。
- **状态**：open/close、empty 通知、unread badge。
- **降级**：Avatar 直链 profile。

## partial 项下轮优先级

| 优先级 | 组件 | 缺口 | 目标产物 |
|---:|---|---|---|
| P1 | Preview 运行时 | 全站 CSS mock | React preview 或 Storybook（长期） |

## 检索入口

| 意图 | 读 |
|---|---|
| 扩展性审计总表 | 本文件 |
| **API override 可复制食谱** | `api-override-recipes.md` |
| **场景级 override 食谱** | `scenario-override-recipes.md` |
| 第三方组件简要规则 | `component-styles/third-party-template.md` |
| 组件索引 + 审计状态 | `component-index.md#extension-audit` |
| 向后兼容门控 | `backward-compatibility.md` |
