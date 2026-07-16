# Code Agent 检索路径指南

> DOCS-005 / G54 产物。帮助 Code Agent 在 **≤3 次 reference 读取** 内定位正确规则、模板与迁移路径，减少目录扫描与错选。

## 使用原则

1. **先判任务类型**，再打开对应 output mode 或本指南路由表。
2. **禁止** 无差别 `rg` 整个 Skill 目录；优先索引 → 分类 detail → 模板文件。
3. 组件/页面不确定时，**必须先读** `decision-matrix.md`，再查 `component-index.md` 或 `pattern-index.md`。
4. 升级 Skill 快照后出现回归，**必须先读** `upgrade-troubleshooting.md` 症状 ID，再查 playbook / SOR。
5. 图标语义不确定时，**必须先读** `icon-system.md`，禁止随机 lucide 替换 TailAdmin 已有 SVG。

## 任务路由表（≤3 跳）

| 任务 | 第 1 跳 | 第 2 跳 | 第 3 跳（可选） |
|---|---|---|---|
| 从 0 搭建新后台 | `output-modes/from-zero.md` | `adoption-onboarding-checklist.md` | `route-index.md` → layout 模板 |
| 首次 vendoring / pin Skill | `adoption-onboarding-checklist.md` | `version-pinning-guide.md` | `engineering-guards.md` |
| 业务改 Skill copy / 准备回流本尊 | `upstream-contribution-guide.md` | `upstream-changelog-template.md` | `backward-compatibility.md` |
| 本尊吸收业务 upstream | `.cursor/commands/absorb-upstream.md` | `create-design-system/scripts/absorb_upstream.sh` | `api-contracts.md` |
| SSR / 微前端接入 Skill | `ssr-microfrontend-adoption-checklist.md` | `adoption-onboarding-checklist.md` | `extension-audit.md` |
| 迁移 TailAdmin 源组件 | `output-modes/migration.md` | `component-index.md` | `component-styles/*-template.md` |
| 升级已 vendored Skill | `version-pinning-guide.md` | `migration-playbook.md` | `upgrade-troubleshooting.md` |
| 业务页部署冒烟（MS-09～13） | `business-validation-checklist.md` | `migration-scenarios.md` | `decision-matrix.md` MS 表 |
| PR 前 Agent 常见失败自检 | `agent-failure-patterns.md` | `agent-failure-patterns-review-checklist.md` | `scene-agent-failure-review-checklist.md` |
| Specimen Lab 键盘/hover/focus 抽检 | `interaction-motion.md` | `ui-elements-keyboard-hover-focus-review-checklist.md` | `scene-ui-elements-keyboard-hover-focus-review-checklist.md` |
| Specimen Lab empty/error/loading 抽检 | `state-index.md` | `ui-elements-empty-error-loading-review-checklist.md` | `scene-ui-elements-empty-error-loading-review-checklist.md` |
| Specimen Lab 变体/交互态抽检 | `component-index.md` | `ui-elements-variant-interaction-review-checklist.md` | `scene-ui-elements-variant-interaction-review-checklist.md` |
| BI 图表深度交互抽检 | `component-index.md` | `bi-chart-interaction-review-checklist.md` | `scene-bi-chart-interaction-review-checklist.md` |
| 复杂表单视觉回归抽检 | `form-composition.md` | `complex-form-visual-regression-review-checklist.md` | `scene-complex-form-visual-regression-review-checklist.md` |
| 页面族视觉回归抽检 | `component-index.md` | `page-family-visual-regression-review-checklist.md` | `scene-page-family-visual-regression-review-checklist.md` |
| 场景页面视觉回归抽检 | `domain-scenarios.md` | `scenario-page-visual-regression-review-checklist.md` | `scene-scenario-page-visual-regression-review-checklist.md` |
| 场景域独立截图抽检 | `domain-scenarios.md` | `scenario-domain-independent-screenshot-review-checklist.md` | `scene-scenario-domain-independent-screenshot-review-checklist.md` |
| 场景域 light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-light-dark-screenshot-review-checklist.md` |
| 场景域 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域交互态打开态 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 disabled/loading tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 empty/error tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 partial/retry tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 refetch/pending tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 stale/optimistic tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 conflict/merge tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 offline/sync conflict tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道背压/队列积压 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道后续退役 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道后续清理 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道后续销毁 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道后续归档 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道熔断/限流 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 network partition/recovery tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md` |
| 场景域 mutation pending/rollback tablet/mobile light/dark 独立截图抽检 | `domain-scenarios.md` | `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md` | `scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md` |
| PR 前可访问性抽检 | `accessibility-review-checklist.md` | `scene-accessibility-review-checklist.md` | `engineering-guards.md` |
| PR 前响应式抽检 | `responsive-review-checklist.md` | `scene-responsive-review-checklist.md` | `golden-screens.md` |
| PR 前异步状态抽检 | `async-state-review-checklist.md` | `scene-async-state-review-checklist.md` | `state-index.md` |
| PR 前交互与动效抽检 | `interaction-motion-review-checklist.md` | `scene-interaction-review-checklist.md` | `interaction-motion.md` |
| PR 前中文文案抽检 | `chinese-copy-review-checklist.md` | `scene-chinese-copy-review-checklist.md` | `quality-rubric.md` |
| PR 前视觉 Token 抽检 | `visual-token-review-checklist.md` | `scene-visual-token-review-checklist.md` | `visual-language.md` |
| PR 前逻辑完备抽检 | `form-validation-logic-review-checklist.md` | `logic-completeness-review-checklist.md` | `scene-logic-completeness-review-checklist.md` |
| PR 前类型契约抽检 | `type-api-contract-review-checklist.md` | `scene-type-api-contract-review-checklist.md` | `api-contracts.md` |
| PR 前生成一致性抽检 | `generation-consistency-review-checklist.md` | `scene-generation-consistency-review-checklist.md` | `decision-matrix.md` |
| PR 前组件覆盖率抽检 | `component-coverage-review-checklist.md` | `scene-component-coverage-review-checklist.md` | `component-index.md` |
| PR 前模式覆盖抽检 | `pattern-coverage-review-checklist.md` | `scene-pattern-coverage-review-checklist.md` | `pattern-index.md` |
| PR 前约束遵守抽检 | `constraint-compliance-review-checklist.md` | `scene-constraint-compliance-review-checklist.md` | `engineering-guards.md` |
| 补充缺失组件 | `output-modes/missing-component.md` | `component-styles/_index.md` | 对应 `*-template.md` + `templates/` |
| UiElements 原子模板（Tabs/Tooltip/Segmented 等） | `component-index.md` | `templates/ui/tabs.tsx` 等 | `navigation-template.md` / `overlay-template.md` / `primitive-template.md` |
| 不确定用哪个组件 | `decision-matrix.md` | `component-index.md` | `templates/ui/*.tsx` |
| 不确定用哪个页面模板 | `decision-matrix.md` | `pattern-index.md` | `domain-scenarios.md` |
| 表单页 / 查看态 | `layout-patterns/form-composition.md` | `decision-matrix.md` | `templates/layout/*.tsx` |
| BI / 大屏 / 联动分析 | `domain-scenarios.md` | `prd/F11-bi-analytics.md`（spec） | `templates/bi/*.tsx` |
| DevOps / CI/CD | `domain-scenarios.md` | `component-styles/devops-template.md` | `templates/devops/*.tsx` |
| 网关 / 控制平面 | `gateway-template.md` | `templates/gateway/*.tsx` | `scenario-override-recipes.md#sor-05` |
| PaaS 资源管理 | `component-styles/paas-template.md` | `templates/paas/*.tsx` | `scenario-override-recipes.md#sor-03` |
| 治理 / RBAC / 审计 | `component-styles/governance-template.md` | `templates/governance/*.tsx` | `scenario-override-recipes.md#sor-04` |
| 复杂组件 override | `api-override-recipes.md` | `merge-options-guide.md` | `templates/lib/*-theme.ts` |
| 多项目 brand/density/copy/shell | `brand-preset.ts` / `density-preset.ts` / `copy-preset.ts` / `shell-preset.ts` | `scenario-override-recipes.md` | example `token-density` / `page-dashboard` |
| 场景组合 override | `scenario-override-recipes.md` | `decision-matrix.md` | 对应 `templates/*/` 组合页 |
| Token / 视觉密度 | `token-index.md` | `visual-language.md` | `index.css` @theme |
| 交互 / 动效 / 状态 | `interaction-motion-review-checklist.md` | `scene-interaction-review-checklist.md` | `interaction-motion.md` |
| 图标选型 | `icon-system.md` | `templates/icons/icon-registry.tsx` | `decision-matrix.md#图标选型` |
| UI 质量评审 | `ui-drift-review-checklist.md` | `scene-ui-drift-review-checklist.md` | example runtime 截图 |
| 可访问性评审 | `accessibility-review-checklist.md` | `scene-accessibility-review-checklist.md` | `engineering-guards.md` |
| 响应式评审 | `responsive-review-checklist.md` | `scene-responsive-review-checklist.md` | `golden-screens.md` |
| 异步状态评审 | `async-state-review-checklist.md` | `state-index.md` | `prd/F02-data-state.md` |
| 交互与动效评审 | `interaction-motion-review-checklist.md` | `scene-interaction-review-checklist.md` | `interaction-motion.md` |
| 中文示例文案评审 | `chinese-copy-review-checklist.md` | `scene-chinese-copy-review-checklist.md` | `quality-rubric.md` |
| 视觉 Token 与密度评审 | `visual-token-review-checklist.md` | `scene-visual-token-review-checklist.md` | `visual-language.md` |
| 表单校验与逻辑完备评审 | `form-validation-logic-review-checklist.md` | `logic-completeness-review-checklist.md` | `layout-patterns/crud-flow.md` |
| 产品逻辑完备评审 | `logic-completeness-review-checklist.md` | `scene-logic-completeness-review-checklist.md` | `layout-patterns/bi-filter-linkage.md` |
| 类型完整与 API 契约评审 | `type-api-contract-review-checklist.md` | `scene-type-api-contract-review-checklist.md` | `api-contracts.md` |
| 生成一致性评审 | `generation-consistency-review-checklist.md` | `scene-generation-consistency-review-checklist.md` | `decision-matrix.md` |
| 组件覆盖率评审 | `component-coverage-review-checklist.md` | `component-index.md` | `extension-audit.md` |
| 模式覆盖评审 | `pattern-coverage-review-checklist.md` | `scene-pattern-coverage-review-checklist.md` | `pattern-index.md` |
| 约束遵守评审 | `constraint-compliance-review-checklist.md` | `scene-constraint-compliance-review-checklist.md` | `engineering-guards.md` |
| 向后兼容 / 破坏性变更 | `backward-compatibility.md` | `migration-notes/` | `api-contracts.md` |
| 演化 / 体检 | `docs/spec/.../sop.md` | `state.md` | `shards/scorecard.md` |

## 常见误路由与纠正

| 误路由 | 正确路径 | 关联症状 |
|---|---|---|
| 直接搜 `templates/` 找页面 | `pattern-index.md` → 场景模板 | SEL-* |
| 金额/密钥用普通 Input | `decision-matrix.md` → AdvancedInput / SecretInput | SEL-* |
| BI 单图接 CrossFilterDashboard | `DrillDownDashboard` 或 StatMetric 卡片 | SEL-01 / MS-11 |
| CI/CD 页只用 Kanban | `CicdRunDetail` 或 PipelineStageBar + Table | SEL-02 / MS-10 |
| PaaS 列表硬塞地图 Card | `ResourceTable` + 可选 Maps panel | SEL-03 / MS-12 |
| RBAC 用 Switch 列表 | `PermissionMatrix` + `AuditLogTable` | SEL-04 / MS-13 |
| 网关子面板写死 mock | `ControlPlaneHub` 受控 props | SEL-05 / MS-09 |
| Carousel options 被覆盖 | `merge-options-guide.md` → `mergeSwiperOptionsDeep` | MER-01 |
| Chart series 深嵌套丢失 | `getBaseChartOptions` + `deepMergeOptions` | MER-02 |
| 升级后类型错误 | `upgrade-troubleshooting.md` TS-* | MS-01～08 / MN-* |
| SSR hydration / 构建失败 | `upgrade-troubleshooting.md` SSR-* | `ssr-microfrontend-adoption-checklist.md` |
| 微前端双壳层/路由错位 | `upgrade-troubleshooting.md` MFE-* | `decision-matrix.md` MFE-04 |
| 图标按钮无名称 | `upgrade-troubleshooting.md` A11Y-04 | `accessibility-review-checklist.md` |
| Dialog 焦点不回 | `upgrade-troubleshooting.md` A11Y-03 | `state-index.md` |
| tablet KPI 仍 4 列或首屏空白 | `upgrade-troubleshooting.md` RESP-02 / RESP-06 | `scene-responsive-review-checklist.md` |
| BI 筛选硬编码色或 Chart SSR 直渲 | `upgrade-troubleshooting.md` CON-06 | `scene-constraint-compliance-review-checklist.md` |
| mobile 表格撑破壳层 | `upgrade-troubleshooting.md` RESP-04 | `master-detail-ops.md` |
| 页面长时间空白无 loading | `upgrade-troubleshooting.md` ASYNC-01 | `async-state-review-checklist.md` |
| 表格翻页后数据静默失败 | `upgrade-troubleshooting.md` ASYNC-02 | `prd/F02-data-state.md` |
| Switch 圆点错位或 Dialog 无过渡 | `upgrade-troubleshooting.md` INTER-03 / INTER-02 | `interaction-motion-review-checklist.md` |
| BI 大屏假占位或 CI/CD 阶段无 active | `upgrade-troubleshooting.md` INTER-06 / INTER-07 | `scene-interaction-review-checklist.md` |
| placeholder/空态/Dialog 仍为英文 | `upgrade-troubleshooting.md` COPY-01 / COPY-02 | `chinese-copy-review-checklist.md` |
| BI/Gateway/PaaS 场景 mock 英文混杂 | `upgrade-troubleshooting.md` COPY-06 / COPY-08 | `scene-chinese-copy-review-checklist.md` |
| 硬编码色/KPI 密度突变/dark 边框丢失 | `upgrade-troubleshooting.md` VIS-01 / VIS-03 | `visual-token-review-checklist.md` |
| BI 大屏假占位/Gateway 配额条无语义色 | `upgrade-troubleshooting.md` VIS-06 / VIS-08 | `scene-visual-token-review-checklist.md` |
| 无确认删除/toast-only 校验/RBAC Switch 冒充 | `upgrade-troubleshooting.md` LOGIC-02 / LOGIC-03 | `form-validation-logic-review-checklist.md` |
| 返回丢筛选/筛选无反馈/主从上下文丢失 | `upgrade-troubleshooting.md` LOGIC-06 / LOGIC-07 / LOGIC-08 | `logic-completeness-review-checklist.md` / `scene-logic-completeness-review-checklist.md` |
| 升级后 `tsc` 报错/props 对不上 | `upgrade-troubleshooting.md` TYPE-01 / TS-* | `scene-type-api-contract-review-checklist.md` |
| BI 单图冒充联动或 CI/CD 误用 Kanban | `upgrade-troubleshooting.md` GEN-06 / GEN-07 | `scene-generation-consistency-review-checklist.md` |
| BI 缺 `templates/bi/*` 或 DevOps 缺领域模板 | `upgrade-troubleshooting.md` COV-06 / COV-07 | `scene-component-coverage-review-checklist.md` |
| BI 缺 layout pattern 或 CI/CD 误用 Kanban 页面模式 | `upgrade-troubleshooting.md` PAT-06 / PAT-07 | `scene-pattern-coverage-review-checklist.md` |
| `audit_*` CI 失败 | `upgrade-troubleshooting.md` RUN-* | 对应 MS / MN |

## 预防性场景快速索引（MS-09～13）

业务使用以下组合页时，升级 pin 前必须确认受控 props，而非 Skill 内部 mock：

| MS | 场景 | 正选模板 | 常见误选 | SOR |
|---|---|---|---|---|
| MS-09 | 企业网关控制平面 | `ControlPlaneHub` | 散落 Card + 硬编码 mock | SOR-05 |
| MS-10 | DevOps 发布看板 | `CicdRunDetail` | 纯 `KanbanBoard` | SOR-02 |
| MS-11 | BI 联动仪表盘 | `CrossFilterDashboard` | 单图 + 手写 onClick | SOR-01 |
| MS-12 | PaaS 资源监控地图 | `ResourceTable` + Maps | 无地图语义的扁平表 | SOR-03 |
| MS-13 | 治理安全控制台 | `PermissionMatrix` + `AuditLogTable` | Switch 列表冒充 RBAC | SOR-04 |

详情见 `migration-scenarios.md` 各 MS 章节、`scenario-override-recipes.md` 与 `business-validation-checklist.md`。

## 验证命令（业务仓库）

升级或大规模生成后，按优先级执行：

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/run_token_hit_tests.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
```

任一失败：查 `upgrade-troubleshooting.md` 的 `RUN-*` 与对应 `TS-*` / `SEL-*` 症状行。

## 自我演化写回

Agent 在业务落地中发现以下情况，必须写回 `decision-matrix.md` 并在 spec `state.md` 登记下轮选题：

- 新高频业务意图无矩阵行。
- 检索路径超过 3 跳仍找不到模板。
- 错选导致 preview 失败或截图验收 fail。
- 真实升级故障未覆盖在 `upgrade-troubleshooting.md` 症状表。

业务 copy Skill 后的可泛化改动，按 `upstream-contribution-guide.md` 登记 `docs/design-system-upstream.md`（模板见 `upstream-changelog-template.md`），不得只改 runtime 不记条目。
