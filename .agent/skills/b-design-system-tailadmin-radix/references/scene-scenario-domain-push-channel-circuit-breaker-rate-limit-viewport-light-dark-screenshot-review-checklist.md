# 场景 Scenario Domain Push Channel Circuit Breaker Rate Limit Viewport Light/Dark Screenshot 评审清单

> DOCS-066 / G115 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道熔断/限流解除独立截图抽检**，确保各域 section 在推送通道熔断态与限流解除态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md`（SDPCBRL-01～05）、`scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDPCDR-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道熔断/限流解除 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCBRL 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道熔断/限流解除 tablet/mobile light/dark 独立截图 | SDPCBRL-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道熔断/限流解除 tablet/mobile light/dark 独立截图 | SDPCBRL-07 + `scenario-devops` |
| Gateway 端点推送通道熔断/限流解除 tablet/mobile light/dark 独立截图 | SDPCBRL-08 + `scenario-gateway` |
| Governance 审计行推送通道熔断/限流解除 tablet/mobile light/dark 独立截图 | SDPCBRL-09 + `scenario-governance` |
| 场景域推送通道熔断/限流解除 tablet/mobile light/dark 独立截图束缺门禁 | SDPCBRL-10 + `verifyScenarioDomainPushChannelDegradationRecoveryViewportLightDarkScreenshots` + `verifyScenarioDomainPushChannelCircuitBreakerRateLimitViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md` SDPCBRL-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-breaker-open,rate-limit-released}.png` 共 40 张推送通道熔断/限流解除独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道熔断/限流解除独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道熔断/限流解除 tablet/mobile light/dark 独立截图（G115）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道熔断/限流解除 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCBRL-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCBRL-06 — BI Analytics 指标推送通道熔断/限流解除 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-channel-breaker-open.png`、`scenario-bi-domain-mobile-dark-rate-limit-released.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-breaker-open | `scenario-bi-domain-tablet-channel-breaker-open.png` + `scenario-bi-domain-tablet-dark-channel-breaker-open.png` channel-breaker-open framing 正常 | SDPCBRL-06 · RESP-06 |
| 2 | mobile light/dark rate-limit-released | `scenario-bi-domain-mobile-rate-limit-released.png` + `scenario-bi-domain-mobile-dark-rate-limit-released.png` rate-limit-released framing 正常 | SDPCBRL-06 · RESP-07 |
| 3 | 指标推送通道熔断/限流解除 | 熔断 banner「推送通道已熔断（限流保护模式）」+ 熔断摘要 + 限流解除 banner「限流已解除，指标推送通道稳定，可继续接收实时变更事件」tablet/mobile light/dark 首屏可见 | SDPCBRL-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 channel-breaker-open banner 与 rate-limit-released banner 层级可辨认 | SDPCBRL-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 channel-breaker-open/rate-limit-released 截图全过 | SDPCBRL-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 channel-breaker-open 面板 → 点击「触发指标限流解除」→ 对照 tablet/mobile light/dark 八张推送通道熔断/限流解除截图。

## SDPCBRL-07 — DevOps 阶段推送通道熔断/限流解除 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-channel-breaker-open.png`、`scenario-devops-domain-mobile-dark-rate-limit-released.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-breaker-open | `scenario-devops-domain-tablet-channel-breaker-open.png` + `scenario-devops-domain-tablet-dark-channel-breaker-open.png` channel-breaker-open framing 正常 | SDPCBRL-07 · RESP-06 |
| 2 | mobile light/dark rate-limit-released | `scenario-devops-domain-mobile-rate-limit-released.png` + `scenario-devops-domain-mobile-dark-rate-limit-released.png` rate-limit-released framing 正常 | SDPCBRL-07 · RESP-07 |
| 3 | 阶段推送通道熔断/限流解除 | 流水线熔断 banner + 限流解除摘要 tablet/mobile light/dark 首屏可见 | SDPCBRL-07 · PAT-07 |
| 4 | rate-limit-released 态 | mobile dark 下 rate-limit-released 文案与「查看限流解除详情」按钮可辨认 | SDPCBRL-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 channel-breaker-open/rate-limit-released 截图全过 | SDPCBRL-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 channel-breaker-open 面板 → 点击「触发阶段限流解除」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBRL-08 — Gateway 端点推送通道熔断/限流解除 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-channel-breaker-open.png`、`scenario-gateway-domain-mobile-dark-rate-limit-released.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-breaker-open | `scenario-gateway-domain-tablet-channel-breaker-open.png` + `scenario-gateway-domain-tablet-dark-channel-breaker-open.png` channel-breaker-open framing 正常 | SDPCBRL-08 · RESP-06 |
| 2 | mobile light/dark rate-limit-released | `scenario-gateway-domain-mobile-rate-limit-released.png` + `scenario-gateway-domain-mobile-dark-rate-limit-released.png` rate-limit-released framing 正常 | SDPCBRL-08 · RESP-07 |
| 3 | 端点推送通道熔断/限流解除 | 端点熔断 banner + 限流解除摘要 tablet/mobile light/dark 首屏可见 | SDPCBRL-08 · PAT-08 |
| 4 | channel-breaker-open 态 | mobile dark 下熔断进度与 banner 可辨认 | SDPCBRL-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 channel-breaker-open/rate-limit-released 截图全过 | SDPCBRL-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 channel-breaker-open 面板 → 点击「触发端点限流解除」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBRL-09 — Governance 审计行推送通道熔断/限流解除 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-channel-breaker-open.png`、`scenario-governance-domain-mobile-channel-breaker-open.png`、`scenario-governance-domain-mobile-dark-rate-limit-released.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-breaker-open | `scenario-governance-domain-tablet-channel-breaker-open.png` + `scenario-governance-domain-tablet-dark-channel-breaker-open.png` channel-breaker-open framing 正常 | SDPCBRL-09 · RESP-06 |
| 2 | mobile light/dark rate-limit-released | `scenario-governance-domain-mobile-rate-limit-released.png` + `scenario-governance-domain-mobile-dark-rate-limit-released.png` rate-limit-released framing 正常 | SDPCBRL-09 · RESP-07 |
| 3 | 审计推送通道熔断/限流解除 | 审计熔断 banner + 限流解除摘要 tablet/mobile light/dark 首屏可见 | SDPCBRL-09 · PAT-09 |
| 4 | rate-limit-released 文案 | mobile dark 下「限流已解除，合规事件推送稳定，可继续提交策略变更」文案可辨认 | SDPCBRL-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 channel-breaker-open/rate-limit-released 截图全过 | SDPCBRL-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 channel-breaker-open 面板 → 点击「触发审计限流解除」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBRL-10 — 场景域推送通道熔断/限流解除 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-breaker-open,rate-limit-released}.png` + `scenarioDomainPushChannelCircuitBreakerRateLimitViewportLightDarkScreenshotStates.pushChannelCircuitBreakerRateLimitStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × channel-breaker-open/rate-limit-released 全量 golden 存在 | SDPCBRL-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelCircuitBreakerRateLimitViewportLightDarkScreenshots` 通过 | SDPCBRL-10 · PREVIEW-* |
| 3 | channel-breaker-open 态 | 五域 `data-audit="scenario-domain-channel-breaker-open-overlay"` `data-state="channel-breaker-open"` 可见 | SDPCBRL-10 · LOGIC-* |
| 4 | rate-limit-released 态 | 五域点击限流解除 trigger 后 `role="status"` + `data-state="rate-limit-released"` 可见 | SDPCBRL-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelCircuitBreakerRateLimitStateMatrixComplete = true` | SDPCBRL-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道熔断/限流解除截图与门禁 JSON 输出。
