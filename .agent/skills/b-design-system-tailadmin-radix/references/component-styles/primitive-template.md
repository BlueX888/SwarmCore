# Primitive 组件 — TailAdmin × shadcn

## variant-scale

跨组件变体词汇表（Agent 生成时必须遵守，禁止把校验态当外观 variant）。

| 轴 | 枚举 | 适用组件 |
|---|---|---|
| appearance | solid / subtle / surface / outline / ghost / plain | Button, Badge, Alert（T2） |
| inputSkin | outlined / filled / borderless / underlined | Input, Select, DatePicker（T2） |
| severity | brand / success / error / warning / info / neutral | Alert, Badge, Chip（T2） |
| size | xs / sm / md / lg / xl | 多数控件 |
| fieldState | default / error / success / warning / validating / disabled / readonly | 表单族 |
| formLayout | vertical / horizontal / inline | FormSection, FormField（经 FormContext 级联） |

正交：`appearance × severity × size × fieldState × dark`

迁移别名（文档用，非主 API）：antd solid→solid；MUI contained→solid；MUI filled input→inputSkin filled；Chakra flushed→underlined。

## Button

**源**：`ui/button/Button.tsx` → **shadcn** `Button` + `cva`

```tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-lg text-sm font-medium transition-colors focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-brand-500 text-white shadow-theme-xs hover:bg-brand-600 disabled:bg-brand-300",
        outline: "bg-white text-gray-700 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-400 dark:ring-gray-700 dark:hover:bg-white/[0.03]",
      },
      size: {
        sm: "px-4 py-3",
        md: "px-5 py-3.5",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  }
);
```

- 图标：`startIcon`/`endIcon` → children 内 `<Icon className="size-5" />`
- 不用 `variant="default"` 作 primary — 显式 `primary`
- P3-B 扩展：`dashed`（虚线描边次要操作）、`filled`（灰底填充工具栏按钮）
- `ButtonGroup`：`attached` 首尾圆角、中间无缝拼接
- `loading` / `loadingText` / `spinnerPlacement` 覆盖异步提交态；loading 时自动 `aria-busy` 并禁用原生 button。
- `IconButton`、`CloseButton`、`DownloadTrigger` 与 Button 共用 recipe；IconButton 必须提供 `aria-label`，DownloadTrigger 支持 string、Blob、File 或 Promise payload。

## Badge

**源**：`ui/badge/Badge.tsx` — **状态 pill**（运行正常/待审批），非数字角标、非可删筛选标签。

```tsx
// variant: light | solid
// color: primary | success | error | warning | info | light | dark
```

- 标签筛选 → `templates/ui/chip.tsx`
- 数字角标 / dot → `templates/ui/count-badge.tsx`

可复制模板：`templates/ui/badge.tsx`

## Chip

**源**：MUI Chip / antd Tag — 可关闭筛选标签、权限标签。

```tsx
// variant: filled | outlined
// color: brand | success | error | warning | info | neutral
// onDelete 可选
```

可复制模板：`templates/ui/chip.tsx`

## CountBadge

**源**：antd Badge / MUI Badge — 叠在图标或头像上的 count/dot/status。

```tsx
<CountBadgeAnchor badge={<CountBadge count={8} />}>
  <Bell className="size-5" />
</CountBadgeAnchor>
```

可复制模板：`templates/ui/count-badge.tsx`

## Checkbox

**源**：`form/input/Checkbox.tsx` → shadcn `Checkbox` + Radix

```tsx
// Root: size-5 rounded-md border-gray-300
// checked: border-transparent bg-brand-500 + white Check icon
// focus: focus-visible:ring-3 focus-visible:ring-brand-500/20
// disabled: opacity-60 cursor-not-allowed
// 与 Label 组合: flex items-center gap-3
// PR-4: indeterminate prop → checked="indeterminate" 表头半选
```

可复制模板：`templates/ui/checkbox.tsx`

## Kbd

**源**：shadcn/ui Kbd / GitHub 快捷键 pill — 命令面板、菜单、Tooltip 内展示组合键。

```tsx
import { Kbd } from "@/components/ui/kbd";

<span className="inline-flex items-center gap-1">
  <Kbd>⌘</Kbd>
  <Kbd>K</Kbd>
</span>
```

- `size`: sm / md（默认 md）
- 语义元素 `<kbd>`；多键并排时外层 flex gap-1

可复制模板：`templates/ui/kbd.tsx`

## Radio

**源**：`form/input/Radio.tsx` → shadcn `RadioGroup` + Radix

```tsx
// Item: size-5 rounded-full border-[1.25px]
// checked: border-brand-500 bg-brand-500 + inner size-2 bg-white dot
// Group: grid gap-3
// label: text-sm font-medium text-gray-700 dark:text-gray-400
```

可复制模板：`templates/ui/radio-group.tsx`

## Switch

**源**：`form/switch/Switch.tsx` → shadcn `Switch` + Radix

```tsx
// track: h-6 w-11 rounded-full
// checked: bg-brand-500; unchecked: bg-gray-200 dark:bg-white/10
// thumb: size-5 bg-white translate-x-5 when checked
// transition: duration-150 ease-linear
```

可复制模板：`templates/ui/switch.tsx`

## Input

**源**：`form/input/InputField.tsx` → shadcn `Input`

正交轴（见 `#variant-scale`）：

- `inputSkin`: outlined（默认）| filled | borderless | underlined
- `fieldState`: default | error | success | warning
- `variant` 为 **已废弃别名**，映射到 `fieldState`

```tsx
<Input inputSkin="filled" fieldState="error" placeholder="集群名称" />
```

可复制模板：`templates/ui/input.tsx`

## Textarea

**源**：`form/input/TextArea.tsx` → shadcn `Textarea`

```tsx
// base: min-h-[120px] w-full rounded-lg border px-4 py-3 text-sm shadow-theme-xs resize-y
// variants: default | error | success（与 Input 对齐）
// focus: focus-visible:border-brand-300 focus-visible:ring-3 focus-visible:ring-brand-500/20
// disabled: opacity-40 bg-gray-100 cursor-not-allowed
```

可复制模板：`templates/ui/textarea.tsx`

## Select

**源**：`form/Select.tsx` → shadcn `Select` + Radix

```tsx
// Trigger: h-11 rounded-lg border-gray-300 shadow-theme-xs
// Content: rounded-xl border-gray-200 shadow-theme-lg dark:bg-gray-dark
// Item: px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-white/5
// Icon: ChevronDown size-4 opacity-50
```

可复制模板：`templates/ui/select.tsx`

## Label

`text-sm font-medium text-gray-700 dark:text-gray-300`

## Avatar

`rounded-full`；尺寸 `size-8` / `size-10` / `size-12` / `size-16`（sm/md/lg/xl）；fallback 用 `AvatarFallback name="..."` 首字母 + 哈希 pastel。

状态指示器：`status="online"|"offline"|"busy"`；右下角圆点 `border-white dark:border-gray-900`。

可复制模板：`templates/ui/avatar.tsx`

```tsx
<Avatar size="md" status="online">
  <AvatarImage src={user.avatar} alt={user.name} />
  <AvatarFallback name={user.name} />
</Avatar>
```

## Separator

**源**：Radix `@radix-ui/react-separator`；TailAdmin 菜单/表单分组线。

```tsx
import { Separator, SeparatorWithLabel } from "@/components/ui/separator";

<Separator />
<Separator orientation="vertical" className="mx-2 h-6" />
<SeparatorWithLabel label="高级选项" labelPosition="center" />
```

可复制模板：`templates/ui/separator.tsx`

## SegmentedControl

**源**：`ui/buttons-group/PrimaryButtonGroup.tsx`、`ui/tabs/DefaultTab.tsx` pill nav。

- `type="single"`（默认，至少一项选中）/ `multiple`
- `size`: sm / md / lg；`block` 等宽铺满；`orientation`: horizontal / vertical

```tsx
import { SegmentedControl, SegmentedControlItem } from "@/components/ui/segmented-control";

<SegmentedControl type="single" defaultValue="week" block>
  <SegmentedControlItem value="day">日</SegmentedControlItem>
  <SegmentedControlItem value="week">周</SegmentedControlItem>
  <SegmentedControlItem value="month">月</SegmentedControlItem>
</SegmentedControl>
```

可复制模板：`templates/ui/segmented-control.tsx`

## Accordion

**源**：sidebar `Collapsible`、FAQ 页；Radix `@radix-ui/react-accordion`。

- `type`: single / multiple；`variant`: outline / enclosed；`size`: sm / md / lg

```tsx
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

<Accordion type="single" collapsible defaultValue="billing">
  <AccordionItem value="billing" variant="outline">
    <AccordionTrigger>账单与发票</AccordionTrigger>
    <AccordionContent>账单周期、发票抬头与税务信息。</AccordionContent>
  </AccordionItem>
</Accordion>
```

可复制模板：`templates/ui/accordion.tsx`

## Slider

**源**：antd Slider / MUI Slider — 配额、阈值、音量等连续值。

- Radix `@radix-ui/react-slider`；`orientation`: horizontal / vertical；`size`: sm / md / lg
- 单 thumb 默认；`value`/`defaultValue` 数组长度 > 1 时自动渲染 range 双 thumb

```tsx
import { Slider } from "@/components/ui/slider";

<Slider defaultValue={[30]} max={100} step={1} />
```

可复制模板：`templates/ui/slider.tsx`

## Steps

**源**：antd Steps / MUI Stepper — 向导、审批、开通流程。

- `orientation`: horizontal / vertical；`variant`: solid / subtle；`size`: sm / md / lg
- `items: StepItem[]` + `current` 索引；单项可覆盖 `status`: wait / process / finish / error

```tsx
import { Steps } from "@/components/ui/steps";

<Steps
  current={1}
  items={[
    { id: "basic", title: "基本信息" },
    { id: "perm", title: "权限配置" },
    { id: "confirm", title: "确认提交" },
  ]}
/>
```

可复制模板：`templates/ui/steps.tsx`（通用）；CI 流水线阶段条见 `templates/devops/pipeline-stage-bar.tsx`。
