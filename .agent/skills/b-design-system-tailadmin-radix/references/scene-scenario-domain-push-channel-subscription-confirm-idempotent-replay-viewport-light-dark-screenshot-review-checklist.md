# 场景 Scenario Domain Push Channel Subscription Confirm Idempotent Replay Viewport Light/Dark Screenshot 评审清单

> DOCS-069 / G118 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道订阅确认/幂等重放独立截图抽检**，确保各域 section 在推送通道订阅确认态与幂等重放完成态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md`（SDPCSCIR-01～05）、`scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md`（SDPCRDL-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCSCIR 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图 | SDPCSCIR-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图 | SDPCSCIR-07 + `scenario-devops` |
| Gateway 端点推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图 | SDPCSCIR-08 + `scenario-gateway` |
| Governance 审计行推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图 | SDPCSCIR-09 + `scenario-governance` |
| 场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图束缺门禁 | SDPCSCIR-10 + `verifyScenarioDomainPushChannelRetryDeadLetterViewportLightDarkScreenshots` + `verifyScenarioDomainPushChannelSubscriptionConfirmIdempotentReplayViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md` SDPCSCIR-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{subscription-confirm,idempotent-replay}.png` 共 40 张推送通道订阅确认/幂等重放独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道订阅确认/幂等重放独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图（G118）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCSCIR-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCSCIR-06 — BI Analytics 指标推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-subscription-confirm.png`、`scenario-bi-domain-mobile-dark-idempotent-replay.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark subscription-confirm | `scenario-bi-domain-tablet-subscription-confirm.png` + `scenario-bi-domain-tablet-dark-subscription-confirm.png` subscription-confirm framing 正常 | SDPCSCIR-06 · RESP-06 |
| 2 | mobile light/dark idempotent-replay | `scenario-bi-domain-mobile-idempotent-replay.png` + `scenario-bi-domain-mobile-dark-idempotent-replay.png` idempotent-replay framing 正常 | SDPCSCIR-06 · RESP-07 |
| 3 | 指标推送通道订阅确认/幂等重放 | 订阅确认 banner「推送通道订阅确认中（幂等令牌校验）」+ 幂等令牌摘要 + 幂等重放完成 banner「幂等重放已完成，指标推送通道订阅恢复，可继续接收实时变更事件」tablet/mobile light/dark 首屏可见 | SDPCSCIR-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 subscription-confirm banner 与 idempotent-replay banner 层级可辨认 | SDPCSCIR-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 subscription-confirm/idempotent-replay 截图全过 | SDPCSCIR-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 subscription-confirm 面板 → 点击「触发指标幂等重放」→ 对照 tablet/mobile light/dark 八张推送通道订阅确认/幂等重放截图。

## SDPCSCIR-07 — DevOps 阶段推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-subscription-confirm.png`、`scenario-devops-domain-mobile-dark-idempotent-replay.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark subscription-confirm | `scenario-devops-domain-tablet-subscription-confirm.png` + `scenario-devops-domain-tablet-dark-subscription-confirm.png` subscription-confirm framing 正常 | SDPCSCIR-07 · RESP-06 |
| 2 | mobile light/dark idempotent-replay | `scenario-devops-domain-mobile-idempotent-replay.png` + `scenario-devops-domain-mobile-dark-idempotent-replay.png` idempotent-replay framing 正常 | SDPCSCIR-07 · RESP-07 |
| 3 | 阶段推送通道订阅确认/幂等重放 | 流水线订阅确认 banner + 幂等重放完成摘要 tablet/mobile light/dark 首屏可见 | SDPCSCIR-07 · PAT-07 |
| 4 | idempotent-replay 态 | mobile dark 下 idempotent-replay 文案与「查看幂等重放详情」按钮可辨认 | SDPCSCIR-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 subscription-confirm/idempotent-replay 截图全过 | SDPCSCIR-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 subscription-confirm 面板 → 点击「触发阶段幂等重放」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCSCIR-08 — Gateway 端点推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-subscription-confirm.png`、`scenario-gateway-domain-mobile-dark-idempotent-replay.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark subscription-confirm | `scenario-gateway-domain-tablet-subscription-confirm.png` + `scenario-gateway-domain-tablet-dark-subscription-confirm.png` subscription-confirm framing 正常 | SDPCSCIR-08 · RESP-06 |
| 2 | mobile light/dark idempotent-replay | `scenario-gateway-domain-mobile-idempotent-replay.png` + `scenario-gateway-domain-mobile-dark-idempotent-replay.png` idempotent-replay framing 正常 | SDPCSCIR-08 · RESP-07 |
| 3 | 端点推送通道订阅确认/幂等重放 | 端点订阅确认 banner + 幂等重放完成摘要 tablet/mobile light/dark 首屏可见 | SDPCSCIR-08 · PAT-08 |
| 4 | subscription-confirm 态 | mobile dark 下幂等令牌摘要与订阅确认 banner 可辨认 | SDPCSCIR-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 subscription-confirm/idempotent-replay 截图全过 | SDPCSCIR-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 subscription-confirm 面板 → 点击「触发端点幂等重放」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCSCIR-09 — Governance 审计行推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-subscription-confirm.png`、`scenario-governance-domain-mobile-subscription-confirm.png`、`scenario-governance-domain-mobile-dark-idempotent-replay.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark subscription-confirm | `scenario-governance-domain-tablet-subscription-confirm.png` + `scenario-governance-domain-tablet-dark-subscription-confirm.png` subscription-confirm framing 正常 | SDPCSCIR-09 · RESP-06 |
| 2 | mobile light/dark idempotent-replay | `scenario-governance-domain-mobile-idempotent-replay.png` + `scenario-governance-domain-mobile-dark-idempotent-replay.png` idempotent-replay framing 正常 | SDPCSCIR-09 · RESP-07 |
| 3 | 审计推送通道订阅确认/幂等重放 | 审计订阅确认 banner + 幂等重放完成摘要 tablet/mobile light/dark 首屏可见 | SDPCSCIR-09 · PAT-09 |
| 4 | idempotent-replay 文案 | mobile dark 下「幂等重放已完成，合规事件推送订阅恢复，可继续提交策略变更」文案可辨认 | SDPCSCIR-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 subscription-confirm/idempotent-replay 截图全过 | SDPCSCIR-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 subscription-confirm 面板 → 点击「触发审计幂等重放」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCSCIR-10 — 场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{subscription-confirm,idempotent-replay}.png` + `scenarioDomainPushChannelSubscriptionConfirmIdempotentReplayViewportLightDarkScreenshotStates.pushChannelSubscriptionConfirmIdempotentReplayStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × subscription-confirm/idempotent-replay 全量 golden 存在 | SDPCSCIR-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelSubscriptionConfirmIdempotentReplayViewportLightDarkScreenshots` 通过 | SDPCSCIR-10 · PREVIEW-* |
| 3 | subscription-confirm 态 | 五域 `data-audit="scenario-domain-subscription-confirm-overlay"` `data-state="subscription-confirm"` 可见 | SDPCSCIR-10 · LOGIC-* |
| 4 | idempotent-replay 态 | 五域点击幂等重放 trigger 后 `role="status"` + `data-state="idempotent-replay"` 可见 | SDPCSCIR-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelSubscriptionConfirmIdempotentReplayStateMatrixComplete = true` | SDPCSCIR-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道订阅确认/幂等重放截图与门禁 JSON 输出。
