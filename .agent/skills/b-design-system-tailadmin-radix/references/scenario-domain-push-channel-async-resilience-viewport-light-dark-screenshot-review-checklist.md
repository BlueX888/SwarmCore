# Scenario Domain Push Channel Async Resilience Viewport Light/Dark Screenshot 评审清单

> DOCS-070 / G119 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道后续异步韧性独立截图视觉回归抽检**，确保每个场景 section 在推送通道异步韧性监测态、异步韧性恢复完成态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md`（SDPCSCIR-01～05）、`scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md`（SDPCAR-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCAR 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道后续异步韧性 tablet/mobile light/dark golden 对照 | SDPCAR-01 + `scenario-bi-domain-tablet-async-pending.png` + `scenario-bi-domain-mobile-dark-async-recovered.png` |
| DevOps 场景阶段推送通道后续异步韧性 tablet/mobile light/dark golden 对照 | SDPCAR-02 + `scenario-devops-domain-tablet-async-pending.png` + `scenario-devops-domain-mobile-dark-async-recovered.png` |
| Gateway 场景端点推送通道后续异步韧性 tablet/mobile light/dark golden 对照 | SDPCAR-03 + `scenario-gateway-domain-tablet-async-pending.png` + `scenario-gateway-domain-mobile-dark-async-recovered.png` |
| Governance 场景审计行推送通道后续异步韧性 tablet/mobile light/dark golden 对照 | SDPCAR-04 + `scenario-governance-domain-tablet-async-pending.png` + `scenario-governance-domain-mobile-dark-async-recovered.png` |
| PaaS 场景容量推送通道后续异步韧性 tablet/mobile light/dark golden 对照 | SDPCAR-05 + `scenario-paas-domain-tablet-async-pending.png` + `scenario-paas-domain-mobile-dark-async-recovered.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md` SDPCSCIR-01～05（推送通道订阅确认/幂等重放独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{async-pending,async-recovered}.png` 四视口双主题推送通道后续异步韧性独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 async-pending 与一张 async-recovered 独立截图；async-pending 必须出现异步韧性监测 banner「推送通道后续异步韧性监测中（重试队列排队）」与重试队列摘要，async-recovered 必须出现异步韧性恢复完成 banner 与「查看异步韧性恢复详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道后续异步韧性截图出现文案裁切、异步韧性监测 banner 对比度不足、async-recovered banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图（G119）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图抽检行。

## SDPCAR-01 — BI 场景指标推送通道后续异步韧性 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-async-pending.png`、`scenario-bi-domain-tablet-dark-async-pending.png`、`scenario-bi-domain-mobile-async-pending.png`、`scenario-bi-domain-mobile-dark-async-pending.png`、`scenario-bi-domain-tablet-async-recovered.png`、`scenario-bi-domain-tablet-dark-async-recovered.png`、`scenario-bi-domain-mobile-async-recovered.png`、`scenario-bi-domain-mobile-dark-async-recovered.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light async-pending 截图 | `scenario-bi-domain-tablet-async-pending.png` 存在且 async-pending framing 正常 | SDPCAR-01 · RESP-06 |
| 2 | tablet dark async-pending 截图 | `scenario-bi-domain-tablet-dark-async-pending.png` 存在且异步韧性监测 banner 可读 | SDPCAR-01 · VIS-05 |
| 3 | mobile light async-recovered 截图 | `scenario-bi-domain-mobile-async-recovered.png` async-recovered banner 首屏可见 | SDPCAR-01 · RESP-07 |
| 4 | mobile dark async-recovered 截图 | `scenario-bi-domain-mobile-dark-async-recovered.png` async-recovered 对比度可辨认 | SDPCAR-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelAsyncResilienceViewportLightDarkScreenshots` biDomain 全过 | SDPCAR-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 async-pending 面板 → 点击「触发指标异步韧性恢复」→ 对照 tablet/mobile light/dark 八张 async-pending/async-recovered 截图。

## SDPCAR-02 — DevOps 场景阶段推送通道后续异步韧性 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-async-pending.png`、`scenario-devops-domain-tablet-dark-async-pending.png`、`scenario-devops-domain-mobile-async-pending.png`、`scenario-devops-domain-mobile-dark-async-pending.png`、`scenario-devops-domain-tablet-async-recovered.png`、`scenario-devops-domain-tablet-dark-async-recovered.png`、`scenario-devops-domain-mobile-async-recovered.png`、`scenario-devops-domain-mobile-dark-async-recovered.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light async-pending 截图 | `scenario-devops-domain-tablet-async-pending.png` 存在且 async-pending framing 正常 | SDPCAR-02 · RESP-06 |
| 2 | tablet dark async-pending 截图 | `scenario-devops-domain-tablet-dark-async-pending.png` 存在且重试队列摘要可读 | SDPCAR-02 · VIS-05 |
| 3 | mobile light async-recovered 截图 | `scenario-devops-domain-mobile-async-recovered.png` 流水线 async-recovered 首屏可见 | SDPCAR-02 · RESP-07 |
| 4 | mobile dark async-recovered 截图 | `scenario-devops-domain-mobile-dark-async-recovered.png` async-recovered 对比度可辨认 | SDPCAR-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道后续异步韧性 tablet/mobile light/dark 可见 | SDPCAR-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 async-pending 面板 → 点击「触发阶段异步韧性恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCAR-03 — Gateway 场景端点推送通道后续异步韧性 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-async-pending.png`、`scenario-gateway-domain-tablet-dark-async-pending.png`、`scenario-gateway-domain-mobile-async-pending.png`、`scenario-gateway-domain-mobile-dark-async-pending.png`、`scenario-gateway-domain-tablet-async-recovered.png`、`scenario-gateway-domain-tablet-dark-async-recovered.png`、`scenario-gateway-domain-mobile-async-recovered.png`、`scenario-gateway-domain-mobile-dark-async-recovered.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light async-pending 截图 | `scenario-gateway-domain-tablet-async-pending.png` 存在且 async-pending framing 正常 | SDPCAR-03 · RESP-06 |
| 2 | tablet dark async-pending 截图 | `scenario-gateway-domain-tablet-dark-async-pending.png` 存在且重试队列摘要可读 | SDPCAR-03 · VIS-05 |
| 3 | mobile light async-recovered 截图 | `scenario-gateway-domain-mobile-async-recovered.png` 端点 async-recovered 首屏可见 | SDPCAR-03 · RESP-07 |
| 4 | mobile dark async-recovered 截图 | `scenario-gateway-domain-mobile-dark-async-recovered.png` async-recovered 层级不丢失 | SDPCAR-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道后续异步韧性 tablet/mobile light/dark 可见 | SDPCAR-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 async-pending 面板 → 点击「触发端点异步韧性恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCAR-04 — Governance 场景审计行推送通道后续异步韧性 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-async-pending.png`、`scenario-governance-domain-tablet-dark-async-pending.png`、`scenario-governance-domain-mobile-async-pending.png`、`scenario-governance-domain-mobile-dark-async-pending.png`、`scenario-governance-domain-tablet-async-recovered.png`、`scenario-governance-domain-tablet-dark-async-recovered.png`、`scenario-governance-domain-mobile-async-recovered.png`、`scenario-governance-domain-mobile-dark-async-recovered.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light async-pending 截图 | `scenario-governance-domain-tablet-async-pending.png` 存在且 async-pending framing 正常 | SDPCAR-04 · RESP-06 |
| 2 | tablet dark async-pending 截图 | `scenario-governance-domain-tablet-dark-async-pending.png` 存在且重试队列摘要可读 | SDPCAR-04 · VIS-05 |
| 3 | mobile light async-recovered 截图 | `scenario-governance-domain-mobile-async-recovered.png` 审计 async-recovered 首屏可见 | SDPCAR-04 · RESP-07 |
| 4 | mobile dark async-recovered 截图 | `scenario-governance-domain-mobile-dark-async-recovered.png` async-recovered 密度一致 | SDPCAR-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道后续异步韧性 tablet/mobile light/dark 可见 | SDPCAR-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 async-pending 面板 → 点击「触发审计异步韧性恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCAR-05 — PaaS 场景容量推送通道后续异步韧性 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-async-pending.png`、`scenario-paas-domain-tablet-dark-async-pending.png`、`scenario-paas-domain-mobile-async-pending.png`、`scenario-paas-domain-mobile-dark-async-pending.png`、`scenario-paas-domain-tablet-async-recovered.png`、`scenario-paas-domain-tablet-dark-async-recovered.png`、`scenario-paas-domain-mobile-async-recovered.png`、`scenario-paas-domain-mobile-dark-async-recovered.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light async-pending 截图 | `scenario-paas-domain-tablet-async-pending.png` 存在且 async-pending framing 正常 | SDPCAR-05 · RESP-06 |
| 2 | tablet dark async-pending 截图 | `scenario-paas-domain-tablet-dark-async-pending.png` 存在且重试队列摘要可读 | SDPCAR-05 · VIS-05 |
| 3 | mobile light async-recovered 截图 | `scenario-paas-domain-mobile-async-recovered.png` 容量 async-recovered 首屏可见 | SDPCAR-05 · RESP-07 |
| 4 | mobile dark async-recovered 截图 | `scenario-paas-domain-mobile-dark-async-recovered.png` async-recovered 列表项可辨认 | SDPCAR-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道后续异步韧性 tablet/mobile light/dark 可见 | SDPCAR-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 async-pending 面板 → 点击「触发容量异步韧性恢复」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md` SDPCAR-06～10
- 推送通道重试/死信队列 前置：`scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md` SDPCSCIR-01～05
- 选型表：`decision-matrix.md` G119 场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCAR-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelAsyncResilienceViewportLightDarkScreenshots`
