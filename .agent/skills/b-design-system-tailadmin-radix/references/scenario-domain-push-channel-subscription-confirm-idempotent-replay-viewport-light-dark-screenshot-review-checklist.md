# Scenario Domain Push Channel Subscription Confirm Idempotent Replay Viewport Light/Dark Screenshot 评审清单

> DOCS-069 / G118 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道订阅确认/幂等重放独立截图视觉回归抽检**，确保每个场景 section 在推送通道订阅确认态、幂等重放完成态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md`（SDPCRDL-01～05）、`scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md`（SDPCSCIR-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCSCIR 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道订阅确认/幂等重放 tablet/mobile light/dark golden 对照 | SDPCSCIR-01 + `scenario-bi-domain-tablet-subscription-confirm.png` + `scenario-bi-domain-mobile-dark-idempotent-replay.png` |
| DevOps 场景阶段推送通道订阅确认/幂等重放 tablet/mobile light/dark golden 对照 | SDPCSCIR-02 + `scenario-devops-domain-tablet-subscription-confirm.png` + `scenario-devops-domain-mobile-dark-idempotent-replay.png` |
| Gateway 场景端点推送通道订阅确认/幂等重放 tablet/mobile light/dark golden 对照 | SDPCSCIR-03 + `scenario-gateway-domain-tablet-subscription-confirm.png` + `scenario-gateway-domain-mobile-dark-idempotent-replay.png` |
| Governance 场景审计行推送通道订阅确认/幂等重放 tablet/mobile light/dark golden 对照 | SDPCSCIR-04 + `scenario-governance-domain-tablet-subscription-confirm.png` + `scenario-governance-domain-mobile-dark-idempotent-replay.png` |
| PaaS 场景容量推送通道订阅确认/幂等重放 tablet/mobile light/dark golden 对照 | SDPCSCIR-05 + `scenario-paas-domain-tablet-subscription-confirm.png` + `scenario-paas-domain-mobile-dark-idempotent-replay.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md` SDPCRDL-01～05（推送通道重试/死信队列排空独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{subscription-confirm,idempotent-replay}.png` 四视口双主题推送通道订阅确认/幂等重放独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 subscription-confirm 与一张 idempotent-replay 独立截图；subscription-confirm 必须出现订阅确认 banner「推送通道订阅确认中（幂等令牌校验）」与幂等令牌摘要，idempotent-replay 必须出现幂等重放完成 banner 与「查看幂等重放详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道订阅确认/幂等重放截图出现文案裁切、订阅确认 banner 对比度不足、idempotent-replay banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图（G118）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图抽检行。

## SDPCSCIR-01 — BI 场景指标推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-subscription-confirm.png`、`scenario-bi-domain-tablet-dark-subscription-confirm.png`、`scenario-bi-domain-mobile-subscription-confirm.png`、`scenario-bi-domain-mobile-dark-subscription-confirm.png`、`scenario-bi-domain-tablet-idempotent-replay.png`、`scenario-bi-domain-tablet-dark-idempotent-replay.png`、`scenario-bi-domain-mobile-idempotent-replay.png`、`scenario-bi-domain-mobile-dark-idempotent-replay.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light subscription-confirm 截图 | `scenario-bi-domain-tablet-subscription-confirm.png` 存在且 subscription-confirm framing 正常 | SDPCSCIR-01 · RESP-06 |
| 2 | tablet dark subscription-confirm 截图 | `scenario-bi-domain-tablet-dark-subscription-confirm.png` 存在且订阅确认 banner 可读 | SDPCSCIR-01 · VIS-05 |
| 3 | mobile light idempotent-replay 截图 | `scenario-bi-domain-mobile-idempotent-replay.png` idempotent-replay banner 首屏可见 | SDPCSCIR-01 · RESP-07 |
| 4 | mobile dark idempotent-replay 截图 | `scenario-bi-domain-mobile-dark-idempotent-replay.png` idempotent-replay 对比度可辨认 | SDPCSCIR-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelSubscriptionConfirmIdempotentReplayViewportLightDarkScreenshots` biDomain 全过 | SDPCSCIR-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 subscription-confirm 面板 → 点击「触发指标幂等重放」→ 对照 tablet/mobile light/dark 八张 subscription-confirm/idempotent-replay 截图。

## SDPCSCIR-02 — DevOps 场景阶段推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-subscription-confirm.png`、`scenario-devops-domain-tablet-dark-subscription-confirm.png`、`scenario-devops-domain-mobile-subscription-confirm.png`、`scenario-devops-domain-mobile-dark-subscription-confirm.png`、`scenario-devops-domain-tablet-idempotent-replay.png`、`scenario-devops-domain-tablet-dark-idempotent-replay.png`、`scenario-devops-domain-mobile-idempotent-replay.png`、`scenario-devops-domain-mobile-dark-idempotent-replay.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light subscription-confirm 截图 | `scenario-devops-domain-tablet-subscription-confirm.png` 存在且 subscription-confirm framing 正常 | SDPCSCIR-02 · RESP-06 |
| 2 | tablet dark subscription-confirm 截图 | `scenario-devops-domain-tablet-dark-subscription-confirm.png` 存在且幂等令牌摘要可读 | SDPCSCIR-02 · VIS-05 |
| 3 | mobile light idempotent-replay 截图 | `scenario-devops-domain-mobile-idempotent-replay.png` 流水线 idempotent-replay 首屏可见 | SDPCSCIR-02 · RESP-07 |
| 4 | mobile dark idempotent-replay 截图 | `scenario-devops-domain-mobile-dark-idempotent-replay.png` idempotent-replay 对比度可辨认 | SDPCSCIR-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道订阅确认/幂等重放 tablet/mobile light/dark 可见 | SDPCSCIR-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 subscription-confirm 面板 → 点击「触发阶段幂等重放」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCSCIR-03 — Gateway 场景端点推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-subscription-confirm.png`、`scenario-gateway-domain-tablet-dark-subscription-confirm.png`、`scenario-gateway-domain-mobile-subscription-confirm.png`、`scenario-gateway-domain-mobile-dark-subscription-confirm.png`、`scenario-gateway-domain-tablet-idempotent-replay.png`、`scenario-gateway-domain-tablet-dark-idempotent-replay.png`、`scenario-gateway-domain-mobile-idempotent-replay.png`、`scenario-gateway-domain-mobile-dark-idempotent-replay.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light subscription-confirm 截图 | `scenario-gateway-domain-tablet-subscription-confirm.png` 存在且 subscription-confirm framing 正常 | SDPCSCIR-03 · RESP-06 |
| 2 | tablet dark subscription-confirm 截图 | `scenario-gateway-domain-tablet-dark-subscription-confirm.png` 存在且幂等令牌摘要可读 | SDPCSCIR-03 · VIS-05 |
| 3 | mobile light idempotent-replay 截图 | `scenario-gateway-domain-mobile-idempotent-replay.png` 端点 idempotent-replay 首屏可见 | SDPCSCIR-03 · RESP-07 |
| 4 | mobile dark idempotent-replay 截图 | `scenario-gateway-domain-mobile-dark-idempotent-replay.png` idempotent-replay 层级不丢失 | SDPCSCIR-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道订阅确认/幂等重放 tablet/mobile light/dark 可见 | SDPCSCIR-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 subscription-confirm 面板 → 点击「触发端点幂等重放」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCSCIR-04 — Governance 场景审计行推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-subscription-confirm.png`、`scenario-governance-domain-tablet-dark-subscription-confirm.png`、`scenario-governance-domain-mobile-subscription-confirm.png`、`scenario-governance-domain-mobile-dark-subscription-confirm.png`、`scenario-governance-domain-tablet-idempotent-replay.png`、`scenario-governance-domain-tablet-dark-idempotent-replay.png`、`scenario-governance-domain-mobile-idempotent-replay.png`、`scenario-governance-domain-mobile-dark-idempotent-replay.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light subscription-confirm 截图 | `scenario-governance-domain-tablet-subscription-confirm.png` 存在且 subscription-confirm framing 正常 | SDPCSCIR-04 · RESP-06 |
| 2 | tablet dark subscription-confirm 截图 | `scenario-governance-domain-tablet-dark-subscription-confirm.png` 存在且幂等令牌摘要可读 | SDPCSCIR-04 · VIS-05 |
| 3 | mobile light idempotent-replay 截图 | `scenario-governance-domain-mobile-idempotent-replay.png` 审计 idempotent-replay 首屏可见 | SDPCSCIR-04 · RESP-07 |
| 4 | mobile dark idempotent-replay 截图 | `scenario-governance-domain-mobile-dark-idempotent-replay.png` idempotent-replay 密度一致 | SDPCSCIR-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道订阅确认/幂等重放 tablet/mobile light/dark 可见 | SDPCSCIR-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 subscription-confirm 面板 → 点击「触发审计幂等重放」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCSCIR-05 — PaaS 场景容量推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-subscription-confirm.png`、`scenario-paas-domain-tablet-dark-subscription-confirm.png`、`scenario-paas-domain-mobile-subscription-confirm.png`、`scenario-paas-domain-mobile-dark-subscription-confirm.png`、`scenario-paas-domain-tablet-idempotent-replay.png`、`scenario-paas-domain-tablet-dark-idempotent-replay.png`、`scenario-paas-domain-mobile-idempotent-replay.png`、`scenario-paas-domain-mobile-dark-idempotent-replay.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light subscription-confirm 截图 | `scenario-paas-domain-tablet-subscription-confirm.png` 存在且 subscription-confirm framing 正常 | SDPCSCIR-05 · RESP-06 |
| 2 | tablet dark subscription-confirm 截图 | `scenario-paas-domain-tablet-dark-subscription-confirm.png` 存在且幂等令牌摘要可读 | SDPCSCIR-05 · VIS-05 |
| 3 | mobile light idempotent-replay 截图 | `scenario-paas-domain-mobile-idempotent-replay.png` 容量 idempotent-replay 首屏可见 | SDPCSCIR-05 · RESP-07 |
| 4 | mobile dark idempotent-replay 截图 | `scenario-paas-domain-mobile-dark-idempotent-replay.png` idempotent-replay 列表项可辨认 | SDPCSCIR-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道订阅确认/幂等重放 tablet/mobile light/dark 可见 | SDPCSCIR-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 subscription-confirm 面板 → 点击「触发容量幂等重放」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md` SDPCSCIR-06～10
- 推送通道重试/死信队列 前置：`scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md` SDPCRDL-01～05
- 选型表：`decision-matrix.md` G118 场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCSCIR-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelSubscriptionConfirmIdempotentReplayViewportLightDarkScreenshots`
