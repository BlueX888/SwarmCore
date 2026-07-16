---
name: b-design-system-tailadmin-radix
description: |
  从 TailAdmin React Pro 抽取、面向 React + shadcn/ui + Radix + Tailwind CSS v4 的 Code Agent 设计系统 Skill。用于从 0 搭建管理后台、迁移已有 UI、补充缺失组件、评审 UI 一致性，或实现应遵守 TailAdmin 视觉与交互系统的页面。
---

# B Design System — TailAdmin × Radix

本 Skill 指导 Code Agent 以 **TailAdmin 视觉语言** 构建管理后台 UI，技术栈固定为 **React + shadcn/ui + Radix Primitives + Tailwind CSS v4**。

来源产品：**TailAdmin React Pro v2.3.1**。页面溯源见 `examples/b-design-system-tailadmin-radix/src/data/tailadminPageCatalog.ts`；本仓库不再 vendoring 源项目。源产品使用自定义组件；本 Skill 将视觉/交互规则映射到 shadcn/Radix 实现，不复制源项目的非 Radix 浮层实现。

## 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| 框架 | React 19 + TypeScript + Vite | 与源项目一致 |
| 路由 | react-router v7 | 嵌套 `Route` + `Outlet` |
| 组件基座 | shadcn/ui（Radix） | Dialog、DropdownMenu、Tabs、Tooltip、Popover 等 |
| 样式 | Tailwind CSS v4 `@theme` | 语义 Token 见 `references/token-index.md` |
| 类名合并 | `cn()` = clsx + tailwind-merge | `src/lib/utils.ts` |
| 变体 | `cva` | Button、Badge、Alert 等 |
| 图标 | TailAdmin SVG barrel / lucide-react / 项目 SVG barrel | 先查 `references/icon-system.md`；尺寸对齐 `size-4`/`size-5`/`size-6` |
| 暗色 | `html.dark` class | `@custom-variant dark (&:is(.dark *))` |

## 首次判断

| 任务 | 读取 |
|---|---|
| **不确定从哪读 / 检索路径** | `references/agent-retrieval-guide.md` → 本表对应行 |
| **MS-09～13 业务部署冒烟** | `references/business-validation-checklist.md` → `migration-scenarios.md` |
| **UI 漂移评审（PR/生成后抽检）** | `references/ui-drift-review-checklist.md` → `references/scene-ui-drift-review-checklist.md` |
| **Agent 失败模式评审（PR/生成后抽检）** | `references/agent-failure-patterns-review-checklist.md` → `references/scene-agent-failure-review-checklist.md` |
| **UiElements 键盘/hover/focus 评审** | `references/ui-elements-keyboard-hover-focus-review-checklist.md` → `references/scene-ui-elements-keyboard-hover-focus-review-checklist.md` |
| **UiElements empty/error/loading 评审** | `references/ui-elements-empty-error-loading-review-checklist.md` → `references/scene-ui-elements-empty-error-loading-review-checklist.md` |
| **UiElements 变体/交互态评审** | `references/ui-elements-variant-interaction-review-checklist.md` → `references/scene-ui-elements-variant-interaction-review-checklist.md` |
| **BI 图表深度交互评审** | `references/bi-chart-interaction-review-checklist.md` → `references/scene-bi-chart-interaction-review-checklist.md` |
| **复杂表单视觉回归评审** | `references/complex-form-visual-regression-review-checklist.md` → `references/scene-complex-form-visual-regression-review-checklist.md` |
| **页面族视觉回归评审** | `references/page-family-visual-regression-review-checklist.md` → `references/scene-page-family-visual-regression-review-checklist.md` |
| **场景页面视觉回归评审** | `references/scenario-page-visual-regression-review-checklist.md` → `references/scene-scenario-page-visual-regression-review-checklist.md` |
| **场景域独立截图评审** | `references/scenario-domain-independent-screenshot-review-checklist.md` → `references/scene-scenario-domain-independent-screenshot-review-checklist.md` |
| **场景域 light/dark 独立截图评审** | `references/scenario-domain-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-light-dark-screenshot-review-checklist.md` |
| **场景域 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域交互态打开态 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 disabled/loading tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 empty/error tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 partial/retry tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 refetch/pending tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 stale/optimistic tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 conflict/merge tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 offline/sync conflict tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道后续退役 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道后续清理 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道后续销毁 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道后续归档 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道背压/队列积压 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道熔断/限流 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 network partition/recovery tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md` |
| **场景域 mutation pending/rollback tablet/mobile light/dark 独立截图评审** | `references/scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md` → `references/scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md` |
| **首次接入 / vendoring 冒烟** | `references/adoption-onboarding-checklist.md` → `output-modes/from-zero.md` |
| **业务 copy Skill 后修复/改组件/准备回流本尊** | `references/upstream-contribution-guide.md` → `references/upstream-changelog-template.md` |
| **本尊吸收业务 upstream（给目录即可）** | `.cursor/commands/absorb-upstream.md` → `create-design-system/scripts/absorb_upstream.sh` |
| **SSR / 微前端接入冒烟** | `references/ssr-microfrontend-adoption-checklist.md` → `references/extension-audit.md` |
| **可访问性评审（PR/生成后抽检）** | `references/accessibility-review-checklist.md` → `references/scene-accessibility-review-checklist.md` |
| **响应式评审（PR/生成后抽检）** | `references/responsive-review-checklist.md` → `references/scene-responsive-review-checklist.md` |
| **数据状态与异步韧性评审（PR/生成后抽检）** | `references/async-state-review-checklist.md` → `references/scene-async-state-review-checklist.md` |
| **交互与动效评审（PR/生成后抽检）** | `references/interaction-motion-review-checklist.md` → `references/scene-interaction-review-checklist.md` |
| **中文示例文案评审（PR/生成后抽检）** | `references/chinese-copy-review-checklist.md` → `references/scene-chinese-copy-review-checklist.md` |
| **视觉 Token 与密度评审（PR/生成后抽检）** | `references/visual-token-review-checklist.md` → `references/scene-visual-token-review-checklist.md` |
| **表单校验与逻辑完备评审（PR/生成后抽检）** | `references/form-validation-logic-review-checklist.md` → `references/layout-patterns/crud-flow.md` |
| **产品逻辑完备评审（PR/生成后抽检）** | `references/logic-completeness-review-checklist.md` → `references/scene-logic-completeness-review-checklist.md` |
| **类型完整与 API 契约评审（PR/生成后抽检）** | `references/type-api-contract-review-checklist.md` → `references/scene-type-api-contract-review-checklist.md` |
| **生成一致性评审（PR/生成后抽检）** | `references/generation-consistency-review-checklist.md` → `references/scene-generation-consistency-review-checklist.md` |
| **组件覆盖率评审（PR/生成后抽检）** | `references/component-coverage-review-checklist.md` → `references/scene-component-coverage-review-checklist.md` |
| **模式覆盖评审（PR/生成后抽检）** | `references/pattern-coverage-review-checklist.md` → `references/scene-pattern-coverage-review-checklist.md` |
| **约束遵守评审（PR/生成后抽检）** | `references/constraint-compliance-review-checklist.md` → `references/scene-constraint-compliance-review-checklist.md` |
| 从 0 构建新页面/新应用 | `output-modes/from-zero.md` |
| 迁移或重构已有 UI | `output-modes/migration.md` |
| 补充缺失组件 | `output-modes/missing-component.md` |
| 评审 UI 质量或风格漂移 | `references/ui-drift-review-checklist.md` → `references/scene-ui-drift-review-checklist.md` |
| 页面级组合 | `references/route-index.md` → `references/pattern-index.md` → layout 文件 |
| 表单页面 / 查看态描述列表 | `references/layout-patterns/form-composition.md` → `references/decision-matrix.md` |
| 组件规则 | `references/component-index.md` → `references/component-styles/` |
| 不确定该用哪个组件/页面模板 | `references/decision-matrix.md` → `component-index.md` / `pattern-index.md` |
| 图标选择 / 图标风格一致性 | `references/icon-system.md` → `references/decision-matrix.md` |
| Token / 视觉 | `references/token-index.md`、`references/visual-language.md` |
| 交互与状态 | `references/state-index.md`、`references/interaction-motion.md` |
| 工程约束 | `references/engineering-guards.md` |
| 向后兼容 / 业务旧代码迁移 | `references/backward-compatibility.md` → `references/migration-playbook.md` → `references/upgrade-troubleshooting.md` → `references/api-contracts.md` → `references/migration-scenarios.md` → `references/migration-notes/` → `references/version-pinning-guide.md` → `references/merge-options-guide.md` → `references/api-override-recipes.md` → `references/scenario-override-recipes.md` |
| SaaS / 企业 / 政府 / PaaS 业务页面 | `references/domain-scenarios.md` → `references/pattern-index.md` → layout 文件 |
| 通用后台能力路线图 / 新需求开发 | `docs/spec/b-design-system-tailadmin-radix/prd.md` → `docs/spec/b-design-system-tailadmin-radix/prd/` → `references/capability-roadmap.md` |
| 真实 demo / 交互验证 / 可视化回归 | `examples/b-design-system-tailadmin-radix/` |
| **DeepTalk Gateway 双端**（SaaS + ToB） | `references/gateway-visual.md` + `references/gateway-interaction.md` → `docs/demand/gateway.md` |
| shadcn 预设 / 代码模板 | `templates/components.json`、`templates/lib/utils.ts`、`templates/lib/chart-theme.ts`、`templates/lib/fullcalendar-theme.ts`、`templates/lib/kanban-theme.ts`、`templates/lib/maps-theme.ts`、`templates/lib/vector-map-theme.ts`、`templates/lib/editor-theme.ts`、`templates/lib/carousel-theme.ts`、`templates/ui/button.tsx`、… |
| TailAdmin 内置图标资产 | `templates/icons/`（121 个 SVG + `index.ts`）→ `templates/icons/icon-registry.tsx` → `references/icon-system.md` |
| Chart / Calendar / Kanban / Maps / Editor / Carousel | `references/component-styles/chart-theme.md`、`fullcalendar-theme.md`、`kanban-theme.md`、`maps-theme.md`、`vector-map-theme.md`、`editor-theme.md`、`carousel-theme.md`、`third-party-template.md` |
| 体检 / 演化 | `docs/spec/b-design-system-tailadmin-radix/sop.md` → `state.md` |

## 核心规则

1. **先 Token 后类名**：使用 `brand-*`、`gray-*`、`success-*` 等语义 Token，禁止硬编码 hex。
2. **Radix 优先**：浮层、菜单、对话框、Tabs、Tooltip 必须用 shadcn/Radix，禁止手写 click-outside Modal。
3. **`cn()` + `cva`**：所有变体组件统一 `cn()` 合并；禁止模板字符串拼接 className。
4. **索引检索**：普通任务 ≤3 次 reference 读取；不扫描整个 Skill 目录。
5. **状态全覆盖**：hover、focus-visible、disabled、loading、empty、error、selected、dark、responsive。
6. **壳层比例固定**：侧栏 290px/90px、顶栏 sticky、内容区 `max-w-(--breakpoint-2xl)`。
7. **缺组件协议**：新增组件必须同步 `component-index.md`、detail 文件、状态示例。
8. **兼容优先**：已发布模板和组件契约不得静默破坏；破坏性变更必须提供 deprecated wrapper、migration note 和兼容期。
9. **Example 同步**：新增组件、页面模式或业务场景时，同步更新 `examples/b-design-system-tailadmin-radix/`，保持 Group / 组件 / 页面 / 场景 / 验证分组和打开态演示。
10. **静态 Preview 退役**：`b-design-system-tailadmin-radix/preview.html` 已移除；后续验收、查看、截图和 golden screen 全部以 `examples/b-design-system-tailadmin-radix` 的真实运行效果为准。

## 项目落地截图验收

在真实项目中使用本 Skill 生成或修改 UI 后，必须用截图或浏览器检查变更页面。截图出现以下任一情况，不允许标记为 pass：

- 首屏出现大面积无意义空白。
- 主内容列明显窄于可用页面宽度。
- KPI、按钮、表格单元格、Tabs、导航项、表单控件、Dialog、Drawer、Dropdown 的文字被裁切、遮挡、重叠或溢出。
- 卡片、栅格、工具栏、表格、看板等固定格式 UI 没有稳定响应式尺寸。
- desktop/tablet/mobile 中侧栏、顶栏、内容区 framing 明显错位。
- light/dark 主题中对比度丢失、边框层级丢失或主要控件不可读。

发现上述问题时，验收结论必须写为 `fail` 或 `pass-with-concerns`，先修布局，再声称完成；不得把这类截图计为视觉通过。

## shadcn 映射速查

| TailAdmin 概念 | shadcn 组件 | Radix 基座 |
|---|---|---|
| Button primary/outline | `Button` variant | — |
| Badge light/solid | `Badge` variant | — |
| InputField | `Input` + `Label` + `FormMessage` | — |
| Modal | `Dialog` | `@radix-ui/react-dialog` |
| Drawer | `Sheet` | `@radix-ui/react-dialog` |
| Dropdown | `DropdownMenu` | `@radix-ui/react-dropdown-menu` |
| Popover | `Popover` | `@radix-ui/react-popover` |
| Tooltip | `Tooltip` | `@radix-ui/react-tooltip` |
| Tabs | `Tabs` | `@radix-ui/react-tabs` |
| Alert | `Alert` | — |
| Table | `Table` | — |
| Switch | `Switch` | `@radix-ui/react-switch` |
| Checkbox/Radio | `Checkbox`/`RadioGroup` | Radix |
| DatePicker | `Popover` + `Calendar` | `@radix-ui/react-popover` · `templates/ui/date-picker.tsx` |
| MultiSelect | `Popover` + `Command` | 组合 · `templates/ui/multi-select.tsx` |
| FileUpload | native `input[type=file]` | `templates/ui/file-upload.tsx` |
| ThemeToggle | `ThemeProvider` + button | `templates/layout/theme-toggle.tsx` |
| Charts | ApexCharts | `templates/lib/chart-theme.ts` · `chart-theme.md` |
| FullCalendar | `@fullcalendar/react` | `templates/lib/fullcalendar-theme.ts` · `fullcalendar-theme.md` |
| Kanban | `react-dnd` | `templates/lib/kanban-theme.ts` · `templates/ui/kanban-column-menu.tsx` · `kanban-theme.md` |
| Maps | MapLibre / Leaflet / iframe | `templates/lib/maps-theme.ts` · `maps-theme.md` |
| Vector Map | `@react-jvectormap` | `templates/lib/vector-map-theme.ts` · `vector-map-theme.md` |
| Editor | `prismjs` | `templates/lib/editor-theme.ts` · `editor-theme.md` |
| Carousel | `swiper` | `templates/lib/carousel-theme.ts` · `carousel-theme.md` |
| TailAdmin Icons | SVG + SVGR | `templates/icons/` · `references/icon-system.md` |

## 体检门控（演化轮）

结构：`python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix`

内容：读 `docs/spec/b-design-system-tailadmin-radix/shards/scorecard.md`；总分 &lt; 88 时优先补 `third-party-template`、templates、preview 暗色。

## 完成前验证

- [ ] 语义 Token 与 TailAdmin 色板一致（brand-500 = `#465fff`）
- [ ] Radix 浮层 z-index 使用 `z-99999` 层级
- [ ] 表单控件高度 `h-11`、圆角 `rounded-lg`
- [ ] 暗色模式 `dark:` 变体完整
- [ ] `focus-visible:ring-3` 可见焦点环
- [ ] 已截图或浏览器检查 desktop/tablet/mobile 中适用视口；无大面积空白、内容列过窄、文本裁切、遮挡、重叠或 framing 错位
- [ ] 新增能力已在 `examples/b-design-system-tailadmin-radix/` 中补充可运行演示或验证项
- [ ] 组件索引已更新（若新增组件）
- [ ] TypeScript props 与 variants 有类型
