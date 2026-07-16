# 工程守卫 — React + shadcn + Radix + Tailwind v4

## 技术栈红线

| 规则 | 说明 |
|---|---|
| 浮层必须用 Radix | Dialog、DropdownMenu、Popover、Tooltip、Tabs — 经 `@radix-ui/react-*` / shadcn Radix 变体；**禁止** `@base-ui/react-*`、Base UI 预设、手写 portal + mousedown |
| 类名用 `cn()` | `import { cn } from "@/lib/utils"` — 禁止 `` `${a} ${b}` `` |
| 变体用 `cva` | Button、Badge、Alert 等 |
| Token 优先 | 禁止页面内 `#hex`、`rgb()`、`style={{}}` 颜色 |
| 路径别名 | `@/components/ui/*`、`@/lib/utils` |
| 向后兼容 | 已发布模板的导出名、props、variant、theme helper 不得静默破坏；破坏性变更必须走 migration |

## 目录约定

```
src/
├── components/ui/     # shadcn 生成组件
├── components/layout/ # AppLayout, AppSidebar, AppHeader
├── components/forms/  # 业务表单组合（可选）
├── context/           # ThemeContext, SidebarContext
├── hooks/             # useModal → 优先 Dialog 受控模式
├── lib/utils.ts       # cn()
└── index.css          # @theme tokens + @utility menu-*
```

## shadcn 初始化

复制 Skill 内预设后初始化：

```bash
cp b-design-system-tailadmin-radix/templates/components.json ./components.json
cp -r b-design-system-tailadmin-radix/templates/lib ./src/lib
npx shadcn@latest init   # 若已有 components.json 可跳过交互
npx shadcn@latest add button input label select checkbox radio-group switch dialog dropdown-menu tabs tooltip popover alert table badge avatar breadcrumb sheet calendar command popover sonner skeleton
```

用 Skill 模板覆盖 Button / Input variants：

```bash
cp b-design-system-tailadmin-radix/templates/ui/button.tsx ./src/components/ui/button.tsx
cp b-design-system-tailadmin-radix/templates/ui/input.tsx ./src/components/ui/input.tsx
cp b-design-system-tailadmin-radix/templates/ui/textarea.tsx ./src/components/ui/textarea.tsx
cp b-design-system-tailadmin-radix/templates/ui/select.tsx ./src/components/ui/select.tsx
cp b-design-system-tailadmin-radix/templates/ui/checkbox.tsx ./src/components/ui/checkbox.tsx
cp b-design-system-tailadmin-radix/templates/ui/radio-group.tsx ./src/components/ui/radio-group.tsx
cp b-design-system-tailadmin-radix/templates/ui/switch.tsx ./src/components/ui/switch.tsx
cp b-design-system-tailadmin-radix/templates/ui/badge.tsx ./src/components/ui/badge.tsx
cp b-design-system-tailadmin-radix/templates/ui/alert.tsx ./src/components/ui/alert.tsx
cp b-design-system-tailadmin-radix/templates/ui/table.tsx ./src/components/ui/table.tsx
cp b-design-system-tailadmin-radix/templates/ui/pagination.tsx ./src/components/ui/pagination.tsx
cp b-design-system-tailadmin-radix/templates/ui/card.tsx ./src/components/ui/card.tsx
cp b-design-system-tailadmin-radix/templates/ui/progress.tsx ./src/components/ui/progress.tsx
cp b-design-system-tailadmin-radix/templates/ui/skeleton.tsx ./src/components/ui/skeleton.tsx
cp b-design-system-tailadmin-radix/templates/ui/spinner.tsx ./src/components/ui/spinner.tsx
cp b-design-system-tailadmin-radix/templates/ui/avatar.tsx ./src/components/ui/avatar.tsx
cp b-design-system-tailadmin-radix/templates/ui/breadcrumb.tsx ./src/components/ui/breadcrumb.tsx
cp b-design-system-tailadmin-radix/templates/ui/sheet.tsx ./src/components/ui/sheet.tsx
cp b-design-system-tailadmin-radix/templates/ui/list-search-filter-toolbar.tsx ./src/components/ui/list-search-filter-toolbar.tsx
cp b-design-system-tailadmin-radix/templates/ui/list-search-input.tsx ./src/components/ui/list-search-input.tsx
cp b-design-system-tailadmin-radix/templates/ui/list-filter-panel.tsx ./src/components/ui/list-filter-panel.tsx
cp b-design-system-tailadmin-radix/templates/ui/list-filter-types.ts ./src/components/ui/list-filter-types.ts
cp b-design-system-tailadmin-radix/templates/ui/list-filter-utils.ts ./src/components/ui/list-filter-utils.ts
cp b-design-system-tailadmin-radix/templates/lib/use-debounced-value.ts ./src/lib/use-debounced-value.ts
cp b-design-system-tailadmin-radix/templates/context/sidebar-context.tsx ./src/context/sidebar-context.tsx
cp b-design-system-tailadmin-radix/templates/context/theme-context.tsx ./src/context/theme-context.tsx
cp b-design-system-tailadmin-radix/templates/layout/app-sidebar.tsx ./src/components/layout/app-sidebar.tsx
cp b-design-system-tailadmin-radix/templates/layout/app-header.tsx ./src/components/layout/app-header.tsx
cp b-design-system-tailadmin-radix/templates/layout/app-layout.tsx ./src/components/layout/app-layout.tsx
cp b-design-system-tailadmin-radix/templates/layout/backdrop.tsx ./src/components/layout/backdrop.tsx
cp b-design-system-tailadmin-radix/templates/layout/theme-toggle.tsx ./src/components/layout/theme-toggle.tsx
cp b-design-system-tailadmin-radix/templates/layout/notification-dropdown.tsx ./src/components/layout/notification-dropdown.tsx
cp b-design-system-tailadmin-radix/templates/layout/user-dropdown.tsx ./src/components/layout/user-dropdown.tsx
cp b-design-system-tailadmin-radix/templates/ui/dropdown-menu.tsx ./src/components/ui/dropdown-menu.tsx
cp b-design-system-tailadmin-radix/templates/ui/popover.tsx ./src/components/ui/popover.tsx
cp b-design-system-tailadmin-radix/templates/ui/command.tsx ./src/components/ui/command.tsx
cp b-design-system-tailadmin-radix/templates/ui/search-command.tsx ./src/components/ui/search-command.tsx
cp b-design-system-tailadmin-radix/templates/ui/file-upload.tsx ./src/components/ui/file-upload.tsx
cp b-design-system-tailadmin-radix/templates/ui/multi-select.tsx ./src/components/ui/multi-select.tsx
cp b-design-system-tailadmin-radix/templates/ui/calendar.tsx ./src/components/ui/calendar.tsx
cp b-design-system-tailadmin-radix/templates/ui/date-picker.tsx ./src/components/ui/date-picker.tsx
cp b-design-system-tailadmin-radix/templates/lib/chart-theme.ts ./src/lib/chart-theme.ts
cp b-design-system-tailadmin-radix/templates/lib/fullcalendar-theme.ts ./src/lib/fullcalendar-theme.ts
cp b-design-system-tailadmin-radix/templates/sonner-theme.tsx ./src/components/ui/sonner-theme.tsx
```

`components.json` 要点：

- `tailwind.css` → `src/index.css`（Tailwind v4 `@theme`）
- `aliases.ui` → `@/components/ui`
- `style: new-york`，`iconLibrary: lucide`

`index.css` 必须含 TailAdmin `@theme` brand/gray 色板与 `@utility menu-*`（见 `token-index.md`）。

## Radix 组合规则

- 触发器：`<DropdownMenuTrigger asChild><Button /></DropdownMenuTrigger>`
- Dialog 关闭：`<DialogClose asChild>` 或 `onOpenChange`
- Tooltip 需 `<TooltipProvider>` 包裹应用根
- 不要嵌套可聚焦的 `<button>` 在 `<button>` 内 — 用 `asChild`
- **Button `asChild`**：`loading` / `aria-busy` / spinner **不**作用于 `asChild` 分支；loading 态用原生 `<button>` 或包一层非 Slot 容器
- **Dialog 内 Select**：空列表不渲染 Select；或 Select portal 挂 Dialog 内容节点，避免 `aria-hidden` 焦点冲突
- **浮层关闭**：仅 `open` + `onOpenChange` 受控；**禁止**在 `onOpenChange(false)` 里 `remove()` portal 节点、清全局 `inert`/`aria-hidden`、写 `pointer-events: none`（生产 build 易整页卡死）

## Sheet / cn() 合并

`SheetContent` 的 `sheetVariants()` 含 `fixed`。`cn()` 合并时 **禁止**在其后追加 `relative`，否则 `tailwind-merge` 覆盖 `fixed`，遮罩可见但面板滑出视口。仅追加 `p-0` 等不影响定位的类。见 `upgrade-troubleshooting.md#sheet-content-fixed`。

## 顶栏搜索

列表页搜索用 `ListSearchFilterToolbar`；App 顶栏用 `HeaderSearch`（`templates/layout/app-header.tsx`）— **单元素** `border + dark:bg-gray-900`。禁止外壳 div 再包一层带背景的 `Input`（暗色双色条）。

## 列表工具栏

Table List 页工具栏：**左** `ListSearchFilterToolbar` · **右** 新建 · **底** 分页。见 `layout-patterns/table-list.md` · `list-search-filter-toolbar.md`。

## Tailwind v4

- Token 在 `@theme { }` 定义，非 `tailwind.config.js`
- 暗色：`@custom-variant dark (&:is(.dark *))`
- 插件：`@tailwindcss/forms` 用于原生表单 reset

## 静态检查

```bash
# 硬编码颜色
rg -n "#[0-9a-fA-F]{3,8}|rgb\(|oklch\(" src --glob '!index.css'

# 应使用语义 token 而非默认 tailwind 色板（业务代码）
rg -n "text-(blue|slate|zinc)-[0-9]" src/components

# 手写 modal 反模式
rg -n "fixed inset-0.*modal|useEffect.*overflow.*hidden" src --glob '!**/ui/dialog*'

# cn 遗漏
rg -n 'className=\{`' src/components
```

## TypeScript

- Props 导出 interface；variant 用联合类型或 `VariantProps<typeof buttonVariants>`
- 表单：优先 `react-hook-form` + `zod` + shadcn `Form`
- 事件：`onClick?: () => void` 或 Radix `onOpenChange`

## 向后兼容

- 组件新增能力优先新增 props/variant，不直接删除旧 props。
- 组件重构时保留旧导出名、旧 class helper 或 wrapper，内部转接到新实现。
- 破坏性变更必须同步 `references/backward-compatibility.md` 中的 migration 要求。
- 未经用户明确要求，不批量改写业务项目中已经使用旧组件的代码。

## 可访问性

- 图标按钮：`aria-label`
- 表单：`Label htmlFor` + `id`
- 错误：`aria-invalid` + `FormMessage`
- 对比度：正文 `gray-800` on `white` / `white/90` on `gray-900`

## 提交前检查

- [ ] `component-index.md` 已更新（新组件）
- [ ] public API 未破坏；若破坏，已提供 deprecated wrapper 和 migration note
- [ ] Token 未硬编码
- [ ] `dark:` 变体完整
- [ ] `focus-visible` 可见
- [ ] `tsc --noEmit` 通过
- [ ] `eslint .` 无新增 error
