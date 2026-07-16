# 交互与动效

TailAdmin 动效克制、功能导向。使用 shadcn/Radix 时保留相同时长与缓动意图。

## 时长与缓动

| 场景 | 时长 | 缓动 | 证据 |
|---|---|---|---|
| 侧栏宽度/主列 margin | 300ms | ease-in-out | `AppLayout` `transition-[margin] duration-300` |
| 手风琴子菜单 | 300ms | ease-in-out | `.menu-accordion` grid-rows |
| 颜色/背景 | 150–200ms | default | `transition-colors` |
| Radix 浮层 | 150ms | ease-out | shadcn 默认 `animate-in` |

## Hover

- **Button primary**：`hover:bg-brand-600`
- **Button outline**：`hover:bg-gray-50` · 暗色 `dark:hover:bg-white/[0.03]`
- **Menu item**：`hover:bg-gray-100` · 暗色 `dark:hover:bg-white/5`
- **Dropdown item**：`hover:bg-gray-100` · 暗色 `dark:hover:bg-white/5`
- **Modal close**：`hover:bg-gray-200` · 暗色 `dark:hover:bg-gray-700`

## Focus

- **Input**：`focus:outline-hidden focus:ring-3 focus:ring-brand-500/20 focus:border-brand-300`
- **Button（shadcn 补齐）**：`focus-visible:ring-3 focus-visible:ring-brand-500/20`
- **全局 token**：`shadow-focus-ring` = 4px brand 12% 透明度

## 浮层

- **Modal overlay**：`bg-gray-400/50 backdrop-blur-[32px]`
- **Dialog 进入**：fade + scale（shadcn `zoom-in-95`）
- **Dropdown**：`mt-2` 位移 + `shadow-theme-lg`
- **ESC 关闭**：Modal 支持；Radix Dialog 默认支持

## 侧栏

- 折叠态 hover 临时展开（`isHovered`）
- 箭头旋转：`menu-item-arrow-active` → `rotate-180`
- 移动端：Backdrop `bg-gray-900/50` z-40

## 加载

- Spinner：旋转动画（各 `SpinnerOne`–`Four` 变体）
- 按钮加载：禁用 + 左侧 spinner icon
- 表格加载：骨架行或 overlay spinner（源项目多为静态，shadcn 用 `Skeleton`）

## 禁止

- 无意义的 bounce / pulse 装饰
- 超过 400ms 的布局动画（除侧栏）
- 自动播放大面积视差

## prefers-reduced-motion

```css
@media (prefers-reduced-motion: reduce) {
  .menu-accordion { transition: none; }
}
```

Radix/shadcn：`motion-reduce:animate-none`
