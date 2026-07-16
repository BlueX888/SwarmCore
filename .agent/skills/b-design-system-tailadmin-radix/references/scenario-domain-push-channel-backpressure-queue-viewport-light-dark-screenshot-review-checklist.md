# Scenario Domain Push Channel Backpressure Queue Viewport Light/Dark Screenshot 评审清单

> DOCS-067 / G116 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道背压/队列排空独立截图视觉回归抽检**，确保每个场景 section 在推送通道背压激活态、队列排空态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md`（SDPCBRL-01～05）、`scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md`（SDPCBQ-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道背压/队列排空 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCBQ 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道背压/队列排空 tablet/mobile light/dark golden 对照 | SDPCBQ-01 + `scenario-bi-domain-tablet-backpressure-active.png` + `scenario-bi-domain-mobile-dark-queue-drained.png` |
| DevOps 场景阶段推送通道背压/队列排空 tablet/mobile light/dark golden 对照 | SDPCBQ-02 + `scenario-devops-domain-tablet-backpressure-active.png` + `scenario-devops-domain-mobile-dark-queue-drained.png` |
| Gateway 场景端点推送通道背压/队列排空 tablet/mobile light/dark golden 对照 | SDPCBQ-03 + `scenario-gateway-domain-tablet-backpressure-active.png` + `scenario-gateway-domain-mobile-dark-queue-drained.png` |
| Governance 场景审计行推送通道背压/队列排空 tablet/mobile light/dark golden 对照 | SDPCBQ-04 + `scenario-governance-domain-tablet-backpressure-active.png` + `scenario-governance-domain-mobile-dark-queue-drained.png` |
| PaaS 场景容量推送通道背压/队列排空 tablet/mobile light/dark golden 对照 | SDPCBQ-05 + `scenario-paas-domain-tablet-backpressure-active.png` + `scenario-paas-domain-mobile-dark-queue-drained.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md` SDPCBRL-01～05（推送通道熔断/限流解除独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{backpressure-active,queue-drained}.png` 四视口双主题推送通道背压/队列排空独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 backpressure-active 与一张 queue-drained 独立截图；backpressure-active 必须出现背压 banner「推送通道背压激活（队列积压模式）」与积压队列摘要，queue-drained 必须出现队列排空 banner 与「查看队列排空详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道背压/队列排空截图出现文案裁切、背压 banner 对比度不足、queue-drained banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道背压/队列排空 tablet/mobile light/dark 独立截图（G116）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道背压/队列排空 tablet/mobile light/dark 独立截图抽检行。

## SDPCBQ-01 — BI 场景指标推送通道背压/队列排空 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-backpressure-active.png`、`scenario-bi-domain-tablet-dark-backpressure-active.png`、`scenario-bi-domain-mobile-backpressure-active.png`、`scenario-bi-domain-mobile-dark-backpressure-active.png`、`scenario-bi-domain-tablet-queue-drained.png`、`scenario-bi-domain-tablet-dark-queue-drained.png`、`scenario-bi-domain-mobile-queue-drained.png`、`scenario-bi-domain-mobile-dark-queue-drained.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light backpressure-active 截图 | `scenario-bi-domain-tablet-backpressure-active.png` 存在且 backpressure-active framing 正常 | SDPCBQ-01 · RESP-06 |
| 2 | tablet dark backpressure-active 截图 | `scenario-bi-domain-tablet-dark-backpressure-active.png` 存在且背压 banner 可读 | SDPCBQ-01 · VIS-05 |
| 3 | mobile light queue-drained 截图 | `scenario-bi-domain-mobile-queue-drained.png` queue-drained banner 首屏可见 | SDPCBQ-01 · RESP-07 |
| 4 | mobile dark queue-drained 截图 | `scenario-bi-domain-mobile-dark-queue-drained.png` queue-drained 对比度可辨认 | SDPCBQ-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelBackpressureQueueViewportLightDarkScreenshots` biDomain 全过 | SDPCBQ-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 backpressure-active 面板 → 点击「触发指标队列排空」→ 对照 tablet/mobile light/dark 八张 backpressure-active/queue-drained 截图。

## SDPCBQ-02 — DevOps 场景阶段推送通道背压/队列排空 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-backpressure-active.png`、`scenario-devops-domain-tablet-dark-backpressure-active.png`、`scenario-devops-domain-mobile-backpressure-active.png`、`scenario-devops-domain-mobile-dark-backpressure-active.png`、`scenario-devops-domain-tablet-queue-drained.png`、`scenario-devops-domain-tablet-dark-queue-drained.png`、`scenario-devops-domain-mobile-queue-drained.png`、`scenario-devops-domain-mobile-dark-queue-drained.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light backpressure-active 截图 | `scenario-devops-domain-tablet-backpressure-active.png` 存在且 backpressure-active framing 正常 | SDPCBQ-02 · RESP-06 |
| 2 | tablet dark backpressure-active 截图 | `scenario-devops-domain-tablet-dark-backpressure-active.png` 存在且积压摘要可读 | SDPCBQ-02 · VIS-05 |
| 3 | mobile light queue-drained 截图 | `scenario-devops-domain-mobile-queue-drained.png` 流水线 queue-drained 首屏可见 | SDPCBQ-02 · RESP-07 |
| 4 | mobile dark queue-drained 截图 | `scenario-devops-domain-mobile-dark-queue-drained.png` queue-drained 对比度可辨认 | SDPCBQ-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道背压/队列排空 tablet/mobile light/dark 可见 | SDPCBQ-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 backpressure-active 面板 → 点击「触发阶段队列排空」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBQ-03 — Gateway 场景端点推送通道背压/队列排空 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-backpressure-active.png`、`scenario-gateway-domain-tablet-dark-backpressure-active.png`、`scenario-gateway-domain-mobile-backpressure-active.png`、`scenario-gateway-domain-mobile-dark-backpressure-active.png`、`scenario-gateway-domain-tablet-queue-drained.png`、`scenario-gateway-domain-tablet-dark-queue-drained.png`、`scenario-gateway-domain-mobile-queue-drained.png`、`scenario-gateway-domain-mobile-dark-queue-drained.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light backpressure-active 截图 | `scenario-gateway-domain-tablet-backpressure-active.png` 存在且 backpressure-active framing 正常 | SDPCBQ-03 · RESP-06 |
| 2 | tablet dark backpressure-active 截图 | `scenario-gateway-domain-tablet-dark-backpressure-active.png` 存在且积压摘要可读 | SDPCBQ-03 · VIS-05 |
| 3 | mobile light queue-drained 截图 | `scenario-gateway-domain-mobile-queue-drained.png` 端点 queue-drained 首屏可见 | SDPCBQ-03 · RESP-07 |
| 4 | mobile dark queue-drained 截图 | `scenario-gateway-domain-mobile-dark-queue-drained.png` queue-drained 层级不丢失 | SDPCBQ-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道背压/队列排空 tablet/mobile light/dark 可见 | SDPCBQ-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 backpressure-active 面板 → 点击「触发端点队列排空」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBQ-04 — Governance 场景审计行推送通道背压/队列排空 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-backpressure-active.png`、`scenario-governance-domain-tablet-dark-backpressure-active.png`、`scenario-governance-domain-mobile-backpressure-active.png`、`scenario-governance-domain-mobile-dark-backpressure-active.png`、`scenario-governance-domain-tablet-queue-drained.png`、`scenario-governance-domain-tablet-dark-queue-drained.png`、`scenario-governance-domain-mobile-queue-drained.png`、`scenario-governance-domain-mobile-dark-queue-drained.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light backpressure-active 截图 | `scenario-governance-domain-tablet-backpressure-active.png` 存在且 backpressure-active framing 正常 | SDPCBQ-04 · RESP-06 |
| 2 | tablet dark backpressure-active 截图 | `scenario-governance-domain-tablet-dark-backpressure-active.png` 存在且积压摘要可读 | SDPCBQ-04 · VIS-05 |
| 3 | mobile light queue-drained 截图 | `scenario-governance-domain-mobile-queue-drained.png` 审计 queue-drained 首屏可见 | SDPCBQ-04 · RESP-07 |
| 4 | mobile dark queue-drained 截图 | `scenario-governance-domain-mobile-dark-queue-drained.png` queue-drained 密度一致 | SDPCBQ-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道背压/队列排空 tablet/mobile light/dark 可见 | SDPCBQ-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 backpressure-active 面板 → 点击「触发审计队列排空」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBQ-05 — PaaS 场景容量推送通道背压/队列排空 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-backpressure-active.png`、`scenario-paas-domain-tablet-dark-backpressure-active.png`、`scenario-paas-domain-mobile-backpressure-active.png`、`scenario-paas-domain-mobile-dark-backpressure-active.png`、`scenario-paas-domain-tablet-queue-drained.png`、`scenario-paas-domain-tablet-dark-queue-drained.png`、`scenario-paas-domain-mobile-queue-drained.png`、`scenario-paas-domain-mobile-dark-queue-drained.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light backpressure-active 截图 | `scenario-paas-domain-tablet-backpressure-active.png` 存在且 backpressure-active framing 正常 | SDPCBQ-05 · RESP-06 |
| 2 | tablet dark backpressure-active 截图 | `scenario-paas-domain-tablet-dark-backpressure-active.png` 存在且积压摘要可读 | SDPCBQ-05 · VIS-05 |
| 3 | mobile light queue-drained 截图 | `scenario-paas-domain-mobile-queue-drained.png` 容量 queue-drained 首屏可见 | SDPCBQ-05 · RESP-07 |
| 4 | mobile dark queue-drained 截图 | `scenario-paas-domain-mobile-dark-queue-drained.png` queue-drained 列表项可辨认 | SDPCBQ-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道背压/队列排空 tablet/mobile light/dark 可见 | SDPCBQ-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 backpressure-active 面板 → 点击「触发容量队列排空」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md` SDPCBQ-06～10
- 推送通道熔断/限流解除 前置：`scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md` SDPCBRL-01～05
- 选型表：`decision-matrix.md` G116 场景域推送通道背压/队列排空 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCBQ-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelBackpressureQueueViewportLightDarkScreenshots`
