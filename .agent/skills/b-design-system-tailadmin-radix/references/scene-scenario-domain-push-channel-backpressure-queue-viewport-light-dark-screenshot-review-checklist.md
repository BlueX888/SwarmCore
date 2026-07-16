# 场景 Scenario Domain Push Channel Backpressure Queue Viewport Light/Dark Screenshot 评审清单

> DOCS-067 / G116 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道背压/队列排空独立截图抽检**，确保各域 section 在推送通道背压激活态与队列排空态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md`（SDPCBQ-01～05）、`scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md`（SDPCBRL-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道背压/队列排空 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCBQ 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道背压/队列排空 tablet/mobile light/dark 独立截图 | SDPCBQ-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道背压/队列排空 tablet/mobile light/dark 独立截图 | SDPCBQ-07 + `scenario-devops` |
| Gateway 端点推送通道背压/队列排空 tablet/mobile light/dark 独立截图 | SDPCBQ-08 + `scenario-gateway` |
| Governance 审计行推送通道背压/队列排空 tablet/mobile light/dark 独立截图 | SDPCBQ-09 + `scenario-governance` |
| 场景域推送通道背压/队列排空 tablet/mobile light/dark 独立截图束缺门禁 | SDPCBQ-10 + `verifyScenarioDomainPushChannelCircuitBreakerRateLimitViewportLightDarkScreenshots` + `verifyScenarioDomainPushChannelBackpressureQueueViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md` SDPCBQ-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{backpressure-active,queue-drained}.png` 共 40 张推送通道背压/队列排空独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道背压/队列排空独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道背压/队列排空 tablet/mobile light/dark 独立截图（G116）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道背压/队列排空 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCBQ-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCBQ-06 — BI Analytics 指标推送通道背压/队列排空 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-backpressure-active.png`、`scenario-bi-domain-mobile-dark-queue-drained.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark backpressure-active | `scenario-bi-domain-tablet-backpressure-active.png` + `scenario-bi-domain-tablet-dark-backpressure-active.png` backpressure-active framing 正常 | SDPCBQ-06 · RESP-06 |
| 2 | mobile light/dark queue-drained | `scenario-bi-domain-mobile-queue-drained.png` + `scenario-bi-domain-mobile-dark-queue-drained.png` queue-drained framing 正常 | SDPCBQ-06 · RESP-07 |
| 3 | 指标推送通道背压/队列排空 | 背压 banner「推送通道背压激活（队列积压模式）」+ 积压队列摘要 + 队列排空 banner「队列已排空，指标推送通道背压解除，可继续接收实时变更事件」tablet/mobile light/dark 首屏可见 | SDPCBQ-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 backpressure-active banner 与 queue-drained banner 层级可辨认 | SDPCBQ-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 backpressure-active/queue-drained 截图全过 | SDPCBQ-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 backpressure-active 面板 → 点击「触发指标队列排空」→ 对照 tablet/mobile light/dark 八张推送通道背压/队列排空截图。

## SDPCBQ-07 — DevOps 阶段推送通道背压/队列排空 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-backpressure-active.png`、`scenario-devops-domain-mobile-dark-queue-drained.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark backpressure-active | `scenario-devops-domain-tablet-backpressure-active.png` + `scenario-devops-domain-tablet-dark-backpressure-active.png` backpressure-active framing 正常 | SDPCBQ-07 · RESP-06 |
| 2 | mobile light/dark queue-drained | `scenario-devops-domain-mobile-queue-drained.png` + `scenario-devops-domain-mobile-dark-queue-drained.png` queue-drained framing 正常 | SDPCBQ-07 · RESP-07 |
| 3 | 阶段推送通道背压/队列排空 | 流水线背压 banner + 队列排空摘要 tablet/mobile light/dark 首屏可见 | SDPCBQ-07 · PAT-07 |
| 4 | queue-drained 态 | mobile dark 下 queue-drained 文案与「查看队列排空详情」按钮可辨认 | SDPCBQ-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 backpressure-active/queue-drained 截图全过 | SDPCBQ-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 backpressure-active 面板 → 点击「触发阶段队列排空」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBQ-08 — Gateway 端点推送通道背压/队列排空 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-backpressure-active.png`、`scenario-gateway-domain-mobile-dark-queue-drained.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark backpressure-active | `scenario-gateway-domain-tablet-backpressure-active.png` + `scenario-gateway-domain-tablet-dark-backpressure-active.png` backpressure-active framing 正常 | SDPCBQ-08 · RESP-06 |
| 2 | mobile light/dark queue-drained | `scenario-gateway-domain-mobile-queue-drained.png` + `scenario-gateway-domain-mobile-dark-queue-drained.png` queue-drained framing 正常 | SDPCBQ-08 · RESP-07 |
| 3 | 端点推送通道背压/队列排空 | 端点背压 banner + 队列排空摘要 tablet/mobile light/dark 首屏可见 | SDPCBQ-08 · PAT-08 |
| 4 | backpressure-active 态 | mobile dark 下积压进度与背压 banner 可辨认 | SDPCBQ-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 backpressure-active/queue-drained 截图全过 | SDPCBQ-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 backpressure-active 面板 → 点击「触发端点队列排空」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBQ-09 — Governance 审计行推送通道背压/队列排空 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-backpressure-active.png`、`scenario-governance-domain-mobile-backpressure-active.png`、`scenario-governance-domain-mobile-dark-queue-drained.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark backpressure-active | `scenario-governance-domain-tablet-backpressure-active.png` + `scenario-governance-domain-tablet-dark-backpressure-active.png` backpressure-active framing 正常 | SDPCBQ-09 · RESP-06 |
| 2 | mobile light/dark queue-drained | `scenario-governance-domain-mobile-queue-drained.png` + `scenario-governance-domain-mobile-dark-queue-drained.png` queue-drained framing 正常 | SDPCBQ-09 · RESP-07 |
| 3 | 审计推送通道背压/队列排空 | 审计背压 banner + 队列排空摘要 tablet/mobile light/dark 首屏可见 | SDPCBQ-09 · PAT-09 |
| 4 | queue-drained 文案 | mobile dark 下「队列已排空，合规事件推送背压解除，可继续提交策略变更」文案可辨认 | SDPCBQ-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 backpressure-active/queue-drained 截图全过 | SDPCBQ-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 backpressure-active 面板 → 点击「触发审计队列排空」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBQ-10 — 场景域推送通道背压/队列排空 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{backpressure-active,queue-drained}.png` + `scenarioDomainPushChannelBackpressureQueueViewportLightDarkScreenshotStates.pushChannelBackpressureQueueStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × backpressure-active/queue-drained 全量 golden 存在 | SDPCBQ-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelBackpressureQueueViewportLightDarkScreenshots` 通过 | SDPCBQ-10 · PREVIEW-* |
| 3 | backpressure-active 态 | 五域 `data-audit="scenario-domain-backpressure-active-overlay"` `data-state="backpressure-active"` 可见 | SDPCBQ-10 · LOGIC-* |
| 4 | queue-drained 态 | 五域点击队列排空 trigger 后 `role="status"` + `data-state="queue-drained"` 可见 | SDPCBQ-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelBackpressureQueueStateMatrixComplete = true` | SDPCBQ-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道背压/队列排空截图与门禁 JSON 输出。
