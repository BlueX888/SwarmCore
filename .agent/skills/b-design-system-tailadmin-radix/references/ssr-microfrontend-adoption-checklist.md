# SSR / 微前端接入路径清单

> DOCS-009 / G58 产物。业务仓库在 **SSR 框架**（Next.js、Remix 等）或 **微前端壳层**（Module Federation、qiankun、single-spa 等）中接入 TailAdmin-Radix Skill 时，按本清单执行可复现冒烟。`adoption-onboarding-checklist.md` 的 ADOPT-01～05 面向纯 CSR Vite SPA；本文件补齐 SSR hydration 与微前端嵌入路径。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| Next.js / Remix / SSR 框架接入后台 | SSR-01～05 |
| Module Federation / qiankun / 子应用嵌入 | MFE-01～05 |
| ADOPT 通过但生产 hydration 报错 | SSR-02～04 |
| 微前端内侧栏/主题/路由错位 | MFE-02～04 |
| 不确定从哪开始 | `agent-retrieval-guide.md` SSR/微前端路由 |

## 通用前置

1. 已完成 `adoption-onboarding-checklist.md` ADOPT-01～04（或等价脚手架 + Token + pin）。
2. 确认 Skill 路径可读；`extension-audit.md` 中 client-only 组件已标记降级路径。
3. 用户可见文案默认中文（技术缩写除外，见 `quality-rubric.md`）。
4. 业务 `docs/design-system-pin.md` 已记录 `pinned_commit`。

## SSR-01 — 框架边界与渲染模式

**对照 reference**：`engineering-guards.md`、`output-modes/from-zero.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 渲染边界 | 含 `window`/`document`/Radix Portal 的壳层与复杂组件标记 `'use client'` 或 dynamic | SSR-01 |
| 2 | 路由策略 | App Router 下后台页使用 Client Component 边界；布局壳层与内容区分离 | `route-index.md` |
| 3 | CSS 注入 | Tailwind v4 `@import "tailwindcss"` 在 SSR 入口可加载；无 FOUC 大面积裸 HTML | VIS-02 |
| 4 | 路径别名 | `@/components/ui` 在 SSR bundler 与业务侧一致 | ADOPT-01 |
| 5 | 禁止 SSR 直渲 | Chart/Maps/Kanban/FullCalendar/Swiper 等不在 Server Component 直接 import | SSR-02 |

**交互动作**：`next build` 或等价 SSR 构建无 `window is not defined` / `document is not defined` 错误。

## SSR-02 — Client-only 第三方组件 dynamic import

**对照 reference**：`extension-audit.md`、`api-override-recipes.md`、`third-party-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Chart | `dynamic(() => import(...), { ssr: false })` 或路由级懒加载；降级 `StatMetric` | `chart-theme.md` |
| 2 | Maps / Vector Maps | 地图容器 client-only；降级静态地图 Card 或地区表格 | `maps-theme.md` |
| 3 | Kanban / FullCalendar / Carousel | DnD、日历、Swiper 不 SSR；有 loading 占位 | `kanban-theme.md` |
| 4 | Command / ThemeToggle | Radix 依赖 Portal 的组件在 client 边界内 | SSR-04 |
| 5 | 降级可见 | 第三方库缺失时页面仍可读（KPI 卡、表格、描述列表） | `extension-audit.md` |

**交互动作**：首屏 SSR HTML 不含 ApexCharts/MapLibre 容器报错 → 客户端 hydration 后图表/地图正常渲染。

## SSR-03 — Theme / hydration 无闪烁

**对照 reference**：`token-index.md`、`templates/layout/theme-context` 模式

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 初始主题 | `html` 带正确 `dark` class 或 `suppressHydrationWarning` 策略文档化 | VIS-02 |
| 2 | ThemeProvider | 主题状态仅在 client mount 后切换；SSR 与 CSR 首屏 class 一致 | SSR-03 |
| 3 | Token 对比度 | light/dark hydration 后边框与正文层级不丢失 | DRIFT-01 |
| 4 | 系统偏好 | `prefers-color-scheme` 与手动切换不互相覆盖导致闪烁 | `theme-toggle.tsx` |
| 5 | 截图归档 | hydration 稳定后 light + dark 各 1 张 | REV-01 |

**交互动作**：硬刷新 → 观察 300ms 内无主题闪白/闪黑 → 切换 ThemeToggle 后刷新仍保持选择。

## SSR-04 — Radix Portal 与 document 容器

**对照 reference**：`engineering-guards.md`、`state-index.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Portal 容器 | Dialog/Drawer/Dropdown/Popover/Tooltip 在 SSR 下不访问 `document` 直至 mount | SSR-04 |
| 2 | TooltipProvider | 根布局包裹 `TooltipProvider`；延迟与 SSR 无冲突 | ADOPT-03 |
| 3 | 浮层层级 | 打开 Dialog 后 Dropdown 不穿透；z-index 与 `visual-language.md` 一致 | DRIFT-05 |
| 4 | 焦点陷阱 | Modal 打开后焦点循环；关闭回焦触发器 | `state-index.md` |
| 5 | 滚动锁定 | Drawer/Dialog 打开时 body scroll 锁定不导致布局跳动 | `interaction-motion.md` |

**交互动作**：SSR 首屏打开 Dialog → 无 hydration mismatch 警告 → 关闭后焦点回到触发按钮。

## SSR-05 — SSR 冒烟与 MS 场景抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md` MS 表

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 构建通过 | SSR 生产构建 + `tsc --noEmit` 无 error | RUN-03 |
| 2 | 首页壳层 | AppLayout 侧栏 290/90 + 内容区 framing 与 ADOPT-03 一致 | ADOPT-03 |
| 3 | MS 抽检 | 至少 1 个 MS-09～13 组合页在 SSR 下受控 props 可交互 | `business-validation-checklist.md` |
| 4 | 审计通过 | `audit_migration_drills.py` + `verify_design_system.py` exit 0 | RUN-01 |
| 5 | 写回矩阵 | 新 SSR 错选或组件边界问题写入 `decision-matrix.md` | SEL-* |

**交互动作**：在 SSR 环境完成 MS-10 或 MS-11 一项交互（阶段切换或筛选 chip）→ 截图归档。

## MFE-01 — 子应用嵌入与生命周期

**对照 reference**：`templates/layout/app-layout.tsx` 模式、`decision-matrix.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 挂载点 | 子应用挂载到独立 DOM 节点；卸载时清理 Portal/订阅 | MFE-01 |
| 2 | 生命周期 | bootstrap/mount/unmount 不泄漏 ThemeContext/SidebarContext | MFE-01 |
| 3 | 样式作用域 | 子应用根节点带唯一 class 或 data 属性，避免污染主应用 | MFE-02 |
| 4 | 重复 Provider | 不与主应用重复嵌套冲突的 Router/Theme（或文档化单一 Provider 来源） | MFE-02 |
| 5 | 错误边界 | 子应用渲染失败不白屏整个壳层 | RUN-03 |

**交互动作**：主应用切换子应用路由 → 卸载再挂载 → 侧栏状态可恢复或按设计重置。

## MFE-02 — Token / CSS 共享与隔离

**对照 reference**：`token-index.md`、`engineering-guards.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Token 来源 | 共享 `@theme` 或子应用独立加载 Skill `index.css` 片段，不双份冲突 | DRIFT-01 |
| 2 | 前缀策略 | 微前端隔离时使用子应用根 class 限定 Tailwind 范围或 CSS Modules 边界 | MFE-02 |
| 3 | dark 同步 | 主应用切换 dark 时子应用 Token 同步（事件或共享 class） | VIS-02 |
| 4 | 字体与行高 | 不因子应用 isolation 导致字号/行高与 TailAdmin 密度偏离 | REV-01 |
| 5 | 硬编码抽检 | 子应用 `src` 无 `#hex` 颜色（`index.css` 除外） | ADOPT-02 |

**交互动作**：主应用 dark ↔ light → 子应用 KPI/表格对比度同步 → 无「半套主题」页面。

## MFE-03 — 路由、basename 与深链

**对照 reference**：`route-index.md`、`migration-scenarios.md` MN-02

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | basename | 子应用 `BrowserRouter` basename 与主应用注册路径一致 | MFE-03 |
| 2 | 深链 | 刷新子路由不 404（主应用 history 或网关 rewrite） | MFE-03 |
| 3 | 壳层导航 | 主应用菜单与 `AppSidebar` 不重复两套高亮逻辑冲突 | MFE-04 |
| 4 | Command 无路由 | 无 react-router 时用 `SearchCommand` `onItemSelect` 或 MN-02 模式 | TS-02 |
| 5 | 外链跳转 | 跨子应用导航走主应用协议，不 `window.open` 破坏壳层 | `agent-retrieval-guide.md` |

**交互动作**：从主应用菜单进入子应用深链 → 浏览器刷新 → 仍落在正确页面且侧栏高亮正确。

## MFE-04 — 壳层选型（全量 vs 嵌入式）

**对照 reference**：`decision-matrix.md#页面与场景选型`、`layout-patterns/`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 全量子应用 | 独立后台子应用使用完整 `AppLayout` + `AppSidebar` + `AppHeader` | ADOPT-03 |
| 2 | 嵌入式面板 | 仅内容区嵌入时用 `FormPageShell` / `HubTabsLayout` 无重复顶栏 | MFE-04 |
| 3 | 双门户 | Dual Portal Shell 场景主/子应用角色明确，不双顶栏双侧栏 | `pattern-index.md` |
| 4 | 页面正选 | MS-09～13 组合页在微前端内仍用正选模板，非临时 Card 拼 | SEL-* |
| 5 | 截图 framing | 嵌入模式截图无侧栏压入主应用侧栏区域 | DRIFT-05 |

**交互动作**：对比「全量子应用」与「仅内容区嵌入」两种截图 → framing 与 golden 一致。

## MFE-05 — 跨应用导航、状态与发布

**对照 reference**：`version-pinning-guide.md`、`business-validation-checklist.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Skill pin 一致 | 各子应用 `design-system-pin.md` 指向同一 `pinned_commit` 或文档化差异 | ADOPT-04 |
| 2 | 共享状态 | 租户/用户上下文由主应用注入 props，子应用不写死 mock | SEL-05 |
| 3 | 发布顺序 | 主应用先升级壳层再升子应用，或反之有兼容矩阵 | `migration-playbook.md` |
| 4 | 冒烟范围 | 升级后 MS-09～13 至少抽 2 项在微前端环境重跑 | `business-validation-checklist.md` |
| 5 | 写回 | 微前端特有错选写入 `decision-matrix.md` when-not | SEL-* |

**交互动作**：升级 pin 后主应用 + 2 个子应用分别 `tsc --noEmit` → 共跑 1 项 MS 冒烟。

## 五类 SSR/微前端风险速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| SSR 构建失败 | `window is not defined`、hydration mismatch | `extension-audit.md` · SSR-02 | SSR-01 · SSR-02 |
| 图表/地图白块 | 客户端才渲染，SSR 无占位 | `api-override-recipes.md` | SSR-02 |
| 主题闪烁 | 刷新后先白后暗、class 不一致 | `token-index.md` | SSR-03 · VIS-02 |
| Portal 报错 | Dialog 打开 hydration 警告 | `engineering-guards.md` | SSR-04 |
| 微前端双壳层 | 两套侧栏/顶栏、内容被挤压 | `decision-matrix.md` MFE-04 | MFE-04 · DRIFT-05 |
| 路由 404 | 子应用刷新丢失 | `route-index.md` | MFE-03 |
| Token 冲突 | 主/子应用颜色互相覆盖 | `token-index.md` | MFE-02 · DRIFT-01 |

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# SSR 业务仓库
pnpm exec next build   # 或 remix build / 等价 SSR 构建
pnpm exec tsc --noEmit
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- SSR 或微前端路径在真实业务中**稳定复现失败**且根因为 Skill 文档缺口。
- 发现 client-only 组件未列降级或 dynamic import 模式缺失。
- 检索路径超过 3 跳才找到本清单或对应 SSR/MFE 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 SSR-01～05、MFE-01～05。

## 检索入口

| 意图 | 读 |
|---|---|
| CSR 首次接入 | `adoption-onboarding-checklist.md` |
| SSR / 微前端接入 | 本文件 SSR-01～05 / MFE-01～05 |
| client-only 降级 | `extension-audit.md` · `third-party-template.md` |
| MS 场景冒烟 | `business-validation-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` SSR-* / MFE-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
