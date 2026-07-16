# 质量评审规程

用于 UI 评审和生成结果 QA。

## 分层评分

评审 `b-design-system-tailadmin-radix` 时必须拆开看，不能只看一个历史总分：

| 层级 | 当前评估重点 |
|---|---|
| Skill 体系质量 | SOP、PRD 分片、索引、兼容策略、评分与自演化闭环是否能持续发现不足。 |
| 组件/模板质量 | `templates/**` 是否是真实可复制组件，是否有 props、variants、状态、slots、dark、loading、error、disabled 等覆盖。 |
| 场景/页面质量 | 是否提供 SaaS、企业、政府、DevOps、PaaS、Gateway、BI、监控、大屏等完整页面组合，而不是只有孤立组件。 |
| Example/验收质量 | `examples/b-design-system-tailadmin-radix` 是否是真实运行的分组能力展厅，是否可交互，是否有打开态/动作后截图，是否能暴露遮挡、错位、裁切、大屏占位等问题。 |
| 业务部署验证质量 | MS-09～13 场景组合在业务仓库是否按 `business-validation-checklist.md` 通过受控 props 与交互冒烟。 |
| UI 漂移评审质量 | Agent 生成或改写页面是否按 `ui-drift-review-checklist.md` REV-01～05 与 `scene-ui-drift-review-checklist.md` REV-06～10 完成控件级与场景级 golden 对照，无 DRIFT-* / REV-06～10 症状。 |
| 首次接入质量 | 业务仓库首次 vendoring 是否按 `adoption-onboarding-checklist.md` ADOPT-01～05 完成脚手架、Token、壳层、pin 与首页 smoke。 |
| SSR/微前端接入质量 | SSR 或微前端环境是否按 `ssr-microfrontend-adoption-checklist.md` SSR-01～05 / MFE-01～05 完成 client 边界、dynamic import、壳层选型与 MS 抽检。 |
| 可访问性评审质量 | Agent 生成或改写页面是否按 `accessibility-review-checklist.md` A11Y-01～05 与 `scene-accessibility-review-checklist.md` A11Y-06～10 完成控件级与场景级键盘、标签、浮层、图标命名、对比度与 MS 场景可访问性束抽检。 |
| 响应式评审质量 | Agent 生成或改写页面是否按 `responsive-review-checklist.md` RESP-01～05 与 `scene-responsive-review-checklist.md` RESP-06～10 完成控件级与场景级 desktop/tablet/mobile 壳层、栅格、表单、表格与大屏抽检。 |
| 异步状态评审质量 | Agent 生成或改写页面是否按 `async-state-review-checklist.md` ASYNC-01～05 与 `scene-async-state-review-checklist.md` ASYNC-06～10 完成控件级与场景级 loading/empty/error/partial/retry 与 MS 场景异步束抽检。 |
| 交互与动效评审质量 | Agent 生成或改写页面是否按 `interaction-motion-review-checklist.md` INTER-01～05 与 `scene-interaction-review-checklist.md` INTER-06～10 完成控件级与场景级 hover/focus、浮层过渡、布尔控件、loading、微交互与 MS 场景交互束抽检。 |
| 中文示例文案评审质量 | Agent 生成或改写页面是否按 `chinese-copy-review-checklist.md` COPY-01～05 与 `scene-chinese-copy-review-checklist.md` COPY-06～10 完成表单、数据状态、壳层、领域 mock、浮层可读文案与 MS 场景中文文案抽检。 |
| 视觉 Token 与密度评审质量 | Agent 生成或改写页面是否按 `visual-token-review-checklist.md` VIS-01～05 与 `scene-visual-token-review-checklist.md` VIS-06～10 完成语义色、dark 对比、间距密度、圆角阴影层级、排版数字对齐与 MS 场景视觉束抽检。 |
| 表单校验与逻辑完备评审质量 | Agent 生成或改写页面是否按 `form-validation-logic-review-checklist.md` LOGIC-01～05 完成校验触发、破坏性动作、权限门禁、向导分步与 CRUD 闭环抽检。 |
| 产品逻辑完备评审质量 | Agent 生成或改写页面是否按 `logic-completeness-review-checklist.md` LOGIC-06～10 与 `scene-logic-completeness-review-checklist.md` LOGIC-06～10 完成用户流程导航、筛选因果链、主从上下文、审批配额规则与 MS 场景业务逻辑束抽检。 |
| 类型完整与 API 契约评审质量 | Agent 生成或改写页面是否按 `type-api-contract-review-checklist.md` TYPE-01～05 与 `scene-type-api-contract-review-checklist.md` TYPE-06～10 完成 props 导出、theme helper 签名、受控契约、additive 变更与 MS 场景类型抽检。 |
| 生成一致性评审质量 | Agent 生成或改写页面是否按 `generation-consistency-review-checklist.md` GEN-01～05 与 `scene-generation-consistency-review-checklist.md` GEN-06～10 完成选型、Token/密度、状态矩阵、检索路由与 MS 场景生成一致性抽检。 |
| 组件覆盖率评审质量 | Agent 生成或改写页面是否按 `component-coverage-review-checklist.md` COV-01～05 与 `scene-component-coverage-review-checklist.md` COV-06～10 完成主路径模板、extension-audit、preview/golden、变体矩阵与 MS 场景组件覆盖率抽检。 |
| 模式覆盖评审质量 | Agent 生成或改写页面是否按 `pattern-coverage-review-checklist.md` PAT-01～05 与 `scene-pattern-coverage-review-checklist.md` PAT-06～10 完成 output modes、页面/布局模式、状态模式、路由检索与 MS 场景页面组合抽检。 |
| 约束遵守评审质量 | Agent 生成或改写页面是否按 `constraint-compliance-review-checklist.md` CON-01～05 与 `scene-constraint-compliance-review-checklist.md` CON-06～10 完成语义 Token、框架 API、导入规则、Skill 红线与 MS 场景工程边界抽检。 |
| Agent 失败模式防御 | Agent 落地是否对照 `agent-failure-patterns-review-checklist.md` FAIL-01～05 与 `scene-agent-failure-review-checklist.md` FAIL-06～10，并通过 `verify:runtime` 截图与 audit 门禁。 |
| UiElements 键盘/hover/focus | Specimen Lab 是否对照 `ui-elements-keyboard-hover-focus-review-checklist.md` KBF-01～05 与 `scene-ui-elements-keyboard-hover-focus-review-checklist.md` KBF-06～10，并通过 `ui-elements-keyboard-hover-focus-gates.png` runtime 门禁。 |
| UiElements empty/error/loading | Specimen Lab 是否对照 `ui-elements-empty-error-loading-review-checklist.md` EEL-01～05 与 `scene-ui-elements-empty-error-loading-review-checklist.md` EEL-06～10，并通过 `ui-elements-empty-error-loading-gates.png` runtime 门禁。 |
| UiElements 变体/交互态 | Specimen Lab 是否对照 `ui-elements-variant-interaction-review-checklist.md` VAR-01～05 与 `scene-ui-elements-variant-interaction-review-checklist.md` VAR-06～10，并通过 `ui-elements-variant-interaction-gates.png` runtime 门禁。 |
| BI 图表深度交互 | Chart Builder / 指标页是否对照 `bi-chart-interaction-review-checklist.md` CHART-01～05 与 `scene-bi-chart-interaction-review-checklist.md` CHART-06～10，并通过 `bi-chart-interaction-gates.png` runtime 门禁。 |
| 页面族视觉回归 | Dashboard/AI/Auth 等页面族是否对照 `page-family-visual-regression-review-checklist.md` PFVR-01～05 与 `scene-page-family-visual-regression-review-checklist.md` PFVR-06～10，并通过 `page-family-visual-regression-gates.png` runtime 门禁。 |
| 复杂表单视觉回归 | FormPageShell/FormDrawer/FormDialog 等复杂表单是否对照 `complex-form-visual-regression-review-checklist.md` CFVR-01～05 与 `scene-complex-form-visual-regression-review-checklist.md` CFVR-06～10，并通过 `complex-form-visual-regression-gates.png` runtime 门禁。 |
| 场景页面视觉回归 | BI/DevOps/Gateway/Governance/PaaS 场景页是否对照 `scenario-page-visual-regression-review-checklist.md` SPVR-01～05 与 `scene-scenario-page-visual-regression-review-checklist.md` SPVR-06～10，并通过 `scenario-page-visual-regression-gates.png` runtime 门禁。 |
| 场景域独立截图 | 5 大场景域是否各有独立 `scenario-*-domain.png` 截图，对照 `scenario-domain-independent-screenshot-review-checklist.md` SDIS-01～05 与 `scene-scenario-domain-independent-screenshot-review-checklist.md` SDIS-06～10，并通过 `verifyScenarioDomainScreenshots` runtime 门禁。 |
| 场景域 light/dark 独立截图 | 5 大场景域是否各有 light + dark 独立 `scenario-*-domain.png` / `scenario-*-domain-dark.png` 截图，对照 `scenario-domain-light-dark-screenshot-review-checklist.md` SDLD-01～05 与 `scene-scenario-domain-light-dark-screenshot-review-checklist.md` SDLD-06～10，并通过 `verifyScenarioDomainLightDarkScreenshots` runtime 门禁。 |
| 场景域 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark 独立 `scenario-*-domain-{tablet,mobile}{,-dark}.png` 截图，对照 `scenario-domain-viewport-light-dark-screenshot-review-checklist.md` SDTM-01～05 与 `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md` SDTM-06～10，并通过 `verifyScenarioDomainViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域交互态打开态 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark 打开态独立 `scenario-*-domain-{tablet,mobile}{,-dark}-open.png` 截图，对照 `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDIO-01～05 与 `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDIO-06～10，并通过 `verifyScenarioDomainInteractiveOpenViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark 浮层打开态独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{dropdown,popover,command}-open.png` 截图，对照 `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDPC-01～05 与 `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDPC-06～10，并通过 `verifyScenarioDomainFloatingInteractiveOpenViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark Tooltip/Context Menu 打开态独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{tooltip,context-menu}-open.png` 截图，对照 `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDTC-01～05 与 `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDTC-06～10，并通过 `verifyScenarioDomainTooltipContextMenuInteractiveOpenViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark Hover 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-hover.png` 截图，对照 `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md` SDHO-01～05 与 `scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md` SDHO-06～10，并通过 `verifyScenarioDomainHoverViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark Focus 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-focus.png` 截图，对照 `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md` SDFK-01～05 与 `scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md` SDFK-06～10，并通过 `verifyScenarioDomainFocusKeyboardViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 disabled/loading tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark disabled/loading 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{disabled,loading}.png` 截图，对照 `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md` SDDL-01～05 与 `scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md` SDDL-06～10，并通过 `verifyScenarioDomainDisabledLoadingViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 empty/error tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark empty/error 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{empty,error}.png` 截图，对照 `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md` SDEE-01～05 与 `scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md` SDEE-06～10，并通过 `verifyScenarioDomainEmptyErrorViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 partial/retry tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark partial/retry 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{partial,retry}.png` 截图，对照 `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md` SDPR-01～05 与 `scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md` SDPR-06～10，并通过 `verifyScenarioDomainPartialRetryViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 refetch/pending tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark refetch/pending 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{pending,refetch}.png` 截图，对照 `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md` SDRP-01～05 与 `scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md` SDRP-06～10，并通过 `verifyScenarioDomainRefetchPendingViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 stale/optimistic tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark stale/optimistic 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{stale,optimistic}.png` 截图，对照 `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md` SDSO-01～05 与 `scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md` SDSO-06～10，并通过 `verifyScenarioDomainStaleOptimisticViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 conflict/merge tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark conflict/merged 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{conflict,merged}.png` 截图，对照 `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md` SDCM-01～05 与 `scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md` SDCM-06～10，并通过 `verifyScenarioDomainConflictMergeViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 offline/sync conflict tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark offline/synced 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{offline,synced}.png` 截图，对照 `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md` SDOSC-01～05 与 `scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md` SDOSC-06～10，并通过 `verifyScenarioDomainOfflineSyncConflictViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark sse-reconnecting/backpressure-released 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{sse-reconnecting,backpressure-released}.png` 截图，对照 `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md` SDSRB-01～05 与 `scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md` SDSRB-06～10，并通过 `verifyScenarioDomainSseReconnectBackpressureViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark long-polling/stream-subscribed 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{long-polling,stream-subscribed}.png` 截图，对照 `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md` SDLPS-01～05 与 `scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md` SDLPS-06～10，并通过 `verifyScenarioDomainLongPollingStreamSubscriptionViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark retry-active/dead-letter-drained 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{retry-active,dead-letter-drained}.png` 截图，对照 `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md` SDPCRDL-01～05 与 `scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md` SDPCRDL-06～10，并通过 `verifyScenarioDomainPushChannelRetryDeadLetterViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark subscription-confirm/idempotent-replay 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{subscription-confirm,idempotent-replay}.png` 截图，对照 `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md` SDPCSCIR-01～05 与 `scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md` SDPCSCIR-06～10，并通过 `verifyScenarioDomainPushChannelSubscriptionConfirmIdempotentReplayViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark audit-tracking-pending/audit-tracking-complete 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{audit-tracking-pending,audit-tracking-complete}.png` 截图，对照 `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md` SDPCAT-01～05 与 `scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md` SDPCAT-06～10，并通过 `verifyScenarioDomainPushChannelAuditTrackingViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark channel-lifecycle-pending/channel-lifecycle-complete 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-lifecycle-pending,channel-lifecycle-complete}.png` 截图，对照 `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md` SDPCLF-01～05 与 `scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md` SDPCLF-06～10，并通过 `verifyScenarioDomainPushChannelLifecycleViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道后续退役 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark channel-retirement-pending/channel-retirement-complete 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-retirement-pending,channel-retirement-complete}.png` 截图，对照 `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md` SDPCRET-01～05 与 `scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md` SDPCRET-06～10，并通过 `verifyScenarioDomainPushChannelRetirementViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道后续清理 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark channel-cleanup-pending/channel-cleanup-complete 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-cleanup-pending,channel-cleanup-complete}.png` 截图，对照 `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md` SDPCCLN-01～05 与 `scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md` SDPCCLN-06～10，并通过 `verifyScenarioDomainPushChannelCleanupViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道后续销毁 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark channel-destruction-pending/channel-destruction-complete 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-destruction-pending,channel-destruction-complete}.png` 截图，对照 `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md` SDPCDEST-01～05 与 `scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md` SDPCDEST-06～10，并通过 `verifyScenarioDomainPushChannelDestructionViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道后续归档 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark channel-archive-pending/channel-archive-complete 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-archive-pending,channel-archive-complete}.png` 截图，对照 `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md` SDPCARCH-01～05 与 `scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md` SDPCARCH-06～10，并通过 `verifyScenarioDomainPushChannelArchiveViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark compliance-trace-pending/compliance-trace-complete 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{compliance-trace-pending,compliance-trace-complete}.png` 截图，对照 `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md` SDPCCT-01～05 与 `scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md` SDPCCT-06～10，并通过 `verifyScenarioDomainPushChannelComplianceTraceViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark compensation-pending/reconciliation-complete 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{compensation-pending,reconciliation-complete}.png` 截图，对照 `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md` SDPCCR-01～05 与 `scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md` SDPCCR-06～10，并通过 `verifyScenarioDomainPushChannelCompensationReconciliationViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark async-pending/async-recovered 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{async-pending,async-recovered}.png` 截图，对照 `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md` SDPCAR-01～05 与 `scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md` SDPCAR-06～10，并通过 `verifyScenarioDomainPushChannelAsyncResilienceViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道背压/队列积压 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark backpressure-active/queue-drained 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{backpressure-active,queue-drained}.png` 截图，对照 `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md` SDPCBQ-01～05 与 `scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md` SDPCBQ-06～10，并通过 `verifyScenarioDomainPushChannelBackpressureQueueViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道熔断/限流 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark channel-breaker-open/rate-limit-released 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-breaker-open,rate-limit-released}.png` 截图，对照 `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md` SDPCBRL-01～05 与 `scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md` SDPCBRL-06～10，并通过 `verifyScenarioDomainPushChannelCircuitBreakerRateLimitViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark channel-degraded/channel-recovered 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-degraded,channel-recovered}.png` 截图，对照 `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md` SDPCDR-01～05 与 `scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md` SDPCDR-06～10，并通过 `verifyScenarioDomainPushChannelDegradationRecoveryViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark reconnecting/circuit-closed 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{reconnecting,circuit-closed}.png` 截图，对照 `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md` SDWRCB-01～05 与 `scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md` SDWRCB-06～10，并通过 `verifyScenarioDomainWebsocketReconnectCircuitBreakerViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark retrying/heartbeat-restored 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{retrying,heartbeat-restored}.png` 截图，对照 `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md` SDRHT-01～05 与 `scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md` SDRHT-06～10，并通过 `verifyScenarioDomainDisconnectRetryHeartbeatViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 network partition/recovery tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark partitioned/recovered 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{partitioned,recovered}.png` 截图，对照 `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md` SDNPR-01～05 与 `scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md` SDNPR-06～10，并通过 `verifyScenarioDomainNetworkPartitionRecoveryViewportLightDarkScreenshots` runtime 门禁。 |
| 场景域 mutation pending/rollback tablet/mobile light/dark 独立截图 | 5 大场景域是否各有 tablet/mobile light + dark mutation-pending/rollback 独立 `scenario-*-domain-{tablet,mobile}{,-dark}-{mutation-pending,rollback}.png` 截图，对照 `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md` SDMR-01～05 与 `scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md` SDMR-06～10，并通过 `verifyScenarioDomainMutationRollbackViewportLightDarkScreenshots` runtime 门禁。 |

短板封顶：

- Example/验收质量低于 85 时，整体成熟度最高 91。
- 组件/模板质量低于 88 时，整体成熟度最高 92。
- 场景/页面质量低于 88 时，模式覆盖最高 88。
- 只完成文档/SOP，但 example 仍是静态 mock、不可交互时，不得评 95+。
- 历史 scorecard 若未采用分层评分，必须在下一轮重评。
- Agent 常见失败见 `agent-failure-patterns.md` → `agent-failure-patterns-review-checklist.md` / `scene-agent-failure-review-checklist.md`；验收以 `examples/b-design-system-tailadmin-radix` 为准。
- UiElements 键盘/hover/focus 见 `ui-elements-keyboard-hover-focus-review-checklist.md` / `scene-ui-elements-keyboard-hover-focus-review-checklist.md`；验收以 `ui-elements-keyboard-hover-focus-gates.png` 为准。
- UiElements empty/error/loading 见 `ui-elements-empty-error-loading-review-checklist.md` / `scene-ui-elements-empty-error-loading-review-checklist.md`；验收以 `ui-elements-empty-error-loading-gates.png` 为准。
- UiElements 变体/交互态见 `ui-elements-variant-interaction-review-checklist.md` / `scene-ui-elements-variant-interaction-review-checklist.md`；验收以 `ui-elements-variant-interaction-gates.png` 为准。

## 中文示例文案规则

`b-design-system-tailadmin-radix` 默认服务中文 SaaS、企业、政府、PaaS、DevOps、BI 中后台项目。所有组件模板和 preview 中的用户可读示例文案必须默认使用中文，包括：

- mock 数据、表格行数据、状态说明、空态/错误/加载文案。
- placeholder、helper、tooltip、按钮文案、Toast/Dialog 文案。
- `aria-label`、`aria-labelledby` 对应的可读标签。
- 大屏、监控、运维、BI、网关、代码平台示例中的业务标题和字段展示名。

允许保留英文的范围：

- 组件名、类型名、变量名、文件名、导入路径和第三方 API。
- 技术缩写和业界固定术语，例如 API、CI/CD、K8s、SLA、P95、QPS。
- 可复制代码中的真实协议、域名、token 前缀、HTTP method。

若模板或 preview 大量出现英文 mock/placeholder 且没有 props 覆盖或 i18n 入口，综合美学最高 88，约束遵守最高 88。

| 维度 | 检查内容 |
|---|---|
| 生成一致性 | 相同参考能稳定产出组件选择、Token、间距和状态。 |
| 组件覆盖率 | 所需基础组件、复合组件、布局、反馈、浮层、业务组件存在，或有明确缺组件路径。 |
| 类型完整 | props、variants、受控状态、数据模型和示例可发现且类型完整。 |
| 模式覆盖 | 表单、表格、仪表盘、详情、登录、设置、加载、空态、错误、响应式、权限状态有覆盖。 |
| 约束遵守 | 语义 Token、框架 API、可访问性、导入规则和设计限制被遵守。 |
| 逻辑完备 | 用户流程、校验、权限、破坏性动作和异步状态符合产品逻辑。 |
| 扩展性与灵活性 | props、slots、variants、状态机、数据适配、项目 override、降级方案足以支撑多业务复用。 |
| 交互与动效质量 | hover、focus、pressed、selected、loading、open/close 动效流畅且克制。 |
| 综合美学 | 比例、密度、语义、逻辑美学共同形成精致高端结果。 |

## 扩展性与灵活性评审

已实现的模板、插件主题或复合组件不能只检查“能渲染”。每轮评分必须回答：

- API 是否支持受控/非受控、关键回调、常用 slots、className 覆盖和项目级 Token 覆盖。
- 变体是否覆盖 size、density、intent、status、dark、loading、disabled、readonly、error。
- 数据是否支持空值、长文本、大数据量、异步刷新、局部失败、权限禁用和只读模式。
- 第三方库是否有主题隔离、CSS override 边界、替代/降级方案和 SSR/懒加载说明。
- 场景是否可迁移到 SaaS、企业、政府、PaaS、DevOps、控制平面等不同后台域。
- 新增能力是否更新 `component-index.md`、`pattern-index.md`、对应 `prd/Fxx-*.md` 和 preview 截图。

若组件只有单一静态样例、props 无类型边界、无状态矩阵或无降级方案，扩展性与灵活性不得高于 85；若还依赖项目专有路由/品牌/文案才能工作，不得高于 80。

## 美学评审

- 比例：页面壳、内容区、控件、图标比例有秩序。
- 密度：信息紧凑、可读、可扫描。
- 语义：色彩、层级、图标、状态表达明确含义。
- 逻辑：布局和动作位置体现对产品任务的理解。

## 截图失败红线

截图出现以下任一问题时，综合美学不得评为通过：

- 首屏主内容列异常窄，右侧或下方有大面积无意义空白。
- KPI、表格、按钮、标签、导航、表单、弹窗或下拉中的文字被裁切、遮挡、重叠或溢出。
- 固定格式 UI（卡片、栅格、工具栏、表格、看板、计数器）在 hover、加载、长文案或响应式视口下改变尺寸并破坏布局。
- 侧栏、顶栏、内容区 framing 明显错位，截图不能代表目标视口的真实布局。
- light/dark 任一主题中主要控件不可读、边框层级丢失或对比度不足。
- example 左侧导航没有分组，组件、规格、场景和页面混在一个长页面。
- Select、DatePicker、MultiSelect、Dialog、Drawer、Table、Switch、Checkbox、Radio、Slider 等组件不能真实交互。
- 弹层、日期面板、下拉、多选列表、Tooltip、Popover、Command 或 Drawer 遮挡后续组件到无法阅读。
- Switch、Checkbox、Radio、Slider、Loading 或 Progress 出现圆点/轨道错位、动效脱离容器或 loading 贴边。
- BI/Data Screen/监控大屏只有空容器、假柱状条、示意文本或低信息密度 placeholder。

此类问题必须标记为 `fail` 或 `pass-with-concerns`，并进入下一轮修复项。可执行检查项见 `ui-drift-review-checklist.md`（DOCS-007）。
