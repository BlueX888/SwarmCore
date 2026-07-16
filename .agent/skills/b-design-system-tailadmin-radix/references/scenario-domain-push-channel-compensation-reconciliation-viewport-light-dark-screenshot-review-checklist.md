# Scenario Domain Push Channel Compensation Reconciliation Viewport Light/Dark Screenshot 评审清单

> DOCS-071 / G120 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道后续补偿/对账独立截图视觉回归抽检**，确保每个场景 section 在推送通道补偿对账中态、补偿对账完成态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md`（SDPCAR-01～05）、`scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md`（SDPCCR-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCCR 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道后续补偿/对账 tablet/mobile light/dark golden 对照 | SDPCCR-01 + `scenario-bi-domain-tablet-compensation-pending.png` + `scenario-bi-domain-mobile-dark-reconciliation-complete.png` |
| DevOps 场景阶段推送通道后续补偿/对账 tablet/mobile light/dark golden 对照 | SDPCCR-02 + `scenario-devops-domain-tablet-compensation-pending.png` + `scenario-devops-domain-mobile-dark-reconciliation-complete.png` |
| Gateway 场景端点推送通道后续补偿/对账 tablet/mobile light/dark golden 对照 | SDPCCR-03 + `scenario-gateway-domain-tablet-compensation-pending.png` + `scenario-gateway-domain-mobile-dark-reconciliation-complete.png` |
| Governance 场景审计行推送通道后续补偿/对账 tablet/mobile light/dark golden 对照 | SDPCCR-04 + `scenario-governance-domain-tablet-compensation-pending.png` + `scenario-governance-domain-mobile-dark-reconciliation-complete.png` |
| PaaS 场景容量推送通道后续补偿/对账 tablet/mobile light/dark golden 对照 | SDPCCR-05 + `scenario-paas-domain-tablet-compensation-pending.png` + `scenario-paas-domain-mobile-dark-reconciliation-complete.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md` SDPCAR-01～05（推送通道后续异步韧性独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{compensation-pending,reconciliation-complete}.png` 四视口双主题推送通道后续补偿/对账独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 compensation-pending 与一张 reconciliation-complete 独立截图；compensation-pending 必须出现补偿对账 banner「推送通道后续补偿对账中（差异事件排队）」与差异事件摘要，reconciliation-complete 必须出现补偿对账完成 banner 与「查看补偿对账详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道后续补偿/对账截图出现文案裁切、补偿对账 banner 对比度不足、reconciliation-complete banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图（G120）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图抽检行。

## SDPCCR-01 — BI 场景指标推送通道后续补偿/对账 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-compensation-pending.png`、`scenario-bi-domain-tablet-dark-compensation-pending.png`、`scenario-bi-domain-mobile-compensation-pending.png`、`scenario-bi-domain-mobile-dark-compensation-pending.png`、`scenario-bi-domain-tablet-reconciliation-complete.png`、`scenario-bi-domain-tablet-dark-reconciliation-complete.png`、`scenario-bi-domain-mobile-reconciliation-complete.png`、`scenario-bi-domain-mobile-dark-reconciliation-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light compensation-pending 截图 | `scenario-bi-domain-tablet-compensation-pending.png` 存在且 compensation-pending framing 正常 | SDPCCR-01 · RESP-06 |
| 2 | tablet dark compensation-pending 截图 | `scenario-bi-domain-tablet-dark-compensation-pending.png` 存在且补偿对账 banner 可读 | SDPCCR-01 · VIS-05 |
| 3 | mobile light reconciliation-complete 截图 | `scenario-bi-domain-mobile-reconciliation-complete.png` reconciliation-complete banner 首屏可见 | SDPCCR-01 · RESP-07 |
| 4 | mobile dark reconciliation-complete 截图 | `scenario-bi-domain-mobile-dark-reconciliation-complete.png` reconciliation-complete 对比度可辨认 | SDPCCR-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelCompensationReconciliationViewportLightDarkScreenshots` biDomain 全过 | SDPCCR-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 compensation-pending 面板 → 点击「触发指标补偿对账完成」→ 对照 tablet/mobile light/dark 八张 compensation-pending/reconciliation-complete 截图。

## SDPCCR-02 — DevOps 场景阶段推送通道后续补偿/对账 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-compensation-pending.png`、`scenario-devops-domain-tablet-dark-compensation-pending.png`、`scenario-devops-domain-mobile-compensation-pending.png`、`scenario-devops-domain-mobile-dark-compensation-pending.png`、`scenario-devops-domain-tablet-reconciliation-complete.png`、`scenario-devops-domain-tablet-dark-reconciliation-complete.png`、`scenario-devops-domain-mobile-reconciliation-complete.png`、`scenario-devops-domain-mobile-dark-reconciliation-complete.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light compensation-pending 截图 | `scenario-devops-domain-tablet-compensation-pending.png` 存在且 compensation-pending framing 正常 | SDPCCR-02 · RESP-06 |
| 2 | tablet dark compensation-pending 截图 | `scenario-devops-domain-tablet-dark-compensation-pending.png` 存在且差异事件摘要可读 | SDPCCR-02 · VIS-05 |
| 3 | mobile light reconciliation-complete 截图 | `scenario-devops-domain-mobile-reconciliation-complete.png` 流水线 reconciliation-complete 首屏可见 | SDPCCR-02 · RESP-07 |
| 4 | mobile dark reconciliation-complete 截图 | `scenario-devops-domain-mobile-dark-reconciliation-complete.png` reconciliation-complete 对比度可辨认 | SDPCCR-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道后续补偿/对账 tablet/mobile light/dark 可见 | SDPCCR-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 compensation-pending 面板 → 点击「触发阶段补偿对账完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCR-03 — Gateway 场景端点推送通道后续补偿/对账 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-compensation-pending.png`、`scenario-gateway-domain-tablet-dark-compensation-pending.png`、`scenario-gateway-domain-mobile-compensation-pending.png`、`scenario-gateway-domain-mobile-dark-compensation-pending.png`、`scenario-gateway-domain-tablet-reconciliation-complete.png`、`scenario-gateway-domain-tablet-dark-reconciliation-complete.png`、`scenario-gateway-domain-mobile-reconciliation-complete.png`、`scenario-gateway-domain-mobile-dark-reconciliation-complete.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light compensation-pending 截图 | `scenario-gateway-domain-tablet-compensation-pending.png` 存在且 compensation-pending framing 正常 | SDPCCR-03 · RESP-06 |
| 2 | tablet dark compensation-pending 截图 | `scenario-gateway-domain-tablet-dark-compensation-pending.png` 存在且差异事件摘要可读 | SDPCCR-03 · VIS-05 |
| 3 | mobile light reconciliation-complete 截图 | `scenario-gateway-domain-mobile-reconciliation-complete.png` 端点 reconciliation-complete 首屏可见 | SDPCCR-03 · RESP-07 |
| 4 | mobile dark reconciliation-complete 截图 | `scenario-gateway-domain-mobile-dark-reconciliation-complete.png` reconciliation-complete 层级不丢失 | SDPCCR-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道后续补偿/对账 tablet/mobile light/dark 可见 | SDPCCR-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 compensation-pending 面板 → 点击「触发端点补偿对账完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCR-04 — Governance 场景审计行推送通道后续补偿/对账 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-compensation-pending.png`、`scenario-governance-domain-tablet-dark-compensation-pending.png`、`scenario-governance-domain-mobile-compensation-pending.png`、`scenario-governance-domain-mobile-dark-compensation-pending.png`、`scenario-governance-domain-tablet-reconciliation-complete.png`、`scenario-governance-domain-tablet-dark-reconciliation-complete.png`、`scenario-governance-domain-mobile-reconciliation-complete.png`、`scenario-governance-domain-mobile-dark-reconciliation-complete.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light compensation-pending 截图 | `scenario-governance-domain-tablet-compensation-pending.png` 存在且 compensation-pending framing 正常 | SDPCCR-04 · RESP-06 |
| 2 | tablet dark compensation-pending 截图 | `scenario-governance-domain-tablet-dark-compensation-pending.png` 存在且差异事件摘要可读 | SDPCCR-04 · VIS-05 |
| 3 | mobile light reconciliation-complete 截图 | `scenario-governance-domain-mobile-reconciliation-complete.png` 审计 reconciliation-complete 首屏可见 | SDPCCR-04 · RESP-07 |
| 4 | mobile dark reconciliation-complete 截图 | `scenario-governance-domain-mobile-dark-reconciliation-complete.png` reconciliation-complete 密度一致 | SDPCCR-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道后续补偿/对账 tablet/mobile light/dark 可见 | SDPCCR-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 compensation-pending 面板 → 点击「触发审计补偿对账完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCR-05 — PaaS 场景容量推送通道后续补偿/对账 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-compensation-pending.png`、`scenario-paas-domain-tablet-dark-compensation-pending.png`、`scenario-paas-domain-mobile-compensation-pending.png`、`scenario-paas-domain-mobile-dark-compensation-pending.png`、`scenario-paas-domain-tablet-reconciliation-complete.png`、`scenario-paas-domain-tablet-dark-reconciliation-complete.png`、`scenario-paas-domain-mobile-reconciliation-complete.png`、`scenario-paas-domain-mobile-dark-reconciliation-complete.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light compensation-pending 截图 | `scenario-paas-domain-tablet-compensation-pending.png` 存在且 compensation-pending framing 正常 | SDPCCR-05 · RESP-06 |
| 2 | tablet dark compensation-pending 截图 | `scenario-paas-domain-tablet-dark-compensation-pending.png` 存在且差异事件摘要可读 | SDPCCR-05 · VIS-05 |
| 3 | mobile light reconciliation-complete 截图 | `scenario-paas-domain-mobile-reconciliation-complete.png` 容量 reconciliation-complete 首屏可见 | SDPCCR-05 · RESP-07 |
| 4 | mobile dark reconciliation-complete 截图 | `scenario-paas-domain-mobile-dark-reconciliation-complete.png` reconciliation-complete 列表项可辨认 | SDPCCR-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道后续补偿/对账 tablet/mobile light/dark 可见 | SDPCCR-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 compensation-pending 面板 → 点击「触发容量补偿对账完成」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md` SDPCCR-06～10
- 推送通道后续异步韧性 前置：`scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md` SDPCAR-01～05
- 选型表：`decision-matrix.md` G120 场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCCR-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelCompensationReconciliationViewportLightDarkScreenshots`
