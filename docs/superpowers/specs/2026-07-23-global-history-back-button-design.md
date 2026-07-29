# 全局历史返回按钮

日期：2026-07-23  
状态：已对齐，待实现

## 目标

在 Web 控制台提供全局「返回上一页」能力，行为等价于浏览器后退，减少用户依赖浏览器原生后退或各页分散的父级链接。

## 非目标

- 不替换各页现有 `BackLink`（固定父级路由）。
- 不自建站内历史栈 / HistoryContext。
- 不改变路由结构或侧边栏导航。

## 行为

| 场景 | 行为 |
|------|------|
| 存在可后退历史 | 点击后 `navigate(-1)` |
| 无可后退历史（新开标签直达、刷新后仅一条记录等） | 按钮可见且禁用 |
| 各页 `BackLink` | 保持不变，与全局按钮并存 |

## UI

- 位置：`AppShell` 顶栏左侧——移动端「打开导航」按钮之后、当前页标题之前。
- 形态：`Button` `variant="ghost"` `size="icon"`，图标 `ArrowLeft`（或与壳层一致的 Chevron）。
- 无障碍：`aria-label="返回上一页"`；禁用时由原生 `disabled` 表达。

## 实现要点

1. 在 `apps/web/src/components/layout/app-shell.tsx` 的 `AppShell` 顶栏加入返回按钮。
2. 使用 `useNavigate()`，点击时 `navigate(-1)`。
3. 可后退判定：优先读取 React Router data router 写入的 `window.history.state.idx`（`idx > 0` 可退）；若无法判定，保守视为不可退并禁用。
4. 不在此任务中改动 `BackLink` 组件或各业务页。

## 测试

扩展或新增 `app-shell` 相关测试：

- 渲染 `AppShell` 时存在 `aria-label="返回上一页"` 的按钮。
- 无历史（`idx === 0` 或等价初始态）时按钮 `disabled`。
- 有历史时点击会触发后退（mock `navigate` 或等价断言）。

## 验收

- 站内从 A 页进入 B 页后，顶栏返回可回到 A。
- 直接打开某深层路由时，返回按钮禁用。
- 现有页面级 `BackLink` 仍可用。
- `pnpm web:lint` 与相关 Vitest 通过。
