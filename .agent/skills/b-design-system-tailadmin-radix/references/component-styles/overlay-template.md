# Overlay 组件 — Dialog / Dropdown / Popover / Tooltip

源项目为手写浮层；**实现必须用 shadcn/Radix**，视觉对齐 TailAdmin。

## Dialog（替代 Modal）

**源**：`ui/modal/index.tsx`

| 元素 | TailAdmin 类 | shadcn 映射 |
|---|---|---|
| Overlay | `bg-gray-400/50 backdrop-blur-[32px]` | `DialogOverlay` className 覆盖 |
| Content | `rounded-3xl bg-white dark:bg-gray-900` | `DialogContent` |
| Close | `rounded-full bg-gray-100 h-9.5 w-9.5` | `DialogClose` + 圆形按钮 |
| z-index | `z-99999` | `className="z-99999"` |

```tsx
<Dialog open={open} onOpenChange={setOpen}>
  <DialogContent className="rounded-3xl sm:max-w-lg z-99999">
    ...
  </DialogContent>
</Dialog>
```

- ESC + backdrop 关闭：Radix 默认
- `useModal` hook → 改为 `useState` + `Dialog`

## FormDialog fullScreen {#formdialog-fullscreen}

**模板**：`templates/ui/form-dialog.tsx`

短表单 Dialog 全屏变体（PR-E）— 复杂配置仍用 Drawer / 独立页。

| prop | 类型 | 说明 |
|---|---|---|
| `fullScreen` | `boolean?` | 与 `size="full"` 等价 |
| `size` | `"xs" \| "sm" \| "md" \| "lg" \| "xl" \| "full"` | `full` → `h-[100dvh] rounded-none m-0` |

antd `Modal` fullscreen / 移动端全屏编辑场景；字段仍建议 ≤20，超出用 `FormDrawer`。

```tsx
<FormDialog open={open} onOpenChange={setOpen} title="批量导入" fullScreen onSubmit={handleSubmit}>
  {/* 全屏表单字段 */}
</FormDialog>
```

## DropdownMenu

**源**：`ui/dropdown/Dropdown.tsx`

```tsx
// panel: absolute z-40 right-0 mt-2 rounded-xl border border-gray-200 bg-white shadow-theme-lg
//        dark:border-gray-800 dark:bg-gray-dark
// item: px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-white/5
```

```tsx
<DropdownMenuContent className="rounded-xl border-gray-200 shadow-theme-lg dark:bg-gray-dark">
  <DropdownMenuItem className="text-theme-sm">...</DropdownMenuItem>
</DropdownMenuContent>
```

## Popover

**源**：`ui/popover/Popover.tsx` — 同 Dropdown 阴影与圆角 `rounded-xl`。

```tsx
<Popover>
  <PopoverTrigger asChild>
    <Button variant="outline">Filter range</Button>
  </PopoverTrigger>
  <PopoverContent className="w-auto min-w-[260px] rounded-xl border-gray-200 p-4 shadow-theme-lg dark:border-gray-800 dark:bg-gray-dark">
    ...
  </PopoverContent>
</Popover>
```

- 面板：`rounded-xl border-gray-200 shadow-theme-lg dark:bg-gray-dark`
- 选项：`px-3 py-2.5 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5`
- 选中：`bg-brand-50 text-brand-500`

preview 对齐：`preview.html` Overlay 卡片 Popover mock（Filter range + 日期选项列表）。

## Tooltip

**源**：`ui/tooltip/Tooltip.tsx`（Default / Dark / Light / Placement）

- 实现：**Radix** `@radix-ui/react-tooltip`（非 floating-ui 手写）
- 可复制模板：`templates/ui/tooltip.tsx`
- `variant`: default / inverted / minimal
- 根节点需 `TooltipProvider delayDuration={200}`

```tsx
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

<TooltipProvider delayDuration={200}>
  <Tooltip>
    <TooltipTrigger asChild>
      <Button variant="outline">导出</Button>
    </TooltipTrigger>
    <TooltipContent variant="default" side="top">
      导出为 CSV
    </TooltipContent>
  </Tooltip>
</TooltipProvider>
```

- 浅色：`variant="default"` + border
- 反色：`variant="inverted"`
- 无边框：`variant="minimal"`

## HoverCard

**实现**：Radix `@radix-ui/react-hover-card` — 悬停展示多行详情（用户卡片、资源摘要）。

可复制模板：`templates/ui/hover-card.tsx`

```tsx
<HoverCard openDelay={200}>
  <HoverCardTrigger asChild>
    <Button variant="ghost">周敏</Button>
  </HoverCardTrigger>
  <HoverCardContent>
    <p className="text-sm font-medium">平台工程师</p>
    <p className="text-theme-sm text-gray-500">华东 · 最近活跃 2 分钟前</p>
  </HoverCardContent>
</HoverCard>
```

| 场景 | 优先 | 不要用 |
|---|---|---|
| 单行短提示 | `Tooltip` | HoverCard |
| 多行摘要 + 轻操作 | `HoverCard` | Popover（需点击） |

## Drawer（Sheet）

**实现**：shadcn `Sheet`（Radix Dialog 侧滑变体），替代源项目无独立 Drawer 的场景。

可复制模板：`templates/ui/sheet.tsx`（`size="filter"|"edit"|"default"|"large"|"full"` 宽度变体）

| 元素 | TailAdmin 类 | shadcn 映射 |
|---|---|---|
| Overlay | `bg-gray-400/50 backdrop-blur-[32px]` | `SheetOverlay` className 覆盖 |
| Panel | `bg-white dark:bg-gray-900` 右侧全高 | `SheetContent side="right"` |
| Header | `px-6 py-4 border-b` | `SheetHeader` |
| Footer | `px-6 py-4 border-t justify-end` | `SheetFooter` |
| 动效 | 300ms slide | `transition-transform duration-300` |

```tsx
<Sheet open={open} onOpenChange={setOpen}>
  <SheetContent side="right" className="flex w-[400px] flex-col p-0 sm:max-w-[400px]">
    <SheetHeader className="border-b border-gray-200 px-6 py-5 dark:border-gray-800">
      <SheetTitle>Advanced filters</SheetTitle>
      <SheetDescription>Refine order list by status and date range.</SheetDescription>
    </SheetHeader>
    <div className="flex-1 overflow-y-auto p-6">{/* filter fields */}</div>
    <SheetFooter className="border-t border-gray-100 px-6 py-4 dark:border-white/[0.05]">
      <Button variant="outline">Reset</Button>
      <Button>Apply filters</Button>
    </SheetFooter>
  </SheetContent>
</Sheet>
```

- ESC + backdrop 关闭：Radix 默认
- 筛选面板：字段 3–8 个时用 Drawer 代替 Dialog
- 宽度：默认 `400px`（筛选）/ `480px`（编辑）/ `378px`（默认）/ `736px`（large）

**P3-B 扩展 props**：

| prop | 说明 |
|---|---|
| `resizable` | 左右侧 Sheet 显示 4px 拖拽区调整宽度 |
| `push` + `stackIndex` | 多层 Sheet 叠加时水平偏移 |
| `overlayBlur` / `SheetOverlay blur` | 遮罩是否 `backdrop-blur` |
| `showOverlay` | 显式控制遮罩；列表筛选 Drawer 传 `false` |
| `variant` | `temporary`（默认）/ `persistent` / `mini` |

### SheetContent 定位（必读）

`sheetVariants()` 基类含 `fixed z-99999`。`SheetContent` 的 `cn()` **仅**追加 `p-0` 等布局类 — **禁止** `"relative p-0"`：`tailwind-merge` 会让 `relative` 覆盖 `fixed`，表现为遮罩正常但面板不可见。

### 列表筛选 Drawer

复杂列表筛选（4+ 字段）：

```tsx
<Sheet modal={false} open={open} onOpenChange={setOpen}>
  <SheetContent side="right" size="filter" showOverlay={false} className="flex flex-col">
    <SheetHeader><SheetTitle>筛选</SheetTitle></SheetHeader>
    <div className="flex-1 overflow-y-auto px-6 py-4">{fields}</div>
    <SheetFooter>...</SheetFooter>
  </SheetContent>
</Sheet>
```

左侧列表保持可见、可操作；详见 `layout-patterns/list-search-filter-toolbar.md`。

### Dialog 内 Select

`SelectContent` 默认 portal 到 `document.body`，在 `Dialog` 内可能触发 `aria-hidden` 焦点警告。

- 无选项时不渲染 Select（静态说明文案）
- 或将 `SelectContent` portal 容器设为 `DialogContent` ref（项目层扩展）
- 使用 `position="popper"`

### Sheet variant 语义

| variant | 行为 | 宽度 |
|---------|------|------|
| `temporary` | 浮层 + 遮罩，ESC/backdrop 关闭 | 随 `size`：`filter` 400px / `edit` 480px / `default` 378px / `large` 736px / `full` |
| `persistent` | 无遮罩，挤占主内容区（`shadow-none` + ring） | 同 `size` |
| `mini` | 侧栏式窄面板，对齐 `AppSidebar` 折叠/展开比例 | 折叠 `w-[90px]` / 展开 `w-[290px]` |

`mini` 用于设置页、筛选器等于主导航并存的场景；宽度与 `AppSidebar`（`w-[290px]` 展开 / `w-[90px]` 折叠）保持一致，避免壳层比例冲突。

## Popconfirm

**源**：antd Popconfirm — 锚点旁二次确认，比 Dialog 轻量。

可复制模板：`templates/ui/popconfirm.tsx`（基于 `Popover` + 确定/取消按钮）

| 场景 | 优先 | 不要用 |
|---|---|---|
| 行内删除/撤销 | `Popconfirm` | 居中 Dialog |
| 整页危险操作 | `AlertDialog` | Popconfirm |

## Scroll Area

**源**：Radix Scroll Area — 固定高度容器内滚动，统一样式滚动条。

可复制模板：`templates/ui/scroll-area.tsx`

preview 对齐：`preview.html` Overlay 卡片 Drawer mock（Filter Drawer + 300ms slide）。

## Tour

**实现**：`driver.js`（peer 依赖）— 步骤引导 / 新功能 Onboarding。

可复制模板：`templates/ui/tour.tsx`

```tsx
import { Tour } from "@/components/ui/tour";

<Tour
  open={open}
  onOpenChange={setOpen}
  steps={[
    { element: "#sidebar", title: "导航", description: "从这里切换模块", side: "right" },
    { element: "#create-btn", title: "新建", description: "点击创建资源" },
  ]}
  onFinish={() => setOpen(false)}
  onSkip={() => setOpen(false)}
/>
```

| 场景 | 优先 | 不要用 |
|---|---|---|
| 首次引导 / 多步 Onboarding | `Tour` | 多个 Dialog |
| 单字段说明 | `Tooltip` / `ToggleTip` | Tour |

### driver.js CSS override（TailAdmin 皮肤）

在应用全局样式追加以下类，并通过 `popoverClass: "driver-popover-tailadmin"` 挂载：

| 选择器 | TailAdmin 类 / 值 | 说明 |
|---|---|---|
| `.driver-popover-tailadmin` | `rounded-2xl border border-gray-200 bg-white shadow-theme-lg dark:border-gray-800 dark:bg-gray-dark` | 弹层容器 |
| `.driver-popover-tailadmin .driver-popover-title` | `text-base font-semibold text-gray-800 dark:text-white/90` | 标题 |
| `.driver-popover-tailadmin .driver-popover-description` | `text-theme-sm text-gray-500 dark:text-gray-400` | 描述 |
| `.driver-popover-tailadmin .driver-popover-footer button` | `rounded-lg px-4 py-2 text-theme-sm font-medium` | 底部按钮基类 |
| `.driver-popover-tailadmin .driver-popover-next-btn` | `bg-brand-500 text-white hover:bg-brand-600` | 下一步 / 完成 |
| `.driver-popover-tailadmin .driver-popover-prev-btn` | `bg-white text-gray-700 ring-1 ring-inset ring-gray-300 hover:bg-gray-50` | 上一步 |
| `.driver-popover-tailadmin .driver-popover-close-btn` | `text-gray-400 hover:text-gray-600` | 关闭 |
| `.driver-overlay` | `backdrop-blur-[2px]` | 蒙层（可选） |

```css
.driver-popover-tailadmin {
  @apply rounded-2xl border border-gray-200 bg-white shadow-theme-lg dark:border-gray-800 dark:bg-gray-dark;
}
.driver-popover-tailadmin .driver-popover-title {
  @apply text-base font-semibold text-gray-800 dark:text-white/90;
}
.driver-popover-tailadmin .driver-popover-description {
  @apply text-theme-sm text-gray-500 dark:text-gray-400;
}
.driver-popover-tailadmin .driver-popover-next-btn {
  @apply rounded-lg bg-brand-500 px-4 py-2 text-theme-sm font-medium text-white hover:bg-brand-600;
}
```

- 受控：`open` + `onOpenChange`
- 蒙层：`mask`（默认 true，`overlayOpacity: 0.6`）
- 完成 / 跳过：`onFinish` / `onSkip`
