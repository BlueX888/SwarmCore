# 向后兼容与迁移策略

TailAdmin-Radix Skill 会持续自动演化，但业务项目可能已经复制了旧模板或在页面中使用旧组件契约。自动演化不得静默破坏这些业务代码。

## 兼容原则

- 新增能力优先使用新 props、variant、slot、recipe，不直接删除旧 API。
- 组件重构时保留旧组件名或旧 props 的 wrapper/alias，内部转接到新实现。
- 破坏性变更必须写 migration note，说明旧用法、新用法、影响范围和替代路径。
- 旧 API 标为 deprecated 后至少保留一个演化周期，不得同轮新增替代并删除旧 API。
- 真实业务项目应以 Git commit、tag、版本号或 vendored copy 固定已采用的设计系统快照。
- 除非用户明确要求迁移，不主动批量重写业务项目中的旧组件调用。

## TailAdmin-Radix 破坏性变更

以下变化视为破坏性变更：

- 删除或改名导出组件、props、variant、class 常量、theme helper。
- 改变默认尺寸、密度、DOM 语义或交互行为，导致旧截图/测试明显变化。
- 替换第三方库封装方式且没有 fallback。
- 删除旧 preview frame 或旧文档入口，导致业务 Agent 找不到旧用法。

## 迁移要求

发生破坏性变更时，必须同时提供：

- Deprecated wrapper 或 alias。
- 旧用法到新用法示例。
- 影响范围：组件、页面模式、preview、截图、业务项目可能使用点。
- 回滚方式或兼容期说明。
- `component-index.md`、相关 `prd/Fxx-*.md`、`scorecard.md` 风险记录。

## 使用建议

- 新页面使用最新模板。
- 旧页面维护时优先保持旧契约，除非本次任务就是迁移。
- 大规模迁移先出 checklist，再按模块逐步替换。
- 旧代码只要满足截图、可访问性、类型和业务逻辑验收，不因 Skill 新增能力而强制改写。

## 公开 API 契约（COMPAT-001）

已实现复杂组件的导出名、props、variants、theme helpers 摘要见 `api-contracts.md`。

| 类别 | 组件 | 契约等级 | 破坏性风险 |
|---|---|---|---|
| theme lib | Chart、FullCalendar、Maps、Vector Maps、Carousel | stable / theme-only | 低 |
| theme lib | Editor | evolving / theme-only | 中（缺 CodeBlock 组件） |
| React 模板 | KanbanBoard、DatePicker、MultiSelect、FileUpload | stable / evolving | 低～中 |
| React 模板 | ThemeToggle（`ThemeToggleButton`）、Command/SearchCommand | stable | 低 |

演化前必须先查 `api-contracts.md` 风险总表；发生破坏性变更时复制 `migration-note-template.md` 填写。

## Skill 快照固定（COMPAT-002）

业务项目 vendored 或复制模板后，应固定 Skill commit 快照，避免自动演化静默破坏已验收页面。详见 `version-pinning-guide.md`。

升级前必做：

1. 对比 `api-contracts.md` 风险总表。
2. 查阅 `migration-playbook.md` 场景路由表，定位 MS-01～MS-13 对应 MN / override / SOR 路径。
3. 升级后若出现类型/视觉/merge/错选回归，查 `upgrade-troubleshooting.md` 症状路由表与回滚决策树。
4. 不确定检索路径时，先读 `agent-retrieval-guide.md` 任务路由表（≤3 跳规则）。
5. MS-09～13 场景组合页部署前，按 `business-validation-checklist.md` 冒烟验证。
6. Agent 生成或大规模 UI 改写后，按 `ui-drift-review-checklist.md` 抽检 REV-01～05；对 BI/DevOps/Gateway/PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-ui-drift-review-checklist.md`（DOCS-034 / G83）。
7. 业务仓库**首次**接入 Skill 时，按 `adoption-onboarding-checklist.md` 完成 ADOPT-01～05。
8. SSR 或微前端环境接入时，按 `ssr-microfrontend-adoption-checklist.md` 完成 SSR-01～05 / MFE-01～05。
9. PR 前或大规模生成后，按 `accessibility-review-checklist.md` 抽检 A11Y-01～05；对 BI/DevOps/Gateway/PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-accessibility-review-checklist.md`（DOCS-026 / G75）。
10. PR 前或大规模生成后，按 `responsive-review-checklist.md` 抽检 RESP-01～05；对 BI/DevOps/Gateway/PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-responsive-review-checklist.md`（DOCS-027 / G76）。
11. PR 前或大规模生成后，按 `async-state-review-checklist.md` 抽检 ASYNC-01～05。
12. PR 前或大规模生成后，按 `interaction-motion-review-checklist.md` 抽检 INTER-01～05；按 `scene-interaction-review-checklist.md` 抽检 INTER-06～10。
13. PR 前或大规模生成后，按 `chinese-copy-review-checklist.md` 抽检 COPY-01～05；对 BI/DevOps/Gateway/PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-chinese-copy-review-checklist.md`（DOCS-029 / G78）。
14. PR 前或大规模生成后，按 `visual-token-review-checklist.md` 抽检 VIS-01～05；按 `scene-visual-token-review-checklist.md` 抽检 VIS-06～10。
15. PR 前或大规模生成后，按 `form-validation-logic-review-checklist.md` 抽检 LOGIC-01～05。
16. PR 前或大规模生成后，按 `type-api-contract-review-checklist.md` 抽检 TYPE-01～05；对 BI/DevOps/Gateway/PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-type-api-contract-review-checklist.md`（DOCS-033 / G82）。
17. PR 前或大规模生成后，按 `generation-consistency-review-checklist.md` 抽检 GEN-01～05；对 BI/DevOps/Gateway/PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-generation-consistency-review-checklist.md`（DOCS-030 / G79）。
18. PR 前或新增组件后，按 `component-coverage-review-checklist.md` 抽检 COV-01～05；对 BI/DevOps/Gateway/PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-component-coverage-review-checklist.md`（DOCS-031 / G80）。
19. PR 前或新增页面模式后，按 `pattern-coverage-review-checklist.md` 抽检 PAT-01～05；对 BI/DevOps/Gateway/PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-pattern-coverage-review-checklist.md`（DOCS-032 / G81）。
20. PR 前或大规模生成后，按 `constraint-compliance-review-checklist.md` 抽检 CON-01～05；对 BI/DevOps/Gateway/PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-constraint-compliance-review-checklist.md`（DOCS-028 / G77）。
21. PR 前或大规模生成后，按 `logic-completeness-review-checklist.md` 抽检 LOGIC-06～10；对 BI/DevOps/Gateway/PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-logic-completeness-review-checklist.md`（DOCS-035 / G84）。
22. PR 前或大规模 Agent 生成后，按 `agent-failure-patterns-review-checklist.md` 抽检 FAIL-01～05；对 BI/DevOps/Gateway/PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-agent-failure-review-checklist.md`（DOCS-036 / G85）。
23. Specimen Lab / UiElements 键盘、hover、focus 与失败态抽检见 `ui-elements-keyboard-hover-focus-review-checklist.md`（KBF-01～05）与 `scene-ui-elements-keyboard-hover-focus-review-checklist.md`（KBF-06～10）（DOCS-037 / G86）。
24. Specimen Lab / UiElements empty/error/loading 失败态抽检见 `ui-elements-empty-error-loading-review-checklist.md`（EEL-01～05）与 `scene-ui-elements-empty-error-loading-review-checklist.md`（EEL-06～10）（DOCS-038 / G87）。
25. Specimen Lab / UiElements 变体/交互态抽检见 `ui-elements-variant-interaction-review-checklist.md`（VAR-01～05）与 `scene-ui-elements-variant-interaction-review-checklist.md`（VAR-06～10）（DOCS-039 / G88）。
26. Chart Builder / BI 图表深度交互抽检见 `bi-chart-interaction-review-checklist.md`（CHART-01～05）与 `scene-bi-chart-interaction-review-checklist.md`（CHART-06～10）（DOCS-040 / G89）。
27. 页面族视觉回归抽检见 `page-family-visual-regression-review-checklist.md`（PFVR-01～05）与 `scene-page-family-visual-regression-review-checklist.md`（PFVR-06～10）（DOCS-041 / G90）。
28. 复杂表单视觉回归抽检见 `complex-form-visual-regression-review-checklist.md`（CFVR-01～05）与 `scene-complex-form-visual-regression-review-checklist.md`（CFVR-06～10）（DOCS-042 / G91）。
29. 场景页面视觉回归抽检见 `scenario-page-visual-regression-review-checklist.md`（SPVR-01～05）与 `scene-scenario-page-visual-regression-review-checklist.md`（SPVR-06～10）（DOCS-043 / G92）。
30. 场景域独立截图抽检见 `scenario-domain-independent-screenshot-review-checklist.md`（SDIS-01～05）与 `scene-scenario-domain-independent-screenshot-review-checklist.md`（SDIS-06～10）（DOCS-044 / G93）。
31. 场景域 light/dark 独立截图抽检见 `scenario-domain-light-dark-screenshot-review-checklist.md`（SDLD-01～05）与 `scene-scenario-domain-light-dark-screenshot-review-checklist.md`（SDLD-06～10）（DOCS-045 / G94）。
32. 场景域 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-viewport-light-dark-screenshot-review-checklist.md`（SDTM-01～05）与 `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md`（SDTM-06～10）（DOCS-046 / G95）。
33. 场景域交互态打开态 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDIO-01～05）与 `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDIO-06～10）（DOCS-047 / G96）。
34. 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDPC-01～05）与 `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDPC-06～10）（DOCS-048 / G97）。
35. 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDTC-01～05）与 `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDTC-06～10）（DOCS-049 / G98）。
36. 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md`（SDHO-01～05）与 `scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md`（SDHO-06～10）（DOCS-050 / G99）。
37. 场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md`（SDFK-01～05）与 `scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md`（SDFK-06～10）（DOCS-051 / G100）。
38. 场景域 disabled/loading tablet/mobile light/dark 独立截图抽检见 `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md`（SDDL-01～05）与 `scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md`（SDDL-06～10）（DOCS-052 / G101）。
39. 场景域 empty/error tablet/mobile light/dark 独立截图抽检见 `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md`（SDEE-01～05）与 `scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md`（SDEE-06～10）（DOCS-053 / G102）。
40. 场景域 partial/retry tablet/mobile light/dark 独立截图抽检见 `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md`（SDPR-01～05）与 `scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md`（SDPR-06～10）（DOCS-054 / G103）。
41. 场景域 refetch/pending tablet/mobile light/dark 独立截图抽检见 `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md`（SDRP-01～05）与 `scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md`（SDRP-06～10）（DOCS-055 / G104）。
42. 场景域 stale/optimistic tablet/mobile light/dark 独立截图抽检见 `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md`（SDSO-01～05）与 `scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md`（SDSO-06～10）（DOCS-056 / G105）。
44. 场景域 conflict/merge tablet/mobile light/dark 独立截图抽检见 `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md`（SDCM-01～05）与 `scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md`（SDCM-06～10）（DOCS-058 / G107）。
45. 场景域 offline/sync conflict tablet/mobile light/dark 独立截图抽检见 `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md`（SDOSC-01～05）与 `scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md`（SDOSC-06～10）（DOCS-059 / G108）。
49. 场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md`（SDSRB-01～05）与 `scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md`（SDSRB-06～10）（DOCS-063 / G112）。
50. 场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md`（SDLPS-01～05）与 `scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md`（SDLPS-06～10）（DOCS-064 / G113）。
53. 场景域推送通道背压/队列积压 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md`（SDPCBQ-01～05）与 `scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md`（SDPCBQ-06～10）（DOCS-067 / G116）。
54. 场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md`（SDPCRDL-01～05）与 `scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md`（SDPCRDL-06～10）（DOCS-068 / G117）。
55. 场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md`（SDPCSCIR-01～05）与 `scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md`（SDPCSCIR-06～10）（DOCS-069 / G118）。
58. 场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md`（SDPCAT-01～05）与 `scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md`（SDPCAT-06～10）（DOCS-072 / G121）。
61. 场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md`（SDPCLF-01～05）与 `scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md`（SDPCLF-06～10）（DOCS-075 / G124）。
62. 场景域推送通道后续退役 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md`（SDPCRET-01～05）与 `scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md`（SDPCRET-06～10）（DOCS-076 / G125）。
63. 场景域推送通道后续清理 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md`（SDPCCLN-01～05）与 `scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md`（SDPCCLN-06～10）（DOCS-078 / G127）。
64. 场景域推送通道后续销毁 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md`（SDPCDEST-01～05）与 `scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md`（SDPCDEST-06～10）（DOCS-077 / G126）。
60. 场景域推送通道后续归档 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md`（SDPCARCH-01～05）与 `scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md`（SDPCARCH-06～10）（DOCS-074 / G123）。
59. 场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md`（SDPCCT-01～05）与 `scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md`（SDPCCT-06～10）（DOCS-073 / G122）。
57. 场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md`（SDPCCR-01～05）与 `scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md`（SDPCCR-06～10）（DOCS-071 / G120）。
56. 场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md`（SDPCAR-01～05）与 `scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md`（SDPCAR-06～10）（DOCS-070 / G119）。
52. 场景域推送通道熔断/限流 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md`（SDPCBRL-01～05）与 `scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md`（SDPCBRL-06～10）（DOCS-066 / G115）。
51. 场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDPCDR-01～05）与 `scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDPCDR-06～10）（DOCS-065 / G114）。
48. 场景域 WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md`（SDWRCB-01～05）与 `scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md`（SDWRCB-06～10）（DOCS-062 / G111）。
47. 场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图抽检见 `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md`（SDRHT-01～05）与 `scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md`（SDRHT-06～10）（DOCS-061 / G110）。
46. 场景域 network partition/recovery tablet/mobile light/dark 独立截图抽检见 `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDNPR-01～05）与 `scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDNPR-06～10）（DOCS-060 / G109）。
43. 场景域 mutation pending/rollback tablet/mobile light/dark 独立截图抽检见 `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md`（SDMR-01～05）与 `scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md`（SDMR-06～10）（DOCS-057 / G106）。

## 预防性迁移场景

尚未发生但常见的契约风险（ThemeToggle 导出名、SearchCommand 无 router、Kanban 自建 DnD 等）见 `migration-scenarios.md`。**一站式路由**见 `migration-playbook.md`（MS-01～13 → MN / override / SOR）。**首次接入**见 `adoption-onboarding-checklist.md`（ADOPT-01～05）。**SSR/微前端接入**见 `ssr-microfrontend-adoption-checklist.md`（SSR-01～05 / MFE-01～05）。**可访问性评审**见 `accessibility-review-checklist.md`（A11Y-01～05）与 `scene-accessibility-review-checklist.md`（A11Y-06～10）。**响应式评审**见 `responsive-review-checklist.md`（RESP-01～05）与 `scene-responsive-review-checklist.md`（RESP-06～10）。**异步状态评审**见 `async-state-review-checklist.md`（ASYNC-01～05）与 `scene-async-state-review-checklist.md`（ASYNC-06～10）。**交互与动效评审**见 `interaction-motion-review-checklist.md`（INTER-01～05）与 `scene-interaction-review-checklist.md`（INTER-06～10）。**中文示例文案评审**见 `chinese-copy-review-checklist.md`（COPY-01～05）与 `scene-chinese-copy-review-checklist.md`（COPY-06～10）。**视觉 Token 与密度评审**见 `visual-token-review-checklist.md`（VIS-01～05）与 `scene-visual-token-review-checklist.md`（VIS-06～10）。**表单校验与逻辑完备评审**见 `form-validation-logic-review-checklist.md`（LOGIC-01～05）。**类型完整与 API 契约评审**见 `type-api-contract-review-checklist.md`（TYPE-01～05）与 `scene-type-api-contract-review-checklist.md`（TYPE-06～10）。**生成一致性评审**见 `generation-consistency-review-checklist.md`（GEN-01～05）与 `scene-generation-consistency-review-checklist.md`（GEN-06～10）。**组件覆盖率评审**见 `component-coverage-review-checklist.md`（COV-01～05）与 `scene-component-coverage-review-checklist.md`（COV-06～10）。**模式覆盖评审**见 `pattern-coverage-review-checklist.md`（PAT-01～05）与 `scene-pattern-coverage-review-checklist.md`（PAT-06～10）。**约束遵守评审**见 `constraint-compliance-review-checklist.md`（CON-01～05）与 `scene-constraint-compliance-review-checklist.md`（CON-06～10）。**产品逻辑完备评审**见 `logic-completeness-review-checklist.md`（LOGIC-06～10）与 `scene-logic-completeness-review-checklist.md`（LOGIC-06～10 场景级）。**业务部署冒烟**见 `business-validation-checklist.md`（MS-09～13）。**UI 漂移评审**见 `ui-drift-review-checklist.md`（REV-01～05）与 `scene-ui-drift-review-checklist.md`（REV-06～10）。已填写的 migration note 演练见 `migration-notes/`（MN-01～03）。真实破坏性变更发生时，再复制 `migration-note-template.md` 填写正式记录。

## Migration Note 演练（COMPAT-003）

| ID | 场景 | 状态 | Wrapper |
|---|---|---|---|
| MN-01 | MS-01 ThemeToggle alias | active | `templates/ui/deprecated/theme-toggle-alias.tsx` |
| MN-02 | MS-02 SearchCommand 无 router | active | `templates/ui/deprecated/search-command-static.tsx` |
| MN-03 | MS-03 Kanban 自建板 | active | `templates/ui/deprecated/kanban-legacy-shell.tsx` |

验证：`audit_migration_drills.py` + `audit_compat_contracts.py`。

## Deprecated Wrapper 模式

未来删除或重命名导出时，在同一文件或 `templates/ui/deprecated/` 提供 wrapper：

```tsx
/** @deprecated 见 migration-note-<id>.md，兼容至 G<n+1> */
export function LegacyName(props: LegacyProps) {
  return <CurrentName {...mapLegacyProps(props)} />;
}
```

同轮规则：先 additive 新 API → 标记旧 API deprecated → 下一演化周期再删除。

## 评分门控

若破坏性变更没有 migration note、deprecated wrapper 或兼容说明：

- `约束遵守` 最高 85。
- `扩展性与灵活性` 最高 85。
- `向后兼容性` 最高 85。
- 若业务主路径可能受影响且无回归截图，总分最高 89。
