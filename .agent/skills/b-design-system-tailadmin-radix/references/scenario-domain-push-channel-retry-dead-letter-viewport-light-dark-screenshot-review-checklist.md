# Scenario Domain Push Channel Retry Dead Letter Viewport Light/Dark Screenshot 评审清单

> DOCS-068 / G117 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道重试/死信队列独立截图视觉回归抽检**，确保每个场景 section 在推送通道重试激活态、死信队列排空态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md`（SDPCBQ-01～05）、`scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md`（SDPCRDL-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCRDL 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道重试/死信队列 tablet/mobile light/dark golden 对照 | SDPCRDL-01 + `scenario-bi-domain-tablet-retry-active.png` + `scenario-bi-domain-mobile-dark-dead-letter-drained.png` |
| DevOps 场景阶段推送通道重试/死信队列 tablet/mobile light/dark golden 对照 | SDPCRDL-02 + `scenario-devops-domain-tablet-retry-active.png` + `scenario-devops-domain-mobile-dark-dead-letter-drained.png` |
| Gateway 场景端点推送通道重试/死信队列 tablet/mobile light/dark golden 对照 | SDPCRDL-03 + `scenario-gateway-domain-tablet-retry-active.png` + `scenario-gateway-domain-mobile-dark-dead-letter-drained.png` |
| Governance 场景审计行推送通道重试/死信队列 tablet/mobile light/dark golden 对照 | SDPCRDL-04 + `scenario-governance-domain-tablet-retry-active.png` + `scenario-governance-domain-mobile-dark-dead-letter-drained.png` |
| PaaS 场景容量推送通道重试/死信队列 tablet/mobile light/dark golden 对照 | SDPCRDL-05 + `scenario-paas-domain-tablet-retry-active.png` + `scenario-paas-domain-mobile-dark-dead-letter-drained.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md` SDPCBQ-01～05（推送通道背压/队列排空独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{retry-active,dead-letter-drained}.png` 四视口双主题推送通道重试/死信队列独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 retry-active 与一张 dead-letter-drained 独立截图；retry-active 必须出现重试 banner「推送通道重试激活（指数退避模式）」与死信队列摘要，dead-letter-drained 必须出现死信队列排空 banner 与「查看死信队列排空详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道重试/死信队列截图出现文案裁切、重试 banner 对比度不足、dead-letter-drained banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图（G117）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图抽检行。

## SDPCRDL-01 — BI 场景指标推送通道重试/死信队列 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-retry-active.png`、`scenario-bi-domain-tablet-dark-retry-active.png`、`scenario-bi-domain-mobile-retry-active.png`、`scenario-bi-domain-mobile-dark-retry-active.png`、`scenario-bi-domain-tablet-dead-letter-drained.png`、`scenario-bi-domain-tablet-dark-dead-letter-drained.png`、`scenario-bi-domain-mobile-dead-letter-drained.png`、`scenario-bi-domain-mobile-dark-dead-letter-drained.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retry-active 截图 | `scenario-bi-domain-tablet-retry-active.png` 存在且 retry-active framing 正常 | SDPCRDL-01 · RESP-06 |
| 2 | tablet dark retry-active 截图 | `scenario-bi-domain-tablet-dark-retry-active.png` 存在且重试 banner 可读 | SDPCRDL-01 · VIS-05 |
| 3 | mobile light dead-letter-drained 截图 | `scenario-bi-domain-mobile-dead-letter-drained.png` dead-letter-drained banner 首屏可见 | SDPCRDL-01 · RESP-07 |
| 4 | mobile dark dead-letter-drained 截图 | `scenario-bi-domain-mobile-dark-dead-letter-drained.png` dead-letter-drained 对比度可辨认 | SDPCRDL-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelRetryDeadLetterViewportLightDarkScreenshots` biDomain 全过 | SDPCRDL-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 retry-active 面板 → 点击「触发指标死信队列排空」→ 对照 tablet/mobile light/dark 八张 retry-active/dead-letter-drained 截图。

## SDPCRDL-02 — DevOps 场景阶段推送通道重试/死信队列 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-retry-active.png`、`scenario-devops-domain-tablet-dark-retry-active.png`、`scenario-devops-domain-mobile-retry-active.png`、`scenario-devops-domain-mobile-dark-retry-active.png`、`scenario-devops-domain-tablet-dead-letter-drained.png`、`scenario-devops-domain-tablet-dark-dead-letter-drained.png`、`scenario-devops-domain-mobile-dead-letter-drained.png`、`scenario-devops-domain-mobile-dark-dead-letter-drained.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retry-active 截图 | `scenario-devops-domain-tablet-retry-active.png` 存在且 retry-active framing 正常 | SDPCRDL-02 · RESP-06 |
| 2 | tablet dark retry-active 截图 | `scenario-devops-domain-tablet-dark-retry-active.png` 存在且死信队列摘要可读 | SDPCRDL-02 · VIS-05 |
| 3 | mobile light dead-letter-drained 截图 | `scenario-devops-domain-mobile-dead-letter-drained.png` 流水线 dead-letter-drained 首屏可见 | SDPCRDL-02 · RESP-07 |
| 4 | mobile dark dead-letter-drained 截图 | `scenario-devops-domain-mobile-dark-dead-letter-drained.png` dead-letter-drained 对比度可辨认 | SDPCRDL-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道重试/死信队列 tablet/mobile light/dark 可见 | SDPCRDL-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 retry-active 面板 → 点击「触发阶段死信队列排空」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCRDL-03 — Gateway 场景端点推送通道重试/死信队列 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-retry-active.png`、`scenario-gateway-domain-tablet-dark-retry-active.png`、`scenario-gateway-domain-mobile-retry-active.png`、`scenario-gateway-domain-mobile-dark-retry-active.png`、`scenario-gateway-domain-tablet-dead-letter-drained.png`、`scenario-gateway-domain-tablet-dark-dead-letter-drained.png`、`scenario-gateway-domain-mobile-dead-letter-drained.png`、`scenario-gateway-domain-mobile-dark-dead-letter-drained.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retry-active 截图 | `scenario-gateway-domain-tablet-retry-active.png` 存在且 retry-active framing 正常 | SDPCRDL-03 · RESP-06 |
| 2 | tablet dark retry-active 截图 | `scenario-gateway-domain-tablet-dark-retry-active.png` 存在且死信队列摘要可读 | SDPCRDL-03 · VIS-05 |
| 3 | mobile light dead-letter-drained 截图 | `scenario-gateway-domain-mobile-dead-letter-drained.png` 端点 dead-letter-drained 首屏可见 | SDPCRDL-03 · RESP-07 |
| 4 | mobile dark dead-letter-drained 截图 | `scenario-gateway-domain-mobile-dark-dead-letter-drained.png` dead-letter-drained 层级不丢失 | SDPCRDL-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道重试/死信队列 tablet/mobile light/dark 可见 | SDPCRDL-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 retry-active 面板 → 点击「触发端点死信队列排空」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCRDL-04 — Governance 场景审计行推送通道重试/死信队列 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-retry-active.png`、`scenario-governance-domain-tablet-dark-retry-active.png`、`scenario-governance-domain-mobile-retry-active.png`、`scenario-governance-domain-mobile-dark-retry-active.png`、`scenario-governance-domain-tablet-dead-letter-drained.png`、`scenario-governance-domain-tablet-dark-dead-letter-drained.png`、`scenario-governance-domain-mobile-dead-letter-drained.png`、`scenario-governance-domain-mobile-dark-dead-letter-drained.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retry-active 截图 | `scenario-governance-domain-tablet-retry-active.png` 存在且 retry-active framing 正常 | SDPCRDL-04 · RESP-06 |
| 2 | tablet dark retry-active 截图 | `scenario-governance-domain-tablet-dark-retry-active.png` 存在且死信队列摘要可读 | SDPCRDL-04 · VIS-05 |
| 3 | mobile light dead-letter-drained 截图 | `scenario-governance-domain-mobile-dead-letter-drained.png` 审计 dead-letter-drained 首屏可见 | SDPCRDL-04 · RESP-07 |
| 4 | mobile dark dead-letter-drained 截图 | `scenario-governance-domain-mobile-dark-dead-letter-drained.png` dead-letter-drained 密度一致 | SDPCRDL-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道重试/死信队列 tablet/mobile light/dark 可见 | SDPCRDL-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 retry-active 面板 → 点击「触发审计死信队列排空」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCRDL-05 — PaaS 场景容量推送通道重试/死信队列 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-retry-active.png`、`scenario-paas-domain-tablet-dark-retry-active.png`、`scenario-paas-domain-mobile-retry-active.png`、`scenario-paas-domain-mobile-dark-retry-active.png`、`scenario-paas-domain-tablet-dead-letter-drained.png`、`scenario-paas-domain-tablet-dark-dead-letter-drained.png`、`scenario-paas-domain-mobile-dead-letter-drained.png`、`scenario-paas-domain-mobile-dark-dead-letter-drained.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retry-active 截图 | `scenario-paas-domain-tablet-retry-active.png` 存在且 retry-active framing 正常 | SDPCRDL-05 · RESP-06 |
| 2 | tablet dark retry-active 截图 | `scenario-paas-domain-tablet-dark-retry-active.png` 存在且死信队列摘要可读 | SDPCRDL-05 · VIS-05 |
| 3 | mobile light dead-letter-drained 截图 | `scenario-paas-domain-mobile-dead-letter-drained.png` 容量 dead-letter-drained 首屏可见 | SDPCRDL-05 · RESP-07 |
| 4 | mobile dark dead-letter-drained 截图 | `scenario-paas-domain-mobile-dark-dead-letter-drained.png` dead-letter-drained 列表项可辨认 | SDPCRDL-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道重试/死信队列 tablet/mobile light/dark 可见 | SDPCRDL-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 retry-active 面板 → 点击「触发容量死信队列排空」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md` SDPCRDL-06～10
- 推送通道背压/队列排空 前置：`scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md` SDPCBQ-01～05
- 选型表：`decision-matrix.md` G117 场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCRDL-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelRetryDeadLetterViewportLightDarkScreenshots`
