# Navigation — Sidebar / Header / Breadcrumb / Tabs

## AppSidebar

**源**：`layout/AppSidebar.tsx`

可复制模板：`templates/layout/app-sidebar.tsx` · `templates/context/sidebar-context.tsx`

结构：
- fixed `left-0 top-0` · `h-screen` · `border-r border-gray-200 dark:border-gray-800`
- 宽度：`w-[290px]` 展开 / `w-[90px]` 折叠；hover 临时展开
- 导航项：`menu-item` + `menu-item-active` | `menu-item-inactive`
- 图标：`menu-item-icon-size`（svg `size-6`）
- 子菜单：Radix `Collapsible` + `menu-dropdown-item-*`；accordion 300ms
- Badge：`menu-dropdown-badge` / `menu-dropdown-badge-pro`

```tsx
import { AppSidebar, type NavSection } from "@/components/layout/app-sidebar";
import { SidebarProvider } from "@/context/sidebar-context";
import { LayoutDashboard } from "lucide-react";

const sections: NavSection[] = [
  {
    title: "Menu",
    items: [
      {
        name: "Dashboard",
        icon: <LayoutDashboard className="size-6" />,
        subItems: [
          { name: "Ecommerce", path: "/" },
          { name: "Analytics", path: "/analytics" },
        ],
      },
    ],
  },
];

<SidebarProvider>
  <AppSidebar sections={sections} logo={<Logo />} collapsedLogo={<LogoIcon />} />
</SidebarProvider>
```

## AppHeader

**源**：`layout/AppHeader.tsx`

可复制模板：`templates/layout/app-header.tsx`

- `sticky top-0 z-99999 bg-white dark:bg-gray-900`
- 左：sidebar toggle + 搜索（`⌘K` 快捷键）
- 右：ThemeToggle · NotificationDropdown · UserDropdown

```tsx
import { AppHeader, HeaderSearch } from "@/components/layout/app-header";
import { ThemeToggleButton } from "@/components/layout/theme-toggle";

<AppHeader
  logo={<Logo />}
  onOpenCommand={() => setCommandOpen(true)}
  actions={
    <>
      <ThemeToggleButton />
      <NotificationDropdown />
      <UserDropdown />
    </>
  }
/>
```

应用根需包裹 `ThemeProvider`（`templates/context/theme-context.tsx`）。

## AppLayout

可复制模板：`templates/layout/app-layout.tsx`

```tsx
import { AppLayout } from "@/components/layout/app-layout";
import { NotificationDropdown } from "@/components/layout/notification-dropdown";
import { UserDropdown } from "@/components/layout/user-dropdown";

<AppLayout
  sidebar={{ sections, logo: <Logo />, collapsedLogo: <LogoIcon /> }}
  onOpenCommand={() => setCommandOpen(true)}
  header={{
    actions: (
      <>
        <NotificationDropdown items={notifications} hasUnread />
        <UserDropdown name="Musharof" email="randomuser@pimjo.com" />
      </>
    ),
  }}
/>
```

默认渲染 `<Backdrop />`（移动端 sidebar 遮罩）；可通过 `backdrop` prop 覆盖。
```

## Breadcrumb

`text-sm text-gray-500`；当前项 `text-gray-800 dark:text-white/90`；分隔符 ChevronRight 或 `/`；Home 项用 `BreadcrumbHome`。

可复制模板：`templates/ui/breadcrumb.tsx`

```tsx
<Breadcrumb>
  <BreadcrumbList>
    <BreadcrumbItem>
      <BreadcrumbHome href="/" />
    </BreadcrumbItem>
    <BreadcrumbSeparator />
    <BreadcrumbItem>
      <BreadcrumbLink href="/ui">Ui Kits</BreadcrumbLink>
    </BreadcrumbItem>
    <BreadcrumbSeparator />
    <BreadcrumbItem>
      <BreadcrumbPage>Avatar</BreadcrumbPage>
    </BreadcrumbItem>
  </BreadcrumbList>
</Breadcrumb>
```

preview 对齐：`preview.html` Identity 卡片 + 页头 breadcrumb mock。

## Tabs

**源**：`ui/tabs/TabWithUnderline.tsx`、`DefaultTab.tsx`、`VerticalTabs.tsx`、`TabWithBadge.tsx`

- 可复制模板：`templates/ui/tabs.tsx`
- `TabsList.variant`: line（默认）/ enclosed / outline / plain
- `TabsList.size`: sm / md / lg；`fitted` 等宽；`orientation`: horizontal / vertical
- `TabsTrigger` 支持 `icon`、`badge` slot

```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

<Tabs defaultValue="overview">
  <TabsList variant="line">
    <TabsTrigger value="overview">概览</TabsTrigger>
    <TabsTrigger value="analytics">分析</TabsTrigger>
  </TabsList>
  <TabsContent value="overview">概览内容</TabsContent>
  <TabsContent value="analytics">分析内容</TabsContent>
</Tabs>

<Tabs defaultValue="week">
  <TabsList variant="enclosed" fitted>
    <TabsTrigger value="day">日</TabsTrigger>
    <TabsTrigger value="week">周</TabsTrigger>
    <TabsTrigger value="month">月</TabsTrigger>
  </TabsList>
</Tabs>
```

选型：不同内容面板用 Tabs；同视图粒度切换用 SegmentedControl（见 decision-matrix#变体与导航选型）。

## Tabs editable {#tabs-editable}

antd `Tabs` `type="editable-card"` 等价 — 可关闭/新增 Tab。

| prop | 类型 | 说明 |
|---|---|---|
| `editable` | `boolean?` | Tab 右侧 close + 末尾 add 按钮 |
| `onEdit` | `(targetKey, action: "add" \| "remove") => void` | 增删回调 |
| `hideAdd` | `boolean?` | 隐藏 add 按钮 |

关闭 Tab 后 focus 下一 active tab；动态面板 key 由业务受控。

```tsx
<Tabs value={active} onValueChange={setActive}>
  <TabsList editable onEdit={handleEdit}>
    {panes.map((p) => (
      <TabsTrigger key={p.key} value={p.key}>{p.title}</TabsTrigger>
    ))}
  </TabsList>
  {panes.map((p) => (
    <TabsContent key={p.key} value={p.key}>{p.content}</TabsContent>
  ))}
</Tabs>
```

## Steps mobile {#steps-mobile}

**模板**：`templates/ui/steps.tsx`

窄屏步骤条变体（PR-E）：

| prop | 类型 | 说明 |
|---|---|---|
| `mobileVariant` | `"dots" \| "text" \| "progress"?` | `<md` 展示模式；默认 `dots` |
| `responsive` | `boolean?` | 默认 `true` — 自动在 `<md` 切换 mobileVariant |

| mobileVariant | 行为 |
|---|---|
| `dots` | 隐藏 label，仅圆点指示 |
| `text` | 缩写 label，横向滚动 |
| `progress` | 顶部细 progress bar |

桌面仍用完整水平/垂直步骤条；CI 流水线领域包装见 `pipeline-stage-bar.tsx`。

## Sheet variant {#sheet-variant}

**模板**：`templates/ui/sheet.tsx` · 详情见 `overlay-template.md#drawer`

| variant | 场景 |
|---|---|
| `temporary` | 默认浮层 + 遮罩 |
| `persistent` | 挤占主内容、无遮罩 — 设置页/筛选常驻侧栏 |
| `mini` | `w-[90px]`/`w-[290px]` — 与 `AppSidebar` 折叠比例对齐 |

`mini` + `side="left"` 用于与主导航并存的次级面板；勿与完整 `AppLayout` 侧栏叠放两套 290px 壳层。

## Pagination

**源**：`ui/pagination/PaginationWithIcon.tsx`

- 页码：`size-10 rounded-lg`
- 当前页：`bg-brand-500 text-white hover:bg-brand-600`
- 其他：`text-gray-700 hover:bg-gray-100`
- 禁用：`opacity-50 pointer-events-none`

可复制模板：`templates/ui/pagination.tsx`

```tsx
<Pagination>
  <PaginationContent>
    <PaginationItem><PaginationPrevious /></PaginationItem>
    <PaginationItem><PaginationLink isActive>1</PaginationLink></PaginationItem>
    <PaginationItem><PaginationLink>2</PaginationLink></PaginationItem>
    <PaginationItem><PaginationNext /></PaginationItem>
  </PaginationContent>
</Pagination>
```

## AnchorNav {#anchor-nav}

**模板**：`templates/ui/anchor-nav.tsx` · **Hook**：`templates/lib/use-page-nav.ts`

长设置页/文档页章节锚点导航；内部 `usePageNav` 注册 section、`scrollTo`、IntersectionObserver 高亮 `activeId`。

| prop | 类型 | 说明 |
|---|---|---|
| `sections` | `{ id, label }[]` | 锚点定义 |
| `offset` | `number?` | 滚动偏移；默认 `72` |
| `affix` | `boolean?` | sticky 吸顶；默认 `true` |
| `orientation` | `"vertical" \| "horizontal"?` | 布局方向 |

配合 `AnchorSection` 包裹各章节内容（`id` + `registerRef`）。

```tsx
import { AnchorNav, AnchorSection } from "@/components/ui/anchor-nav";

<AnchorNav sections={[{ id: "general", label: "常规" }, { id: "security", label: "安全" }]} />
<AnchorSection id="general">…</AnchorSection>
<AnchorSection id="security">…</AnchorSection>
```

active 项：`border-l-2 border-brand-500 text-brand-600`（vertical）。
