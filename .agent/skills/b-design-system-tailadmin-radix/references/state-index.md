# 状态索引

每个 UI 状态必须可检索。shadcn/Radix 实现时对照本表。

## 交互状态

| 状态 | TailAdmin 模式 | shadcn 实现 |
|---|---|---|
| hover | `hover:bg-brand-600`（btn）· `hover:bg-gray-100`（menu） | 同 Token + `hover:` |
| focus | Input: `focus:ring-3 focus:ring-brand-500/20` | `focus-visible:ring-3`（Button 必须补） |
| pressed/active | 侧栏 `menu-item-active` | `data-[state=open]` / `aria-current` |
| selected | `bg-brand-50 text-brand-500` | Tabs `data-[state=active]` |
| disabled | `opacity-50 cursor-not-allowed` | `disabled:` + `aria-disabled` |

## 数据状态

| 状态 | 模式 | 组件 |
|---|---|---|
| loading | Spinner 组件 / 按钮内 Loader | `Spinner` · `Button disabled` + icon |
| pending | 首次请求未返回 | `QueryShell` 全块替换 |
| empty | 居中文案 + CTA，`min-h-[240px]` | `ContentState` · `QueryShell` |
| error | 原因 + 下一步 + Retry/深链 | `ErrorState` · `QueryShell` |
| refetching | 保留内容 + overlay Spinner | `QueryShell` |
| partial | warning banner + stale 数据 | `QueryShell` · `StatMetric partial` |
| forbidden | Lock 图标 + 掩码 `•••` | `ContentState forbidden` · `StatMetric` |
| zero-value KPI | 灰色 `0`，非错误 | `StatMetric zero` |
| success | Input `border-success-500` | 校验通过 hint `text-success-500` |

详情契约：`component-styles/content-state-contract.md`

## 浮层状态

| 状态 | TailAdmin | shadcn/Radix |
|---|---|---|
| open | Modal `isOpen` | `Dialog open` / `DropdownMenu` |
| close | ESC + backdrop click | Radix 默认 + `onOpenChange` |
| scroll lock | `body.overflow = hidden` | Dialog 内置 |

## 主题状态

| 模式 | 实现 |
|---|---|
| light | 默认 |
| dark | `html.dark` + 全组件 `dark:` 变体 |
| auto | `prefers-color-scheme` → 写入 `localStorage.theme` |

源：`context/ThemeContext.tsx`

## 布局状态

| 状态 | 触发 | 类名变化 |
|---|---|---|
| sidebar expanded | 默认桌面 | `xl:ml-[290px]` |
| sidebar collapsed | toggle | `xl:ml-[90px]` |
| sidebar hover expand | 折叠+mouseEnter | 临时 `w-[290px]` |
| mobile menu open | hamburger | `Backdrop` + sidebar translate |

源：`context/SidebarContext.tsx`

## 校验状态

| 状态 | 视觉 |
|---|---|
| default | `border-gray-300` |
| error | `border-error-500` + `text-error-500` hint |
| success | `border-success-500` + `text-success-500` hint |
| disabled | `opacity-40 bg-gray-100` |

## 响应式

| 断点 | 行为 |
|---|---|
| `< xl` | 侧栏 overlay；顶栏双行 |
| `xl+` | 侧栏 fixed；主列 margin |
| `md+` | 页面 padding `p-6` |

## 低动态 / 可访问性

- 尊重 `prefers-reduced-motion`：侧栏 `transition` 可降为 `duration-0`
- Dialog 必须 trap focus（Radix 默认）
- 图标按钮需 `aria-label`
- 表单错误关联 `aria-describedby`
