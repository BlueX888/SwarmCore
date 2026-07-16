# Scenario Domain Push Channel Audit Tracking Viewport Light/Dark Screenshot 评审清单

> DOCS-072 / G121 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道后续审计追踪独立截图视觉回归抽检**，确保每个场景 section 在推送通道审计追踪中态、审计追踪完成态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md`（SDPCCR-01～05）、`scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md`（SDPCAT-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCAT 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道后续审计追踪 tablet/mobile light/dark golden 对照 | SDPCAT-01 + `scenario-bi-domain-tablet-audit-tracking-pending.png` + `scenario-bi-domain-mobile-dark-audit-tracking-complete.png` |
| DevOps 场景阶段推送通道后续审计追踪 tablet/mobile light/dark golden 对照 | SDPCAT-02 + `scenario-devops-domain-tablet-audit-tracking-pending.png` + `scenario-devops-domain-mobile-dark-audit-tracking-complete.png` |
| Gateway 场景端点推送通道后续审计追踪 tablet/mobile light/dark golden 对照 | SDPCAT-03 + `scenario-gateway-domain-tablet-audit-tracking-pending.png` + `scenario-gateway-domain-mobile-dark-audit-tracking-complete.png` |
| Governance 场景审计行推送通道后续审计追踪 tablet/mobile light/dark golden 对照 | SDPCAT-04 + `scenario-governance-domain-tablet-audit-tracking-pending.png` + `scenario-governance-domain-mobile-dark-audit-tracking-complete.png` |
| PaaS 场景容量推送通道后续审计追踪 tablet/mobile light/dark golden 对照 | SDPCAT-05 + `scenario-paas-domain-tablet-audit-tracking-pending.png` + `scenario-paas-domain-mobile-dark-audit-tracking-complete.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md` SDPCCR-01～05（推送通道后续补偿/对账独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{audit-tracking-pending,audit-tracking-complete}.png` 四视口双主题推送通道后续审计追踪独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 audit-tracking-pending 与一张 audit-tracking-complete 独立截图；audit-tracking-pending 必须出现审计追踪 banner「推送通道后续审计追踪中（留痕事件排队）」与留痕事件摘要，audit-tracking-complete 必须出现审计追踪完成 banner 与「查看审计追踪详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道后续审计追踪截图出现文案裁切、审计追踪 banner 对比度不足、audit-tracking-complete banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图（G121）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图抽检行。

## SDPCAT-01 — BI 场景指标推送通道后续审计追踪 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-audit-tracking-pending.png`、`scenario-bi-domain-tablet-dark-audit-tracking-pending.png`、`scenario-bi-domain-mobile-audit-tracking-pending.png`、`scenario-bi-domain-mobile-dark-audit-tracking-pending.png`、`scenario-bi-domain-tablet-audit-tracking-complete.png`、`scenario-bi-domain-tablet-dark-audit-tracking-complete.png`、`scenario-bi-domain-mobile-audit-tracking-complete.png`、`scenario-bi-domain-mobile-dark-audit-tracking-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light audit-tracking-pending 截图 | `scenario-bi-domain-tablet-audit-tracking-pending.png` 存在且 audit-tracking-pending framing 正常 | SDPCAT-01 · RESP-06 |
| 2 | tablet dark audit-tracking-pending 截图 | `scenario-bi-domain-tablet-dark-audit-tracking-pending.png` 存在且审计追踪 banner 可读 | SDPCAT-01 · VIS-05 |
| 3 | mobile light audit-tracking-complete 截图 | `scenario-bi-domain-mobile-audit-tracking-complete.png` audit-tracking-complete banner 首屏可见 | SDPCAT-01 · RESP-07 |
| 4 | mobile dark audit-tracking-complete 截图 | `scenario-bi-domain-mobile-dark-audit-tracking-complete.png` audit-tracking-complete 对比度可辨认 | SDPCAT-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelAuditTrackingViewportLightDarkScreenshots` biDomain 全过 | SDPCAT-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 audit-tracking-pending 面板 → 点击「触发指标审计追踪完成」→ 对照 tablet/mobile light/dark 八张 audit-tracking-pending/audit-tracking-complete 截图。

## SDPCAT-02 — DevOps 场景阶段推送通道后续审计追踪 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-audit-tracking-pending.png`、`scenario-devops-domain-tablet-dark-audit-tracking-pending.png`、`scenario-devops-domain-mobile-audit-tracking-pending.png`、`scenario-devops-domain-mobile-dark-audit-tracking-pending.png`、`scenario-devops-domain-tablet-audit-tracking-complete.png`、`scenario-devops-domain-tablet-dark-audit-tracking-complete.png`、`scenario-devops-domain-mobile-audit-tracking-complete.png`、`scenario-devops-domain-mobile-dark-audit-tracking-complete.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light audit-tracking-pending 截图 | `scenario-devops-domain-tablet-audit-tracking-pending.png` 存在且 audit-tracking-pending framing 正常 | SDPCAT-02 · RESP-06 |
| 2 | tablet dark audit-tracking-pending 截图 | `scenario-devops-domain-tablet-dark-audit-tracking-pending.png` 存在且留痕事件摘要可读 | SDPCAT-02 · VIS-05 |
| 3 | mobile light audit-tracking-complete 截图 | `scenario-devops-domain-mobile-audit-tracking-complete.png` 流水线 audit-tracking-complete 首屏可见 | SDPCAT-02 · RESP-07 |
| 4 | mobile dark audit-tracking-complete 截图 | `scenario-devops-domain-mobile-dark-audit-tracking-complete.png` audit-tracking-complete 对比度可辨认 | SDPCAT-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道后续审计追踪 tablet/mobile light/dark 可见 | SDPCAT-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 audit-tracking-pending 面板 → 点击「触发阶段审计追踪完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCAT-03 — Gateway 场景端点推送通道后续审计追踪 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-audit-tracking-pending.png`、`scenario-gateway-domain-tablet-dark-audit-tracking-pending.png`、`scenario-gateway-domain-mobile-audit-tracking-pending.png`、`scenario-gateway-domain-mobile-dark-audit-tracking-pending.png`、`scenario-gateway-domain-tablet-audit-tracking-complete.png`、`scenario-gateway-domain-tablet-dark-audit-tracking-complete.png`、`scenario-gateway-domain-mobile-audit-tracking-complete.png`、`scenario-gateway-domain-mobile-dark-audit-tracking-complete.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light audit-tracking-pending 截图 | `scenario-gateway-domain-tablet-audit-tracking-pending.png` 存在且 audit-tracking-pending framing 正常 | SDPCAT-03 · RESP-06 |
| 2 | tablet dark audit-tracking-pending 截图 | `scenario-gateway-domain-tablet-dark-audit-tracking-pending.png` 存在且留痕事件摘要可读 | SDPCAT-03 · VIS-05 |
| 3 | mobile light audit-tracking-complete 截图 | `scenario-gateway-domain-mobile-audit-tracking-complete.png` 端点 audit-tracking-complete 首屏可见 | SDPCAT-03 · RESP-07 |
| 4 | mobile dark audit-tracking-complete 截图 | `scenario-gateway-domain-mobile-dark-audit-tracking-complete.png` audit-tracking-complete 层级不丢失 | SDPCAT-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道后续审计追踪 tablet/mobile light/dark 可见 | SDPCAT-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 audit-tracking-pending 面板 → 点击「触发端点审计追踪完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCAT-04 — Governance 场景审计行推送通道后续审计追踪 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-audit-tracking-pending.png`、`scenario-governance-domain-tablet-dark-audit-tracking-pending.png`、`scenario-governance-domain-mobile-audit-tracking-pending.png`、`scenario-governance-domain-mobile-dark-audit-tracking-pending.png`、`scenario-governance-domain-tablet-audit-tracking-complete.png`、`scenario-governance-domain-tablet-dark-audit-tracking-complete.png`、`scenario-governance-domain-mobile-audit-tracking-complete.png`、`scenario-governance-domain-mobile-dark-audit-tracking-complete.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light audit-tracking-pending 截图 | `scenario-governance-domain-tablet-audit-tracking-pending.png` 存在且 audit-tracking-pending framing 正常 | SDPCAT-04 · RESP-06 |
| 2 | tablet dark audit-tracking-pending 截图 | `scenario-governance-domain-tablet-dark-audit-tracking-pending.png` 存在且留痕事件摘要可读 | SDPCAT-04 · VIS-05 |
| 3 | mobile light audit-tracking-complete 截图 | `scenario-governance-domain-mobile-audit-tracking-complete.png` 审计 audit-tracking-complete 首屏可见 | SDPCAT-04 · RESP-07 |
| 4 | mobile dark audit-tracking-complete 截图 | `scenario-governance-domain-mobile-dark-audit-tracking-complete.png` audit-tracking-complete 密度一致 | SDPCAT-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道后续审计追踪 tablet/mobile light/dark 可见 | SDPCAT-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 audit-tracking-pending 面板 → 点击「触发合规审计追踪完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCAT-05 — PaaS 场景容量推送通道后续审计追踪 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-audit-tracking-pending.png`、`scenario-paas-domain-tablet-dark-audit-tracking-pending.png`、`scenario-paas-domain-mobile-audit-tracking-pending.png`、`scenario-paas-domain-mobile-dark-audit-tracking-pending.png`、`scenario-paas-domain-tablet-audit-tracking-complete.png`、`scenario-paas-domain-tablet-dark-audit-tracking-complete.png`、`scenario-paas-domain-mobile-audit-tracking-complete.png`、`scenario-paas-domain-mobile-dark-audit-tracking-complete.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light audit-tracking-pending 截图 | `scenario-paas-domain-tablet-audit-tracking-pending.png` 存在且 audit-tracking-pending framing 正常 | SDPCAT-05 · RESP-06 |
| 2 | tablet dark audit-tracking-pending 截图 | `scenario-paas-domain-tablet-dark-audit-tracking-pending.png` 存在且留痕事件摘要可读 | SDPCAT-05 · VIS-05 |
| 3 | mobile light audit-tracking-complete 截图 | `scenario-paas-domain-mobile-audit-tracking-complete.png` 容量 audit-tracking-complete 首屏可见 | SDPCAT-05 · RESP-07 |
| 4 | mobile dark audit-tracking-complete 截图 | `scenario-paas-domain-mobile-dark-audit-tracking-complete.png` audit-tracking-complete 列表项可辨认 | SDPCAT-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道后续审计追踪 tablet/mobile light/dark 可见 | SDPCAT-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 audit-tracking-pending 面板 → 点击「触发容量审计追踪完成」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md` SDPCAT-06～10
- 推送通道后续补偿/对账 前置：`scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md` SDPCCR-01～05
- 选型表：`decision-matrix.md` G121 场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCAT-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelAuditTrackingViewportLightDarkScreenshots`
