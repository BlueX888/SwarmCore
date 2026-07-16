# Scenario Domain Long Polling Stream Subscription Viewport Light/Dark Screenshot 评审清单

> DOCS-064 / G113 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题长轮询/流式订阅独立截图视觉回归抽检**，确保每个场景 section 在长轮询等待态、流式订阅态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md`（SDSRB-01～05）、`scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md`（SDLPS-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图抽检 | 对应 SDLPS 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标长轮询/流式订阅 tablet/mobile light/dark golden 对照 | SDLPS-01 + `scenario-bi-domain-tablet-long-polling.png` + `scenario-bi-domain-mobile-dark-stream-subscribed.png` |
| DevOps 场景阶段长轮询/流式订阅 tablet/mobile light/dark golden 对照 | SDLPS-02 + `scenario-devops-domain-tablet-long-polling.png` + `scenario-devops-domain-mobile-dark-stream-subscribed.png` |
| Gateway 场景端点长轮询/流式订阅 tablet/mobile light/dark golden 对照 | SDLPS-03 + `scenario-gateway-domain-tablet-long-polling.png` + `scenario-gateway-domain-mobile-dark-stream-subscribed.png` |
| Governance 场景审计行长轮询/流式订阅 tablet/mobile light/dark golden 对照 | SDLPS-04 + `scenario-governance-domain-tablet-long-polling.png` + `scenario-governance-domain-mobile-dark-stream-subscribed.png` |
| PaaS 场景容量长轮询/流式订阅 tablet/mobile light/dark golden 对照 | SDLPS-05 + `scenario-paas-domain-tablet-long-polling.png` + `scenario-paas-domain-mobile-dark-stream-subscribed.png` |

## 通用前置

1. 先完成 `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md` SDSRB-01～05（SSE 重连/背压释放独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{long-polling,stream-subscribed}.png` 四视口双主题长轮询/流式订阅独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 long-polling 与一张 stream-subscribed 独立截图；long-polling 必须出现挂起 banner 与等待摘要，stream-subscribed 必须出现订阅 banner 与查看订阅详情 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 长轮询/流式订阅截图出现文案裁切、挂起 banner 对比度不足、subscribed banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图（G113）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图抽检行。

## SDLPS-01 — BI 场景指标长轮询/流式订阅 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-long-polling.png`、`scenario-bi-domain-tablet-dark-long-polling.png`、`scenario-bi-domain-mobile-long-polling.png`、`scenario-bi-domain-mobile-dark-long-polling.png`、`scenario-bi-domain-tablet-stream-subscribed.png`、`scenario-bi-domain-tablet-dark-stream-subscribed.png`、`scenario-bi-domain-mobile-stream-subscribed.png`、`scenario-bi-domain-mobile-dark-stream-subscribed.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light long-polling 截图 | `scenario-bi-domain-tablet-long-polling.png` 存在且 long-polling framing 正常 | SDLPS-01 · RESP-06 |
| 2 | tablet dark long-polling 截图 | `scenario-bi-domain-tablet-dark-long-polling.png` 存在且挂起 banner 可读 | SDLPS-01 · VIS-05 |
| 3 | mobile light stream-subscribed 截图 | `scenario-bi-domain-mobile-stream-subscribed.png` subscribed banner 首屏可见 | SDLPS-01 · RESP-07 |
| 4 | mobile dark stream-subscribed 截图 | `scenario-bi-domain-mobile-dark-stream-subscribed.png` subscribed 对比度可辨认 | SDLPS-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainLongPollingStreamSubscriptionViewportLightDarkScreenshots` biDomain 全过 | SDLPS-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 long-polling 面板 → 点击「触发指标流式订阅」→ 对照 tablet/mobile light/dark 八张 long-polling/stream-subscribed 截图。

## SDLPS-02 — DevOps 场景阶段长轮询/流式订阅 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-long-polling.png`、`scenario-devops-domain-tablet-dark-long-polling.png`、`scenario-devops-domain-mobile-long-polling.png`、`scenario-devops-domain-mobile-dark-long-polling.png`、`scenario-devops-domain-tablet-stream-subscribed.png`、`scenario-devops-domain-tablet-dark-stream-subscribed.png`、`scenario-devops-domain-mobile-stream-subscribed.png`、`scenario-devops-domain-mobile-dark-stream-subscribed.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light long-polling 截图 | `scenario-devops-domain-tablet-long-polling.png` 存在且 long-polling framing 正常 | SDLPS-02 · RESP-06 |
| 2 | tablet dark long-polling 截图 | `scenario-devops-domain-tablet-dark-long-polling.png` 存在且等待摘要可读 | SDLPS-02 · VIS-05 |
| 3 | mobile light stream-subscribed 截图 | `scenario-devops-domain-mobile-stream-subscribed.png` 流水线 subscribed 首屏可见 | SDLPS-02 · RESP-07 |
| 4 | mobile dark stream-subscribed 截图 | `scenario-devops-domain-mobile-dark-stream-subscribed.png` subscribed 对比度可辨认 | SDLPS-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 长轮询/流式订阅 tablet/mobile light/dark 可见 | SDLPS-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 long-polling 面板 → 点击「触发阶段流式订阅」→ 对照 tablet/mobile light/dark 八张截图。

## SDLPS-03 — Gateway 场景端点长轮询/流式订阅 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-long-polling.png`、`scenario-gateway-domain-tablet-dark-long-polling.png`、`scenario-gateway-domain-mobile-long-polling.png`、`scenario-gateway-domain-mobile-dark-long-polling.png`、`scenario-gateway-domain-tablet-stream-subscribed.png`、`scenario-gateway-domain-tablet-dark-stream-subscribed.png`、`scenario-gateway-domain-mobile-stream-subscribed.png`、`scenario-gateway-domain-mobile-dark-stream-subscribed.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light long-polling 截图 | `scenario-gateway-domain-tablet-long-polling.png` 存在且 long-polling framing 正常 | SDLPS-03 · RESP-06 |
| 2 | tablet dark long-polling 截图 | `scenario-gateway-domain-tablet-dark-long-polling.png` 存在且等待摘要可读 | SDLPS-03 · VIS-05 |
| 3 | mobile light stream-subscribed 截图 | `scenario-gateway-domain-mobile-stream-subscribed.png` 端点 subscribed 首屏可见 | SDLPS-03 · RESP-07 |
| 4 | mobile dark stream-subscribed 截图 | `scenario-gateway-domain-mobile-dark-stream-subscribed.png` subscribed 层级不丢失 | SDLPS-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 长轮询/流式订阅 tablet/mobile light/dark 可见 | SDLPS-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 long-polling 面板 → 点击「触发端点流式订阅」→ 对照 tablet/mobile light/dark 八张截图。

## SDLPS-04 — Governance 场景审计行长轮询/流式订阅 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-long-polling.png`、`scenario-governance-domain-tablet-dark-long-polling.png`、`scenario-governance-domain-mobile-long-polling.png`、`scenario-governance-domain-mobile-dark-long-polling.png`、`scenario-governance-domain-tablet-stream-subscribed.png`、`scenario-governance-domain-tablet-dark-stream-subscribed.png`、`scenario-governance-domain-mobile-stream-subscribed.png`、`scenario-governance-domain-mobile-dark-stream-subscribed.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light long-polling 截图 | `scenario-governance-domain-tablet-long-polling.png` 存在且 long-polling framing 正常 | SDLPS-04 · RESP-06 |
| 2 | tablet dark long-polling 截图 | `scenario-governance-domain-tablet-dark-long-polling.png` 存在且等待摘要可读 | SDLPS-04 · VIS-05 |
| 3 | mobile light stream-subscribed 截图 | `scenario-governance-domain-mobile-stream-subscribed.png` 审计 subscribed 首屏可见 | SDLPS-04 · RESP-07 |
| 4 | mobile dark stream-subscribed 截图 | `scenario-governance-domain-mobile-dark-stream-subscribed.png` subscribed 密度一致 | SDLPS-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 长轮询/流式订阅 tablet/mobile light/dark 可见 | SDLPS-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 long-polling 面板 → 点击「触发审计流式订阅」→ 对照 tablet/mobile light/dark 八张截图。

## SDLPS-05 — PaaS 场景容量长轮询/流式订阅 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-long-polling.png`、`scenario-paas-domain-tablet-dark-long-polling.png`、`scenario-paas-domain-mobile-long-polling.png`、`scenario-paas-domain-mobile-dark-long-polling.png`、`scenario-paas-domain-tablet-stream-subscribed.png`、`scenario-paas-domain-tablet-dark-stream-subscribed.png`、`scenario-paas-domain-mobile-stream-subscribed.png`、`scenario-paas-domain-mobile-dark-stream-subscribed.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light long-polling 截图 | `scenario-paas-domain-tablet-long-polling.png` 存在且 long-polling framing 正常 | SDLPS-05 · RESP-06 |
| 2 | tablet dark long-polling 截图 | `scenario-paas-domain-tablet-dark-long-polling.png` 存在且等待摘要可读 | SDLPS-05 · VIS-05 |
| 3 | mobile light stream-subscribed 截图 | `scenario-paas-domain-mobile-stream-subscribed.png` 容量 subscribed 首屏可见 | SDLPS-05 · RESP-07 |
| 4 | mobile dark stream-subscribed 截图 | `scenario-paas-domain-mobile-dark-stream-subscribed.png` subscribed 列表项可辨认 | SDLPS-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 长轮询/流式订阅 tablet/mobile light/dark 可见 | SDLPS-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 long-polling 面板 → 点击「触发容量流式订阅」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md` SDLPS-06～10
- SSE 重连/背压释放 前置：`scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md` SDSRB-01～05
- 选型表：`decision-matrix.md` G113 场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDLPS-01～10
- Runtime 门禁：`verifyScenarioDomainLongPollingStreamSubscriptionViewportLightDarkScreenshots`
