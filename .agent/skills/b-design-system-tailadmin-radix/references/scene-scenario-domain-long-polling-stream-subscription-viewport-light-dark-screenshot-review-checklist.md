# 场景 Scenario Domain Long Polling Stream Subscription Viewport Light/Dark Screenshot 评审清单

> DOCS-064 / G113 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题长轮询/流式订阅独立截图抽检**，确保各域 section 在长轮询等待态与流式订阅态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md`（SDLPS-01～05）、`scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md`（SDSRB-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDLPS 块 + `quality-rubric.md` |
| BI Analytics 指标长轮询/流式订阅 tablet/mobile light/dark 独立截图 | SDLPS-06 + `tailadmin-bi-analytics` |
| DevOps 阶段长轮询/流式订阅 tablet/mobile light/dark 独立截图 | SDLPS-07 + `scenario-devops` |
| Gateway 端点长轮询/流式订阅 tablet/mobile light/dark 独立截图 | SDLPS-08 + `scenario-gateway` |
| Governance 审计行长轮询/流式订阅 tablet/mobile light/dark 独立截图 | SDLPS-09 + `scenario-governance` |
| 场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图束缺门禁 | SDLPS-10 + `verifyScenarioDomainSseReconnectBackpressureViewportLightDarkScreenshots` + `verifyScenarioDomainLongPollingStreamSubscriptionViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md` SDLPS-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{long-polling,stream-subscribed}.png` 共 40 张长轮询/流式订阅独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 长轮询/流式订阅独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图（G113）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDLPS-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDLPS-06 — BI Analytics 指标长轮询/流式订阅 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-long-polling.png`、`scenario-bi-domain-mobile-dark-stream-subscribed.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark long-polling | `scenario-bi-domain-tablet-long-polling.png` + `scenario-bi-domain-tablet-dark-long-polling.png` long-polling framing 正常 | SDLPS-06 · RESP-06 |
| 2 | mobile light/dark stream-subscribed | `scenario-bi-domain-mobile-stream-subscribed.png` + `scenario-bi-domain-mobile-dark-stream-subscribed.png` subscribed framing 正常 | SDLPS-06 · RESP-07 |
| 3 | 指标长轮询/流式订阅 | 挂起 banner + 等待摘要 + 订阅完成 banner tablet/mobile light/dark 首屏可见 | SDLPS-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 long-polling banner 与 subscribed banner 层级可辨认 | SDLPS-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 long-polling/stream-subscribed 截图全过 | SDLPS-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 long-polling 面板 → 点击「触发指标流式订阅」→ 对照 tablet/mobile light/dark 八张长轮询/流式订阅截图。

## SDLPS-07 — DevOps 阶段长轮询/流式订阅 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-long-polling.png`、`scenario-devops-domain-mobile-dark-stream-subscribed.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark long-polling | `scenario-devops-domain-tablet-long-polling.png` + `scenario-devops-domain-tablet-dark-long-polling.png` long-polling framing 正常 | SDLPS-07 · RESP-06 |
| 2 | mobile light/dark stream-subscribed | `scenario-devops-domain-mobile-stream-subscribed.png` + `scenario-devops-domain-mobile-dark-stream-subscribed.png` subscribed framing 正常 | SDLPS-07 · RESP-07 |
| 3 | 阶段长轮询/流式订阅 | 流水线挂起 banner + 订阅完成摘要 tablet/mobile light/dark 首屏可见 | SDLPS-07 · PAT-07 |
| 4 | subscribed 态 | mobile dark 下 subscribed 文案与查看订阅详情按钮可辨认 | SDLPS-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 long-polling/stream-subscribed 截图全过 | SDLPS-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 long-polling 面板 → 点击「触发阶段流式订阅」→ 对照 tablet/mobile light/dark 八张截图。

## SDLPS-08 — Gateway 端点长轮询/流式订阅 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-long-polling.png`、`scenario-gateway-domain-mobile-dark-stream-subscribed.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark long-polling | `scenario-gateway-domain-tablet-long-polling.png` + `scenario-gateway-domain-tablet-dark-long-polling.png` long-polling framing 正常 | SDLPS-08 · RESP-06 |
| 2 | mobile light/dark stream-subscribed | `scenario-gateway-domain-mobile-stream-subscribed.png` + `scenario-gateway-domain-mobile-dark-stream-subscribed.png` subscribed framing 正常 | SDLPS-08 · RESP-07 |
| 3 | 端点长轮询/流式订阅 | 端点挂起 banner + 订阅完成摘要 tablet/mobile light/dark 首屏可见 | SDLPS-08 · PAT-08 |
| 4 | long-polling 态 | mobile dark 下挂起进度与 banner 可辨认 | SDLPS-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 long-polling/stream-subscribed 截图全过 | SDLPS-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 long-polling 面板 → 点击「触发端点流式订阅」→ 对照 tablet/mobile light/dark 八张截图。

## SDLPS-09 — Governance 审计行长轮询/流式订阅 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-long-polling.png`、`scenario-governance-domain-mobile-long-polling.png`、`scenario-governance-domain-mobile-dark-stream-subscribed.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark long-polling | `scenario-governance-domain-tablet-long-polling.png` + `scenario-governance-domain-tablet-dark-long-polling.png` long-polling framing 正常 | SDLPS-09 · RESP-06 |
| 2 | mobile light/dark stream-subscribed | `scenario-governance-domain-mobile-stream-subscribed.png` + `scenario-governance-domain-mobile-dark-stream-subscribed.png` subscribed framing 正常 | SDLPS-09 · RESP-07 |
| 3 | 审计长轮询/流式订阅 | 审计挂起 banner + 订阅完成摘要 tablet/mobile light/dark 首屏可见 | SDLPS-09 · PAT-09 |
| 4 | subscribed 文案 | mobile dark 下「流式订阅已建立，合规事件通道稳定，可继续接收审计推送」文案可辨认 | SDLPS-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 long-polling/stream-subscribed 截图全过 | SDLPS-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 long-polling 面板 → 点击「触发审计流式订阅」→ 对照 tablet/mobile light/dark 八张截图。

## SDLPS-10 — 场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{long-polling,stream-subscribed}.png` + `scenarioDomainLongPollingStreamSubscriptionViewportLightDarkScreenshotStates.longPollingStreamSubscriptionStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × long-polling/stream-subscribed 全量 golden 存在 | SDLPS-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainLongPollingStreamSubscriptionViewportLightDarkScreenshots` 通过 | SDLPS-10 · PREVIEW-* |
| 3 | long-polling 态 | 五域 `data-audit="scenario-domain-long-polling-overlay"` `data-state="long-polling"` 可见 | SDLPS-10 · LOGIC-* |
| 4 | stream-subscribed 态 | 五域点击 stream subscribe trigger 后 `role="status"` + `data-state="stream-subscribed"` 可见 | SDLPS-10 · ASYNC-* |
| 5 | 矩阵完整 | `longPollingStreamSubscriptionStateMatrixComplete = true` | SDLPS-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张长轮询/流式订阅截图与门禁 JSON 输出。
