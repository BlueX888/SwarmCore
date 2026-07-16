# 公开 API 契约注册表

> COMPAT-001 产物。业务项目 vendored 模板或复制组件后，Agent 与维护者必须先读本表确认导出名、props、variants、theme helpers 的稳定性承诺，再决定是否升级 Skill 快照。

## 契约稳定性等级

| 等级 | 含义 | 演化规则 |
|---|---|---|
| **stable** | 已发布且多轮验证 | 不得删除/重命名；仅可 additive 扩展 |
| **additive** | 可安全新增 props/helper | 旧调用无需修改 |
| **evolving** | 功能仍在补齐 | 新增能力走新 props/新模板，不删旧 API |
| **theme-only** | 仅 theme lib，无 React 组件 | 常量/helper 重命名须 migration note |

## 第三方 / 复杂组件（theme lib）

### Chart (ApexCharts) — theme-only · stable

| 类别 | 名称 | 类型 | 说明 |
|---|---|---|---|
| 常量 | `chartPalette` | `Record<brand\|purple\|success\|info\|pink, string>` | hex 色板 |
| 常量 | `chartPaletteCssVars` | CSS var 映射 | 与 preview token 对齐 |
| 常量 | `chartColors` | `string[]` | palette 值数组 |
| 常量 | `barChartPlotOptions` / `lineChartStrokeOptions` / `donutChartPlotOptions` | ApexOptions 片段 | 图类型预设 |
| 常量 | `apexChartsCssOverrides` | `string` | 注入 host CSS |
| helper | `getBaseChartOptions(overrides?)` | `ApexOptions` | 基础配置 + **deep merge** overrides（G49） |
| helper | `createBarChartOptions` / `createLineChartOptions` / `createDonutChartOptions` | `ApexOptions` | 图类型工厂 |

**破坏性风险**：低。`overrides` spread 保证向后兼容。删除 palette key 或改默认 `toolbar.show` 视为破坏性。

**兼容策略**：业务层固定 `getBaseChartOptions({ chart: { id: 'my-chart' } })`；缺失 ApexCharts 时用 `StatMetric` + `MetricCard` 静态 KPI。

### FullCalendar — theme-only · stable

| 类别 | 名称 | 类型 | 说明 |
|---|---|---|---|
| 常量 | `eventLevelPalette` / `eventLevelClassMap` | 事件级别色 | Primary/Success/Danger/Warning |
| 常量 | `defaultHeaderToolbar` / `defaultCustomButtons` | FC 配置 | 与源 Calendar.tsx 对齐 |
| 常量 | `fullCalendarCssOverrides` | `string` | host CSS |
| helper | `getDefaultFullCalendarOptions(overrides?)` | FC options | 基础配置 + **deep merge** overrides（G49） |
| helper | `getEventContentClassName(level)` | `string` | 事件块 className |

**破坏性风险**：低。G45 新增 `overrides` 参数为 additive；旧无参调用不变。

**兼容策略**：`getDefaultFullCalendarOptions({ initialView: 'timeGridWeek', editable: true })`；降级为 table/list 日程。

### Kanban — stable（G33 起）

| 组件/类型 | 导出名 | 关键 props / 回调 |
|---|---|---|
| `KanbanBoard` | 组件 | `columns`, `loading?`, `error?`, `onTaskMove?`, `onColumnAction?`, `onAddTask?` |
| `KanbanColumnData` | type | `id`, `status: KanbanStatus`, `title`, `tasks` |
| `KanbanTask` | type | `id`, `title`, `category?`, `dueDate?`, … |
| `KanbanColumnMenu` | 组件 | `onAction: KanbanColumnMenuAction` |
| theme | `kanbanBoardGridClass`, `getCategoryClassName`, `getColumnCountBadgeClass` | class helpers |

**破坏性风险**：中（G33 新增 `KanbanBoard`）。旧项目若仅用 `kanban-theme` class 常量不受影响；若自建 DnD 板，应迁移到受控 `columns` API。

**兼容策略**：保留 `kanban-theme.ts` 全部 class 常量；过渡 wrapper `KanbanLegacyShell` 见 [MN-03](migration-notes/MN-03-kanban-legacy-board.md)。

### Maps — theme-only · stable

| 类别 | 名称 | 说明 |
|---|---|---|
| 布局 | `mapsPageGridClass`, `mapCardShellClass`, `mapContainerClass` | 卡片与容器 |
| 默认 | `defaultMapLibreOptions`, `defaultLeafletOptions`, `defaultLeafletTileUrl` | 提供商默认 |
| helper | `mergeMapLibreOptions(overrides?)` | MapLibre init | center/zoom/style 浅 merge（G45） |
| helper | `mergeLeafletOptions(overrides?)` | Leaflet init | center/zoom 浅 merge（G45） |
| helper | `createLeafletDivIcon(label, svgPath)` | Leaflet marker HTML |

**破坏性风险**：低。改 `defaultMapLibreOptions.center/zoom` 为视觉破坏性，须 migration note。

**兼容策略**：业务 override options 对象；降级静态地图 Card。

### Vector Maps — theme-only · stable

| 类别 | 名称 | 说明 |
|---|---|---|
| 布局 | `vectorMapCardShellClass`, `vectorMapHeightStyle` | 274px 固定高度 |
| 样式 | `globalMarkerRegionStyle`, `trafficRegionStyle`, `usHeatmapRegionStyle` | 区域 preset |
| helper | `createTrafficRegionStyleInjector`, `createVectorMapZoomHandlers` | 运行时注入 |

**破坏性风险**：低。`vectorMapHeightStyle` 高度变更影响截图对齐，记为视觉破坏性。

**兼容策略**：zoom handlers 通过 ref 注入；降级表格地区分布。

### Editor (Prism) — stable · theme + CodeBlock + CodeEditor

| 类别 | 名称 | 说明 |
|---|---|---|
| 组件 | `CodeBlock` | `templates/ui/code-block.tsx` 可复制只读代码块 |
| 组件 | `CodeEditor` | `templates/ui/code-editor.tsx` 可编辑 + 实时预览（G40 additive） |
| 组合 | `AiCodeGeneratorShell` | `templates/devops/ai-code-generator-shell.tsx` |
| class | `codeBlockShellClass` … `codeBlockPreWithLineNumbersClass` | 只读/可编辑代码块壳 |
| 语言 | `PrismLanguage`, `supportedPrismLanguages`, `getPrismLanguageClass` | 语言 class |
| CSS | `prismCssOverrides`, `prismLanguageImports` | host 注入 |

**破坏性风险**：低。G40 `CodeEditor` / `AiCodeGeneratorShell` 为 additive。

**兼容策略**：`<pre><code className={getPrismLanguageClass('tsx')}>` 降级；`CodeBlock` onEdit 可跳转 `CodeEditor`。

### Carousel (Swiper) — theme-only · stable

| 类别 | 名称 | 说明 |
|---|---|---|
| options | `slideOnlySwiperOptions`, `withControlSwiperOptions`, `withIndicatorsSwiperOptions`, `withControlAndIndicatorsSwiperOptions` | 4 variant |
| class | `carouselNavPrevClass`, `carouselNavNextClass`, `stocksSliderNavClass` | 导航按钮 |
| helper | `mergeSwiperOptions(base, overrides?)` | Swiper preset | 顶层浅 merge（G45）；**仅**替换整个顶层 key；嵌套 override 见 `merge-options-guide.md` |
| helper | `mergeSwiperOptionsDeep(base, overrides?)` | Swiper preset | 嵌套 deep merge（G49）；**默认**用于 preset override |
| helper | `deepMergeOptions(base, overrides?)` | 通用 | `templates/lib/merge-options.ts`（G49） |
| CSS | `swiperCssOverrides` | host 注入 |

**破坏性风险**：低。Swiper `navigation.nextEl` 选择器变更会破坏自定义 DOM，须 migration note。

**兼容策略**：水平 `overflow-x-auto` 图片列表降级。

## 复合控件（React 模板）

### DatePicker — stable

```ts
export type DatePickerProps = {
  label?: string;
  mode?: "single" | "range";                 // legacy alias
  selectionMode?: "single" | "range" | "multiple";
  value?: Date | DateRange | Date[];
  defaultValue?: Date | DateRange | Date[];
  onValueChange?: (value: Date | DateRange | Date[] | undefined) => void;
  placeholder?: string;  // 默认「请选择日期」
  disabled?: boolean;
  min?: Date;
  max?: Date;
  unavailable?: Date[];
  numberOfMonths?: number;
  size?: "sm" | "md" | "lg";
  formatString?: string;
  showTime?: boolean | { format?: string; minuteStep?: number };
  error?: string;
  className?: string;
  id?: string;
};
```

**破坏性风险**：低。`mode` 默认 `single`；`selectionMode` 是 Chakra 命名兼容，受控/非受控双模式 stable，multiple/min/max/unavailable 为 additive。`showTime` 为 PR-3 additive（仅 single 模式）。

**兼容策略**：旧 native `<input type="date">` 可并存；range 模式为 additive（G14+）；仅时间场景用 `TimePicker` 降级。

### MultiSelect — stable

```ts
export type MultiSelectProps = {
  label?: string;
  options: MultiSelectOption[];  // { value, label, keywords? }
  value?: string[];
  defaultValue?: string[];
  onValueChange?: (value: string[]) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  disabled?: boolean;
  className?: string;
  maxVisibleTags?: number;  // 默认 3
};
```

**破坏性风险**：低。`maxVisibleTags` 为 additive。

**兼容策略**：Checkbox 组 + 滚动容器降级。

### FileUpload — stable

```ts
export type FileUploadProps = Omit<React.ComponentProps<"input">, "type"> &
  VariantProps<typeof fileUploadVariants> & {
    label?: string;
    hint?: string;
    error?: string;
  };
// 导出: FileUpload, fileUploadVariants
```

**破坏性风险**：低（当前 API）。`variant: default | error`；`error` prop 强制 error variant。

**兼容策略**：原生 `<input type="file">` 降级。批量/拖拽场景用 additive `FileDropzone`。

### FileDropzone — stable · additive

```ts
export type FileDropzoneItem = { id, name, size?, progress?, status?, error? };
export type FileDropzoneProps = { files?, onFilesSelected?, onRemoveFile?, maxSizeMb?, multiple?, ... };
// 导出: FileDropzone, dropzoneVariants
```

**破坏性风险**：无（新组件，不替换 FileUpload）。

**兼容策略**：简单单文件仍用 `FileUpload`；无 drag-drop 时回退原生 input。

### ThemeToggle — stable（命名注意）

| 导出名 | 实际符号 | 说明 |
|---|---|---|
| `ThemeToggle` | `ThemeToggleButton` alias | G48 additive，见 `migration-notes/MN-01` |
| `ThemeToggleButton` | 主实现 | 壳层顶栏默认导出 |
| props | `className?`, `aria-label?`（默认中文「切换深浅色主题」） | |

**破坏性风险**：低。G48 已提供 `ThemeToggle` alias 与 `templates/ui/deprecated/theme-toggle-alias.tsx`。

**兼容策略**：见 [MN-01](migration-notes/MN-01-theme-toggle-alias.md)。

### Command / Combobox — stable

| 组件 | 关键契约 |
|---|---|
| `Command` + 子组件 | 全量 cmdk props 透传 |
| `SearchCommand` | 受控 `open`/`onOpenChange`，`groups`，可选 `onItemSelect` 覆盖 navigate |
| `SearchCommandStatic` | deprecated wrapper，无 react-router，见 `templates/ui/deprecated/` |
| `ComboboxPanel` | 单选 Popover+Command 组合（见 `search-command.tsx` 下部） |

**破坏性风险**：低。无路由项目传 `onItemSelect` 或使用 `SearchCommandStatic`。

**兼容策略**：见 [MN-02](migration-notes/MN-02-search-command-no-router.md)；简单 `<Input>` 搜索降级。

### Cascader — evolving

```ts
export type CascaderProps = {
  options: HierarchicalNode[];
  value?: string[];
  onChange?: (path: string[]) => void;
  loadData?: LoadDataFn;
  multiple?: boolean;
  changeOnSelect?: boolean;
  showSearch?: boolean;
  placeholder?: string;
  disabled?: boolean;
  inputSkin?: "outlined" | "filled" | "borderless" | "underlined";
  className?: string;
};
```

**破坏性风险**：中（PR-1 Batch A 新增）。`loadData` / `multiple` / `changeOnSelect` 为 evolving 能力。

**兼容策略**：浅层选项用 `Select`；深层树用 `TreeSelect` 降级。

### TreeSelect — evolving

```ts
export type TreeSelectProps = {
  treeData: HierarchicalNode[];
  value?: string | string[];
  onChange?: (value: string | string[]) => void;
  treeCheckable?: boolean;
  showCheckedStrategy?: CheckStrategy;
  loadData?: LoadDataFn;
  showSearch?: boolean;
  placeholder?: string;
  disabled?: boolean;
  inputSkin?: "outlined" | "filled" | "borderless" | "underlined";
  className?: string;
};
```

**破坏性风险**：中（PR-1 Batch A 新增）。`treeCheckable` / `showCheckedStrategy` 为 evolving 能力。

**兼容策略**：只读树展示用 `Tree`；单选浅层用 `Cascader` 降级。

### Transfer — stable（PR-GH 起 `targetSortable`）

```ts
export type TransferProps = {
  dataSource: TransferItem[];
  targetKeys: string[];
  onChange: (targetKeys: string[]) => void;
  titles?: [string, string];
  showSearch?: boolean;
  oneWay?: boolean;
  targetSortable?: boolean;
  render?: (item: TransferItem) => React.ReactNode;
  className?: string;
};
```

**破坏性风险**：低。PR-1 基础 API stable；`showSearch` / `oneWay` / `targetSortable` 均为 additive（PR-GH `targetSortable` 依赖 `@dnd-kit/*` peer）。

**兼容策略**：动态列表批量勾选用 `DataTable` + `rowSelection` 降级；目标侧排序用 `OrderList` 降级。

### Timeline — evolving

```ts
export type TimelineProps = {
  items: TimelineItem[];
  mode?: "left" | "alternate" | "right";
  pending?: React.ReactNode;
  size?: "sm" | "md";
  className?: string;
  ariaLabel?: string;
};
```

**破坏性风险**：中（PR-2 Batch B 新增）。`mode` / `alternate` 布局为 evolving 能力。

**兼容策略**：简单垂直列表用 `Steps`；CI 审批流用 `ApprovalTimeline` 领域包装。

### AnchorNav — evolving

```ts
export type AnchorNavProps = {
  sections: PageNavSection[];
  offset?: number;
  affix?: boolean;
  orientation?: "vertical" | "horizontal";
  className?: string;
};
```

**破坏性风险**：中（PR-2 Batch B 新增）。`usePageNav` hook 与 `AnchorSection` 组合为 evolving 能力。

**兼容策略**：短页用手写 `id` + `scrollIntoView`；页内面板切换用 `Tabs`。

### Tour — evolving

```ts
export type TourProps = {
  steps: TourStep[];
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  mask?: boolean;
  onFinish?: () => void;
  onSkip?: () => void;
};
```

**破坏性风险**：中（PR-2 Batch B 新增）。依赖 `driver.js` peer；步骤 `element` 选择器耦合 DOM。

**兼容策略**：单步说明用 `Tooltip` / `Popover`；静态引导图用 Dialog 降级。

### List — evolving

```ts
export type ListProps = {
  density?: "comfortable" | "compact";
  divided?: boolean;
} & React.HTMLAttributes<HTMLUListElement>;
```

**破坏性风险**：中（PR-2 Batch B 新增）。Slot 组合（`ListItemIcon` / `ListItemTrailing`）为 evolving 能力。

**兼容策略**：只读键值用 `DescriptionList`；表格行操作用 `DataTableCard`。

### TimePicker — evolving

```ts
export type TimePickerProps = {
  value?: Date;
  onChange?: (value: Date | undefined) => void;
  format?: string;
  showSeconds?: boolean;
  minuteStep?: number;
  secondStep?: number;
  disabledHours?: (hour: number) => boolean;
  disabledMinutes?: (hour: number, minute: number) => boolean;
  range?: [Date, Date];
  inputSkin?: "outlined" | "filled" | "borderless" | "underlined";
  placeholder?: string;
  disabled?: boolean;
  className?: string;
};
```

**破坏性风险**：中（PR-3 Batch C 新增）。`range` / `disabledHours` / `disabledMinutes` 为 evolving 能力。

**兼容策略**：`<input type="time">` 降级；日期+时间用 DatePicker `showTime`。

### Mentions — evolving

```ts
export type MentionsProps = {
  value?: string;
  onChange?: (value: string) => void;
  options: { value: string; label: string; avatar?: string }[];
  onSearch?: (query: string) => void;
  prefix?: string;
  rows?: number;
  inputSkin?: "outlined" | "filled" | "borderless" | "underlined";
  placeholder?: string;
  disabled?: boolean;
  className?: string;
};
```

**破坏性风险**：中（PR-3 Batch C 新增）。`onSearch` 远程候选为 evolving 能力。

**兼容策略**：固定候选集用 Autocomplete；只读展示用 Textarea。

### Rating — evolving

```ts
export type RatingProps = {
  value?: number;
  onChange?: (value: number) => void;
  count?: number;
  allowHalf?: boolean;
  readOnly?: boolean;
  disabled?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
};
```

**破坏性风险**：中（PR-3 Batch C 新增）。`allowHalf` 半星交互为 evolving 能力。

**兼容策略**：只读展示用手写 Star 图标；NPS 量表用 RadioGroup 降级。

### ColorPicker — evolving

```ts
export type ColorPickerProps = {
  value?: string;
  onChange?: (value: string) => void;
  format?: "hex" | "rgb" | "hsl";
  presets?: string[];
  showInput?: boolean;
  trigger?: "swatch" | "input";
  disabled?: boolean;
  className?: string;
};
```

**破坏性风险**：中（PR-3 Batch C 新增）。依赖 `react-colorful` peer；`format` 输出转换 evolving。

**兼容策略**：简单场景用 `<input type="color">`；preset-only 用手写色块行。

### Editable — evolving

```ts
export type EditableProps = {
  value?: string;
  onChange?: (value: string) => void;
  onSubmit?: (value: string) => void;
  onCancel?: () => void;
  placeholder?: string;
  submitOnBlur?: boolean;
  className?: string;
};
```

**破坏性风险**：中（PR-3 Batch C 新增）。`EditableTextarea` 多行变体为 evolving 能力。

**兼容策略**：表格行编辑用 FormDrawer；单行快速改名用 borderless Input 切换。

### Kbd — evolving

```ts
export type KbdProps = React.ComponentProps<"kbd"> & {
  size?: "sm" | "md";
};
```

**破坏性风险**：低（PR-4 Batch D 新增）。`size` 变体为 evolving 能力。

**兼容策略**：纯文本 `<code>` 或 inline `<span className="font-mono">` 降级。

### ToggleTip — evolving

```ts
export type ToggleTipProps = {
  content: React.ReactNode;
  children: React.ReactNode;
  side?: "top" | "right" | "bottom" | "left";
  align?: "start" | "center" | "end";
  className?: string;
};
```

**破坏性风险**：低（PR-4 Batch D 新增）。Popover `modal={false}` + click trigger 为 evolving 能力。

**兼容策略**：桌面-only 场景用 Tooltip hover 降级。

### ActionBar — evolving

```ts
export type ActionBarProps = {
  selectedCount: number;
  onClear: () => void;
  actions?: React.ReactNode;
  className?: string;
};
```

**破坏性风险**：低（PR-4 Batch D 新增）。`actions` slot 组合为 evolving 能力。

**兼容策略**：表格 toolbar 内联批量按钮降级。

### ChoiceCard — evolving

```ts
export type ChoiceCardProps = {
  type: "checkbox" | "radio";
  selected: boolean;
  onSelectedChange: (selected: boolean) => void;
  title: React.ReactNode;
  description?: React.ReactNode;
  icon?: React.ReactNode;
  disabled?: boolean;
  value?: string;
  className?: string;
};
```

**破坏性风险**：中（PR-4 Batch D 新增）。`type: radio` 须 RadioGroup 上下文为 evolving 约束。

**兼容策略**：简单选项用 Checkbox + Label 列表降级。

### ConfirmHost / useConfirm — stable

```ts
export type ConfirmOptions = {
  title: React.ReactNode;
  description?: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
};

export function confirm(options: ConfirmOptions): Promise<boolean>;
export function ConfirmHost(): JSX.Element;
```

**破坏性风险**：低（PR-4 Batch D 新增，PR-E runtime 验收后晋升）。根级单例 + Promise API；须挂载 `<ConfirmHost />`。

**兼容策略**：单次确认用受控 AlertDialog；禁止 `window.confirm`。

### useFormList / FormList — stable

```ts
export type UseFormListOptions<T> = { initialValue?: T[]; min?: number; max?: number };
export type FormListField<T> = { id: string; value: T };

export function useFormList<T>(options?: UseFormListOptions<T>): {
  fields: FormListField<T>[];
  values: T[];
  add: (value?: T) => void;
  remove: (index: number) => void;
  move: (from: number, to: number) => void;
  replace: (index: number, value: T) => void;
  setValues: (next: T[]) => void;
  canAdd: boolean;
  canRemove: boolean;
};

// compound: FormList / FormListItems / FormListAdd / useFormListContext
```

**破坏性风险**：低（PR-E Batch E 新增，runtime 验收后晋升）。`move` / `setValues` 为 additive。

**Ant Design 别名**：`Form.List` → `FormList` + `useFormList`。

**兼容策略**：静态字段列表用多个 FormField；复杂校验用 react-hook-form field array 降级。

### useScrollToFirstError — stable

```ts
export function scrollToFirstError(root?: HTMLElement | null): void;
export function useFormSubmit(options: {
  onValid?: () => void;
  onInvalid?: () => void;
  scrollToFirstError?: boolean;
  formRef?: React.RefObject<HTMLElement>;
}): (event: React.FormEvent) => void;
```

**破坏性风险**：低（PR-E Batch E 新增，runtime 验收后晋升）。依赖 `FormField` 输出 `[data-field-invalid]`；`FormProvider scrollToFirstError` 为 additive 级联开关。

**Ant Design 别名**：`Form` scrollToFirstField → `scrollToFirstError` / `useFormSubmit`。

**兼容策略**：短表单用手动 `formRef.current?.querySelector`；toast-only 错误降级。

### RadioButtonGroup — stable

```ts
export type RadioButtonGroupProps = RadioGroupPrimitive.RootProps & {
  orientation?: "horizontal" | "vertical";
  size?: "sm" | "md" | "lg";
  block?: boolean;
};
// 导出: RadioButtonGroup, RadioButton
```

**破坏性风险**：低（PR-E Batch E 新增，runtime 验收后晋升）。`block` 全宽按钮组为 additive。

**Ant Design 别名**：`Radio.Button` / `Radio.Group optionType="button"` → `RadioButtonGroup` + `RadioButton`。

**兼容策略**：圆点单选用 `RadioGroup`；选项多用 `Select` 降级。

### PasswordInput — stable

```ts
export type PasswordInputProps = Omit<InputProps, "type"> & {
  showToggle?: boolean;
};
```

**破坏性风险**：低（PR-E Batch E 新增，runtime 验收后晋升）。仅 show/hide toggle；**不含** copy/rotate。

**兼容策略**：API Key/token 用 `SecretInput`；简单登录密码可用 `AdvancedInput type="password"` 降级。

### FormFieldset — stable

```ts
export type FormFieldsetProps = {
  legend?: React.ReactNode;
  description?: React.ReactNode;
  disabled?: boolean;
  className?: string;
  children: React.ReactNode;
};
```

**破坏性风险**：低（PR-E Batch E 新增，runtime 验收后晋升）。语义 `<fieldset>` 分组；`disabled` 级联禁用子控件。

**兼容策略**：视觉分组仍可用 `FormSection`；只读详情用 `DescriptionList`。

### DataTableColumnFilter — stable

```ts
export type ColumnFilterConfig =
  | { type: "select"; options: { label: string; value: string }[] }
  | { type: "text"; placeholder?: string };

export type DataTableColumnFilterProps = {
  config: ColumnFilterConfig;
  value?: unknown;
  onApply: (value: unknown) => void;
  columnTitle?: React.ReactNode;
};
```

**破坏性风险**：低（PR-E Batch E 新增，runtime 验收后晋升）。`DataTable` 列定义 `filter` / `filteredValue` 为 additive；`virtual` 模式忽略列 filter 并 `console.warn`。

**Ant Design 别名**：`Table` `filterDropdown` / `onFilter` → `columns[].filter` + `DataTableColumnFilter`。

**兼容策略**：全局筛选用 DataTableCard toolbar；简单列筛用手写 Popover 降级。

### ImagePreview — stable

```ts
export type ImagePreviewProps = {
  src: string;
  alt: string;
  fallback?: React.ReactNode;
  preview?: boolean;
  className?: string;
  thumbnailClassName?: string;
};
```

**破坏性风险**：低（PR-E Batch E 新增，runtime 验收后晋升）。缩略图 + Radix Dialog 灯箱；`preview={false}` 仅展示缩略图。

**Ant Design 别名**：`Image` `preview` → `ImagePreview`。

**兼容策略**：只读大图用 `<img>` + 新窗口；多图画廊用 Carousel 降级。

### StatTrend — stable

```ts
export type StatTrendProps = {
  direction: "up" | "down" | "flat";
  value: React.ReactNode;
  className?: string;
};
```

**破坏性风险**：低（PR-E Batch E 新增，runtime 验收后晋升）。`StatMetric` `trend` slot 组合为 additive。

**兼容策略**：手写 delta 文案 + lucide 图标降级。

### ClipboardButton — stable

```ts
export type ClipboardButtonProps = {
  value: string;
  onCopied?: () => void;
} & ButtonProps;
```

**破坏性风险**：低（PR-E Batch E 新增，runtime 验收后晋升）。复制成功/失败 Sonner toast；**不含** mask/reveal。

**兼容策略**：密钥/API Key 用 `SecretInput` 或 `ApiKeyRevealPanel`；只读代码用 `CodeBlock` copy。

## PR-GH 数据展示与命令式浮层（React 模板 · stable）

> PR-GH 批次经 example runtime（`ui-gh-batch` specimen）与 `verify:runtime` 验收后，自 evolving 晋升为 **stable**。仅 additive 扩展；不得删除导出名或 props。

### TreeTable — stable

```ts
export type TreeTableProps<T extends HierarchicalNode = HierarchicalNode> = {
  dataSource: T[];
  columns: DataTableColumn<T>[];
  treeColumnTitle?: React.ReactNode;
  expandedKeys?: string[];
  onExpandedKeysChange?: (keys: string[]) => void;
  checkable?: boolean;
  checkedKeys?: string[];
  onCheckedKeysChange?: (keys: string[]) => void;
  loadData?: LoadDataFn;
  pagination?: TablePagination;
  loading?: boolean;
  virtual?: boolean | { rowHeight?: number; overscan?: number };
  scroll?: { y: number };
  // columns[].filter — 复用 DataTableColumnFilter（PR-E stable）
};
// 导出: TreeTable；配套 flattenTreeRows / TreeTableVirtualBody
```

**破坏性风险**：低。`virtual` / 列 `filter` 为 PR-GH additive；虚拟滚动 peer：`@tanstack/react-virtual`。

**兼容策略**：浅层树用 `DataTable` + 缩进列；只读层级用 `Tree`。

### Tree — stable（`draggable` additive · PR-GH）

```ts
export type TreeProps = {
  nodes: TreeNode[];
  selectedKeys?: string[];
  expandedKeys?: string[];
  onSelect?: (id: string, node: TreeNode) => void;
  onExpand?: (keys: string[]) => void;
  checkable?: boolean;
  checkedKeys?: string[];
  onCheck?: (keys: string[]) => void;
  draggable?: boolean;
  onDrop?: (info: TreeDropInfo) => void;
  className?: string;
};
```

**破坏性风险**：低。`draggable` / `onDrop` 为 PR-GH additive（`@dnd-kit/*` peer）。

**兼容策略**：不可拖拽场景省略 `draggable`；表格内层级用 `TreeTable`。

### ContextMenu — stable

| 导出 | 说明 |
|---|---|
| `ContextMenu` / `Trigger` / `Content` / `Item` / `Sub` / `CheckboxItem` / `RadioItem` … | Radix Context Menu compound；TailAdmin token 样式 |
| peer | `@radix-ui/react-context-menu` ^2.x |

**破坏性风险**：低。与 shadcn ContextMenu 结构对齐；className 透传 additive。

**兼容策略**：行内操作用 `DropdownMenu`；表格批量用 `ActionBar`。

### DialogHost / useDialog — stable

```ts
export type DialogOpenOptions = {
  title?: React.ReactNode;
  content: React.ReactNode;
  size?: "xs" | "sm" | "md" | "lg" | "xl" | "full";
  onClose?: () => void;
};

export function openDialog(options: DialogOpenOptions): void;
export function closeDialog(): void;
export function useDialog(): { open: typeof openDialog; close: typeof closeDialog };
export function DialogHost(): JSX.Element; // 根节点挂载一次
```

**破坏性风险**：低。命令式单例 + `useSyncExternalStore`；须与 `ConfirmHost` 并存时各挂各的 Host。

**兼容策略**：受控场景用 `Dialog` / `FormDialog`；确认框用 `useConfirm` + `ConfirmHost`。

### useSortableList — stable

```ts
export function useSortableList<T>(options: {
  items: T[];
  getId: (item: T) => string;
  onReorder: (items: T[]) => void;
}): { sensors; ids; handleDragEnd };

export function useSortableItem(id: string): {
  attributes; listeners; setNodeRef; style; isDragging;
};
```

**破坏性风险**：低。peer：`@dnd-kit/core` + `@dnd-kit/sortable` + `@dnd-kit/utilities`。

**兼容策略**：简单列表用 `OrderList`；表格行排序用 `DataTable` 受控 + 手写 move。

### OrderList — stable

```ts
export type OrderListProps<T> = {
  items: T[];
  getId: (item: T) => string;
  renderItem: (item: T, index: number) => React.ReactNode;
  onReorder: (items: T[]) => void;
  className?: string;
};
```

**破坏性风险**：低。内部组合 `useSortableList`。

**兼容策略**：双栏穿梭用 `Transfer`；只读顺序用 `List`。

### ImageCompare — stable

```ts
export type ImageCompareProps = {
  beforeSrc: string;
  afterSrc: string;
  beforeLabel?: string;
  afterLabel?: string;
  initialPosition?: number;
  className?: string;
};
```

**破坏性风险**：低。纯 CSS 滑块对比，无第三方 peer。

**兼容策略**：配置 Diff 文本用 `DescriptionDiff`；多图用 `ImagePreview` 灯箱。

### InputGroup — stable

```ts
export type InputGroupProps = {
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  addonBefore?: React.ReactNode;
  addonAfter?: React.ReactNode;
  className?: string;
  children: React.ReactElement<{ className?: string }>;
};
```

**破坏性风险**：低。单 child `cloneElement` 合并圆角；addon 与 affix 互斥组合由调用方保证。

**兼容策略**：简单前后缀用 `AdvancedInput` prefix/suffix。

### StatCountdown — stable

```ts
export type StatCountdownProps = {
  value: number | Date;
  format?: "dhms" | "hms";
  onFinish?: () => void;
  className?: string;
};
```

**破坏性风险**：低。`StatMetric` 倒计时 slot 组合 additive。

**兼容策略**：静态截止文案用手写 `StatMetric` value。

### Prose / Blockquote — stable

| 组件 | 关键契约 |
|---|---|
| `Prose` | `children?` 或可信来源 `html?`；`prose` typography 容器 |
| `Blockquote` | `cite?` + 标准 blockquote attributes 透传 |

**破坏性风险**：低。

**兼容策略**：长文详情用 `Card` + `prose` class；短引用用 `Alert`。

### SkipNav / VisuallyHidden — stable

| 组件 | 关键契约 |
|---|---|
| `SkipNav` | `href` 默认 `#main-content`；键盘聚焦跳过导航 |
| `VisuallyHidden` | 屏幕阅读器-only 文本/装饰 |

**破坏性风险**：低。纯 a11y 辅助，无状态。

**兼容策略**：跳链用手写 `sr-only` link；装饰性图标用 `aria-hidden`。

### Image — stable

```ts
export type ImageProps = React.ImgHTMLAttributes<HTMLImageElement> & {
  rounded?: "none" | "md" | "lg" | "full";
  fallback?: React.ReactNode;
  lazy?: boolean;
};
```

**破坏性风险**：低。`fallback` 加载失败占位 additive。

**兼容策略**：灯箱预览用 `ImagePreview`。

### Listbox — stable

```ts
export type ListboxProps = {
  options: ListboxOption[];
  value: string | string[];
  onChange: (value: string | string[]) => void;
  multiple?: boolean;
  className?: string;
  "aria-label"?: string;
};
```

**破坏性风险**：低。ARIA listbox 模式；多选 checkbox 组合。

**兼容策略**：表单内单选用 `Select`；命令面板用 `Command`。

## Ant Design 别名映射（PR-E）

| Ant Design | TailAdmin Radix | 说明 |
|---|---|---|
| `Form.List` | `FormList` + `useFormList` | 动态重复字段 compound |
| `Form` scrollToFirstField | `scrollToFirstError` / `useFormSubmit` | 配合 `FormField` `[data-field-invalid]` |
| `Radio.Button` | `RadioButtonGroup` + `RadioButton` | 按钮式单选 |
| `Table.filterDropdown` | `DataTableColumnFilter` | 列头 Popover 筛选 |
| `Image.preview` | `ImagePreview` | 缩略图灯箱 |
| `Tag.CheckableTag` | `Chip` `checkable` | 见 `data-display-template.md` |
| `Drawer` variant | `Sheet` `variant` | temporary / persistent / mini |
| `Modal` fullscreen | `FormDialog` `fullScreen` / `size="full"` | 全屏短表单 |

## BI 能力包（React 模板 · additive）

### FilterBar / CrossFilterDashboard — stable · additive

| 组件 | 关键契约 |
|---|---|
| `FilterBar` | `filters: FilterChip[]`、`onRemove`、`onClearAll`、`scope?: "global" \| "local"` |
| `CrossFilterDashboard` | 组合 `FilterBar` + `DashboardGrid`；cross-filter chips 受控 |

**破坏性风险**：无（G36 additive）。**兼容策略**：每图独立 DatePicker 降级。

### DrillDownDashboard / DrillDetailTable — stable · additive

| 组件 | 关键契约 |
|---|---|
| `DrillBreadcrumb` | `items: { label, onClick? }[]` 下钻路径 |
| `DrillDetailTable` | 分页、导出状态、`forbidden`/`error`/`empty` 内置 |
| `DrillDownDashboard` | `view: "chart" \| "detail"` 受控切换 |

**破坏性风险**：无（G37 additive）。**兼容策略**：直接跳明细 Table 降级。

### ExportMenu / ExportJobPanel — stable · additive

| 组件 | 关键契约 |
|---|---|
| `ExportMenu` | `context: ExportContext`、`formats?`、`onExport(format)`、`loading?` |
| `ExportJobPanel` | `jobs: ExportJob[]` 状态 queued/exporting/ready/failed/expired |

**破坏性风险**：无（G38 additive）。**兼容策略**：同步 CSV 下载降级。

### ShareEmbedDialog — stable · additive

| 组件 | 关键契约 |
|---|---|
| `ShareEmbedDialog` | `permission: view/edit/public/embed`、`onGenerate`、`onRevoke`、`allowedDomains?` |
| `ShareAccessDashboard` | 分享入口 + 租户隔离组合 |

**破坏性风险**：无（G39 additive）。**兼容策略**：内部 RBAC 链接降级。

### CodeEditor / AiCodeGeneratorShell — stable · additive

| 组件 | 关键契约 |
|---|---|
| `CodeEditor` | 受控 `value`/`onChange`、`mode: edit/preview/split`、`dirty?`、`onSave?` |
| `AiCodeGeneratorShell` | 提示词 + `CodeEditor` + 生成/保存组合 |

**破坏性风险**：低（G40 additive，不替换 `CodeBlock`）。**兼容策略**：只读场景仍用 `CodeBlock`。

## Gateway 控制平面（React 模板 · stable · additive G27）

| 组件 | 关键契约 | 风险 |
|---|---|---|
| `DeploymentModeMatrix` | `mode: DeploymentMode`、`onModeChange`、`options?` | 低 · additive |
| `BalanceQuotaSummary` | `balanceCents`、`quotaPercent`、`quotaState?` | 低 · additive |
| `SyncHealthPanel` | `tracks: SyncTrack[]`、`onRetry?` | 低 · additive |
| `EndpointProbeTable` | `rows: EndpointProbeRow[]`、`onProbe?` | 低 · additive |
| `LicenseIssuePanel` | `edition`、`expiresAt`、`status?`、`onIssue?` | 低 · additive |
| `ApiKeyRevealPanel` | `rawKey?`、`onReveal?`、`onCopy?`、`onRotate?` | 低 · additive |
| `ControlPlaneHub` | 组合上述子面板；全部 KPI/sync/endpoints props optional | 低 · additive |

**破坏性风险**：无（G27 additive）。子组件可独立使用，Hub 仅页面组合。

**兼容策略**：单独使用 `DeploymentModeMatrix` + `DataTableCard` 降级；探测失败回退静态 Badge 列表。

## DevOps / CI/CD（React 模板 · stable · additive G26/G40）

| 组件 | 关键契约 | 风险 |
|---|---|---|
| `PipelineStageBar` | `stages: PipelineStage[]`、`activeStageId?` | 低 · additive |
| `LogStreamPanel` | `lines: LogLine[]`、`paused?`、`onPauseToggle?`、`search?` | 低 · additive |
| `ArtifactTable` | `rows: ArtifactRow[]`、`onDownload?` | 低 · additive |
| `ApprovalTimeline` | `steps: ApprovalStep[]`、`currentStepId?` | 低 · additive |
| `DangerZone` | `actions: DangerAction[]`、`onAction` | 低 · additive |
| `RollbackDialog` | `currentVersion`、`targetVersion`、`onConfirm` | 低 · additive |
| `DiffViewer` | `before`、`after`、`language?` | 低 · additive |
| `FileBrowser` | `nodes: FileNode[]`、`onSelect?` | 低 · additive |
| `MrDetailShell` | MR/PR 元数据 + diff + timeline 组合 | 低 · additive |
| `CicdRunDetail` | `runId`、`stages`、`logs`、`artifacts` 受控；`onRetry?`/`onCancel?` | 低 · additive |
| `AiCodeGeneratorShell` | 提示词 + `CodeEditor` + 生成/保存（G40 additive） | 低 · additive |

**破坏性风险**：无（G26/G40 additive）。`CicdRunDetail` 内部 state（pause/search/severity）为展示层，不影响外部契约。

**兼容策略**：`PipelineStageBar` + `LogStreamPanel` 独立组合；无 diff 时回退 `CodeBlock`。

## 布局能力包（React 模板 · stable · additive G23）

| 组件 | 关键契约 | 风险 |
|---|---|---|
| `AppLayout` | `sidebar`、`header`、`children` slot 组合 | 低 · stable |
| `AppSidebar` | `sections: NavSection[]`、`collapsed?`、`onNavigate?` | 低 · stable |
| `AppHeader` | `search?`、`actions?`、`userMenu?` | 低 · stable |
| `HubTabsLayout` | `tabs: HubTabDef[]`、`activeTab`、`onTabChange` | 低 · additive |
| `MasterDetailOps` | 左列表 + 右多 Tab 详情 + 高度链 | 低 · additive |
| `ThreeColumnWorkspace` | 左树 + 中列表 + 右工作区 | 低 · additive |
| `FormPageShell` | `title`、`breadcrumbs?`、`dirty?`、`onSave?`、`stickyActions?` | 低 · additive |
| `FormSection` | 分组标题 + 描述 + children | 低 · additive |
| `FormDrawer` | Drawer 内表单 + dirty 关闭确认 | 低 · additive |
| `DescriptionList` | `items: { label, value }[]` 查看态 | 低 · additive |
| `DescriptionDiff` | `before`/`after` 字段对比 | 低 · additive |

**破坏性风险**：低。壳层比例（侧栏 290px/90px）变更视为 visual-breaking，须 migration note。

**兼容策略**：简单页面仍用 `AppLayout` + `Card`；Hub 页降级 Tabs + 单内容区。

## 表单组合（React 模板 · stable · additive G22/G30）

| 组件 | 关键契约 | 风险 |
|---|---|---|
| `AdvancedInput` 家族 | text/search/password/url/email/number/currency/percent/mask/OTP/token | 低 · stable |
| `FormDialog` | 短表单 Dialog + dirty 关闭确认 | 低 · additive G30 |
| `QueryShell` | `loading`/`error`/`empty`/`refetching` 四态 | 低 · stable |
| `DataTableCard` | 表格外壳 + 筛选栏 + 分页 + 四态 | 低 · stable |
| `SecretInput` | mask/copy/reveal 密钥输入 | 低 · stable |

**破坏性风险**：低。`AdvancedInput` variant 仅 additive；删除 variant 视为 breaking。

**兼容策略**：简单字段回退 shadcn `Input` + `Label`；数据四态回退 `Spinner` + 空 div。

## 治理安全（React 模板 · stable）

| 组件 | 关键契约 | 风险 |
|---|---|---|
| `PermissionMatrix` | `roles`、`permissions`、`onToggle`、`inherited?` | 低 · additive G30 |
| `AuditLogTable` | 时间范围、操作者筛选、`onExport`、`onRowClick` | 低 · additive G30 |
| `AuthProviderWizard` | `provider: ldap/oauth/oidc/saml` 四步、`onProbe` | 低 · additive G31 |
| `SecretKeyPanel` | `masked`、`onCopy`、`onRotate`、`onRevoke` | 低 · additive G31 |

**兼容策略**：简单 Table + Badge 降级；密钥展示回退 `SecretInput`。

## PaaS 资源（React 模板 · stable）

| 组件 | 关键契约 | 风险 |
|---|---|---|
| `ResourceTable` | `resourceType`、`rows`、`onRowClick`、状态列 | 低 · additive G32 |
| `CapacityCard` | CPU/Memory/Disk/QPS/Latency/Replica KPI | 低 · additive G32 |
| `ConfigDiff` | `before`/`after`、`riskHint?`、`requiresRestart?` | 低 · additive G32 |
| `BackupTable` | 备份状态 available/expired/restoring/failed | 低 · additive G32 |
| `PaasOpsDangerFlow` | 伸缩/重启/故障转移二次确认 | 低 · additive G32 |

**兼容策略**：通用 `DataTableCard` + `StatusBadge` 降级。

## 破坏性变更风险总表

| 组件 | 风险等级 | 主要风险点 | 当前状态 |
|---|---|---|---|
| Chart | 低 | palette key 删除、默认 animations | 无已知破坏性 |
| FullCalendar | 低 | toolbar 默认视图变更 | 无已知破坏性 |
| Kanban | 中 | G33 前无 Board 组件；theme class 稳定 | theme stable；Board additive |
| Maps | 低 | 默认 center/zoom | 无已知破坏性 |
| Vector Maps | 低 | 固定高度、region style key | 无已知破坏性 |
| Editor | 低 | CodeBlock additive（G35） | stable + CodeBlock |
| Carousel | 低 | Swiper selector 耦合 | 无已知破坏性 |
| DatePicker | 低 | — | stable |
| MultiSelect | 低 | — | stable |
| Cascader | 中 | PR-1 Batch A 新增；loadData/multiple | evolving |
| TreeSelect | 中 | PR-1 Batch A 新增；treeCheckable | evolving |
| Transfer | 低 | PR-1 基础 + PR-GH `targetSortable` additive | stable |
| Timeline | 中 | PR-2 Batch B 新增；mode/alternate | evolving |
| AnchorNav | 中 | PR-2 Batch B 新增；usePageNav | evolving |
| Tour | 中 | PR-2 Batch B 新增；driver.js peer | evolving |
| List | 中 | PR-2 Batch B 新增；density/slots | evolving |
| TimePicker | 中 | PR-3 Batch C 新增；range/disabledHours | evolving |
| Mentions | 中 | PR-3 Batch C 新增；onSearch | evolving |
| Rating | 中 | PR-3 Batch C 新增；allowHalf | evolving |
| ColorPicker | 中 | PR-3 Batch C 新增；react-colorful peer | evolving |
| Editable | 中 | PR-3 Batch C 新增；EditableTextarea | evolving |
| Kbd | 低 | PR-4 Batch D 新增；size 变体 | evolving |
| ToggleTip | 低 | PR-4 Batch D 新增；click trigger | evolving |
| ActionBar | 低 | PR-4 Batch D 新增；actions slot | evolving |
| ChoiceCard | 中 | PR-4 Batch D 新增；radio RadioGroup | evolving |
| ConfirmHost | 低 | PR-4/PR-E；Promise confirm API | stable |
| useFormList / FormList | 低 | PR-E；move/setValues additive | stable |
| useScrollToFirstError | 低 | PR-E；data-field-invalid 耦合 | stable |
| RadioButtonGroup | 低 | PR-E；block 变体 additive | stable |
| PasswordInput | 低 | PR-E；无 copy/rotate | stable |
| FormFieldset | 低 | PR-E；fieldset 分组 | stable |
| DataTableColumnFilter | 低 | PR-E；virtual+filter warn | stable |
| ImagePreview | 低 | PR-E；灯箱预览 | stable |
| StatTrend | 低 | PR-E；StatMetric trend slot | stable |
| ClipboardButton | 低 | PR-E；轻量复制 | stable |
| TreeTable | 低 | PR-GH；virtual / 列 filter additive | stable |
| Tree | 低 | PR-GH；`draggable` / `onDrop` additive | stable |
| ContextMenu | 低 | PR-GH；Radix compound | stable |
| DialogHost / useDialog | 低 | PR-GH；命令式单例 Dialog | stable |
| useSortableList | 低 | PR-GH；dnd-kit 排序 hook | stable |
| OrderList | 低 | PR-GH；垂直拖拽列表 | stable |
| ImageCompare | 低 | PR-GH；双图滑块 | stable |
| InputGroup | 低 | PR-GH；addon/prefix/suffix | stable |
| StatCountdown | 低 | PR-GH；倒计时 KPI | stable |
| Prose / Blockquote | 低 | PR-GH；排版容器 | stable |
| SkipNav / VisuallyHidden | 低 | PR-GH；a11y 辅助 | stable |
| Image | 低 | PR-GH；fallback / aspectRatio | stable |
| Listbox | 低 | PR-GH；ARIA listbox | stable |
| FileUpload | 低 | — | stable |
| FileDropzone | 低 | additive 新组件 | stable |
| ThemeToggle | 低 | 导出名 vs 概念名 | 文档化 alias |
| Command | 低 | `href` 需 react-router | 文档化 onSelect |
| FilterBar / CrossFilterDashboard | 低 | additive G36 | 无已知破坏性 |
| DrillDown / Export / Share BI | 低 | additive G37–G39 | 无已知破坏性 |
| CodeEditor / AiCodeGeneratorShell | 低 | additive G40 | 不替换 CodeBlock |
| Gateway 控制平面 | 低 | additive G27 | 子组件可独立降级 |
| DevOps / CI/CD | 低 | additive G26/G40 | CicdRunDetail 受控 props |
| 布局能力包 | 低 | AppLayout stable；Hub/MasterDetail additive | 壳层比例 visual-breaking |
| 表单组合 | 低 | AdvancedInput/QueryShell stable | variant 删除视为 breaking |
| Gov / PaaS 模板 | 低 | additive G30–G32 | 无已知破坏性 |

## 检索入口

| 意图 | 读 |
|---|---|
| 兼容原则与 migration 模板 | `backward-compatibility.md` |
| Skill 快照固定与升级 | `version-pinning-guide.md` |
| 预防性迁移场景 | `migration-scenarios.md` |
| migration note 填写模板 | `migration-note-template.md` |
| 契约自动审计 | `create-design-system/scripts/audit_compat_contracts.py` |
| 扩展性审计 | `extension-audit.md` |
| 组件索引 | `component-index.md#api-contracts` |
