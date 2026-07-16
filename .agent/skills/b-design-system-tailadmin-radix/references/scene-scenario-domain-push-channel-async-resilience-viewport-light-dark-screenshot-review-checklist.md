# 场景 Scenario Domain Push Channel Async Resilience Viewport Light/Dark Screenshot 评审清单

> DOCS-070 / G119 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道后续异步韧性独立截图抽检**，确保各域 section 在推送通道异步韧性监测态与异步韧性恢复完成态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md`（SDPCAR-01～05）、`scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md`（SDPCSCIR-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCAR 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道后续异步韧性 tablet/mobile light/dark 独立截图 | SDPCAR-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道后续异步韧性 tablet/mobile light/dark 独立截图 | SDPCAR-07 + `scenario-devops` |
| Gateway 端点推送通道后续异步韧性 tablet/mobile light/dark 独立截图 | SDPCAR-08 + `scenario-gateway` |
| Governance 审计行推送通道后续异步韧性 tablet/mobile light/dark 独立截图 | SDPCAR-09 + `scenario-governance` |
| 场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图束缺门禁 | SDPCAR-10 + `verifyScenarioDomainPushChannelSubscriptionConfirmIdempotentReplayViewportLightDarkScreenshots` + `verifyScenarioDomainPushChannelAsyncResilienceViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md` SDPCAR-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{async-pending,async-recovered}.png` 共 40 张推送通道后续异步韧性独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道后续异步韧性独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图（G119）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCAR-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCAR-06 — BI Analytics 指标推送通道后续异步韧性 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-async-pending.png`、`scenario-bi-domain-mobile-dark-async-recovered.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark async-pending | `scenario-bi-domain-tablet-async-pending.png` + `scenario-bi-domain-tablet-dark-async-pending.png` async-pending framing 正常 | SDPCAR-06 · RESP-06 |
| 2 | mobile light/dark async-recovered | `scenario-bi-domain-mobile-async-recovered.png` + `scenario-bi-domain-mobile-dark-async-recovered.png` async-recovered framing 正常 | SDPCAR-06 · RESP-07 |
| 3 | 指标推送通道后续异步韧性 | 异步韧性监测 banner「推送通道异步韧性监测中（重试队列排队）」+ 重试队列摘要 + 异步韧性恢复完成 banner「异步韧性恢复已完成，指标推送通道订阅恢复，可继续接收实时变更事件」tablet/mobile light/dark 首屏可见 | SDPCAR-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 async-pending banner 与 async-recovered banner 层级可辨认 | SDPCAR-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 async-pending/async-recovered 截图全过 | SDPCAR-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 async-pending 面板 → 点击「触发指标异步韧性恢复」→ 对照 tablet/mobile light/dark 八张推送通道后续异步韧性截图。

## SDPCAR-07 — DevOps 阶段推送通道后续异步韧性 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-async-pending.png`、`scenario-devops-domain-mobile-dark-async-recovered.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark async-pending | `scenario-devops-domain-tablet-async-pending.png` + `scenario-devops-domain-tablet-dark-async-pending.png` async-pending framing 正常 | SDPCAR-07 · RESP-06 |
| 2 | mobile light/dark async-recovered | `scenario-devops-domain-mobile-async-recovered.png` + `scenario-devops-domain-mobile-dark-async-recovered.png` async-recovered framing 正常 | SDPCAR-07 · RESP-07 |
| 3 | 阶段推送通道后续异步韧性 | 流水线异步韧性监测 banner + 异步韧性恢复完成摘要 tablet/mobile light/dark 首屏可见 | SDPCAR-07 · PAT-07 |
| 4 | async-recovered 态 | mobile dark 下 async-recovered 文案与「查看异步韧性恢复详情」按钮可辨认 | SDPCAR-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 async-pending/async-recovered 截图全过 | SDPCAR-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 async-pending 面板 → 点击「触发阶段异步韧性恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCAR-08 — Gateway 端点推送通道后续异步韧性 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-async-pending.png`、`scenario-gateway-domain-mobile-dark-async-recovered.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark async-pending | `scenario-gateway-domain-tablet-async-pending.png` + `scenario-gateway-domain-tablet-dark-async-pending.png` async-pending framing 正常 | SDPCAR-08 · RESP-06 |
| 2 | mobile light/dark async-recovered | `scenario-gateway-domain-mobile-async-recovered.png` + `scenario-gateway-domain-mobile-dark-async-recovered.png` async-recovered framing 正常 | SDPCAR-08 · RESP-07 |
| 3 | 端点推送通道后续异步韧性 | 端点异步韧性监测 banner + 异步韧性恢复完成摘要 tablet/mobile light/dark 首屏可见 | SDPCAR-08 · PAT-08 |
| 4 | async-pending 态 | mobile dark 下重试队列摘要与异步韧性监测 banner 可辨认 | SDPCAR-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 async-pending/async-recovered 截图全过 | SDPCAR-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 async-pending 面板 → 点击「触发端点异步韧性恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCAR-09 — Governance 审计行推送通道后续异步韧性 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-async-pending.png`、`scenario-governance-domain-mobile-async-pending.png`、`scenario-governance-domain-mobile-dark-async-recovered.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark async-pending | `scenario-governance-domain-tablet-async-pending.png` + `scenario-governance-domain-tablet-dark-async-pending.png` async-pending framing 正常 | SDPCAR-09 · RESP-06 |
| 2 | mobile light/dark async-recovered | `scenario-governance-domain-mobile-async-recovered.png` + `scenario-governance-domain-mobile-dark-async-recovered.png` async-recovered framing 正常 | SDPCAR-09 · RESP-07 |
| 3 | 审计推送通道后续异步韧性 | 审计异步韧性监测 banner + 异步韧性恢复完成摘要 tablet/mobile light/dark 首屏可见 | SDPCAR-09 · PAT-09 |
| 4 | async-recovered 文案 | mobile dark 下「异步韧性恢复已完成，合规事件推送订阅恢复，可继续提交策略变更」文案可辨认 | SDPCAR-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 async-pending/async-recovered 截图全过 | SDPCAR-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 async-pending 面板 → 点击「触发审计异步韧性恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCAR-10 — 场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{async-pending,async-recovered}.png` + `scenarioDomainPushChannelAsyncResilienceViewportLightDarkScreenshotStates.pushChannelAsyncResilienceStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × async-pending/async-recovered 全量 golden 存在 | SDPCAR-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelAsyncResilienceViewportLightDarkScreenshots` 通过 | SDPCAR-10 · PREVIEW-* |
| 3 | async-pending 态 | 五域 `data-audit="scenario-domain-async-pending-overlay"` `data-state="async-pending"` 可见 | SDPCAR-10 · LOGIC-* |
| 4 | async-recovered 态 | 五域点击异步韧性恢复 trigger 后 `role="status"` + `data-state="async-recovered"` 可见 | SDPCAR-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelAsyncResilienceStateMatrixComplete = true` | SDPCAR-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道后续异步韧性截图与门禁 JSON 输出。
