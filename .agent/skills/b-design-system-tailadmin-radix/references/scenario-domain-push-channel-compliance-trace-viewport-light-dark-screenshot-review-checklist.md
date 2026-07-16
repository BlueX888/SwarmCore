# Scenario Domain Push Channel Compliance Trace Viewport Light/Dark Screenshot 评审清单

> DOCS-073 / G122 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道后续合规留痕独立截图视觉回归抽检**，确保每个场景 section 在推送通道合规留痕中态、合规留痕完成态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md`（SDPCAT-01～05）、`scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md`（SDPCCT-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCCT 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道后续合规留痕 tablet/mobile light/dark golden 对照 | SDPCCT-01 + `scenario-bi-domain-tablet-compliance-trace-pending.png` + `scenario-bi-domain-mobile-dark-compliance-trace-complete.png` |
| DevOps 场景阶段推送通道后续合规留痕 tablet/mobile light/dark golden 对照 | SDPCCT-02 + `scenario-devops-domain-tablet-compliance-trace-pending.png` + `scenario-devops-domain-mobile-dark-compliance-trace-complete.png` |
| Gateway 场景端点推送通道后续合规留痕 tablet/mobile light/dark golden 对照 | SDPCCT-03 + `scenario-gateway-domain-tablet-compliance-trace-pending.png` + `scenario-gateway-domain-mobile-dark-compliance-trace-complete.png` |
| Governance 场景审计行推送通道后续合规留痕 tablet/mobile light/dark golden 对照 | SDPCCT-04 + `scenario-governance-domain-tablet-compliance-trace-pending.png` + `scenario-governance-domain-mobile-dark-compliance-trace-complete.png` |
| PaaS 场景容量推送通道后续合规留痕 tablet/mobile light/dark golden 对照 | SDPCCT-05 + `scenario-paas-domain-tablet-compliance-trace-pending.png` + `scenario-paas-domain-mobile-dark-compliance-trace-complete.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md` SDPCAT-01～05（推送通道后续审计追踪独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{compliance-trace-pending,compliance-trace-complete}.png` 四视口双主题推送通道后续合规留痕独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 compliance-trace-pending 与一张 compliance-trace-complete 独立截图；compliance-trace-pending 必须出现合规留痕 banner「推送通道后续合规留痕中（合规事件排队）」与合规事件摘要，compliance-trace-complete 必须出现合规留痕完成 banner 与「查看合规留痕详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道后续合规留痕截图出现文案裁切、合规留痕 banner 对比度不足、compliance-trace-complete banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图（G122）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图抽检行。

## SDPCCT-01 — BI 场景指标推送通道后续合规留痕 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-compliance-trace-pending.png`、`scenario-bi-domain-tablet-dark-compliance-trace-pending.png`、`scenario-bi-domain-mobile-compliance-trace-pending.png`、`scenario-bi-domain-mobile-dark-compliance-trace-pending.png`、`scenario-bi-domain-tablet-compliance-trace-complete.png`、`scenario-bi-domain-tablet-dark-compliance-trace-complete.png`、`scenario-bi-domain-mobile-compliance-trace-complete.png`、`scenario-bi-domain-mobile-dark-compliance-trace-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light compliance-trace-pending 截图 | `scenario-bi-domain-tablet-compliance-trace-pending.png` 存在且 compliance-trace-pending framing 正常 | SDPCCT-01 · RESP-06 |
| 2 | tablet dark compliance-trace-pending 截图 | `scenario-bi-domain-tablet-dark-compliance-trace-pending.png` 存在且合规留痕 banner 可读 | SDPCCT-01 · VIS-05 |
| 3 | mobile light compliance-trace-complete 截图 | `scenario-bi-domain-mobile-compliance-trace-complete.png` compliance-trace-complete banner 首屏可见 | SDPCCT-01 · RESP-07 |
| 4 | mobile dark compliance-trace-complete 截图 | `scenario-bi-domain-mobile-dark-compliance-trace-complete.png` compliance-trace-complete 对比度可辨认 | SDPCCT-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelComplianceTraceViewportLightDarkScreenshots` biDomain 全过 | SDPCCT-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 compliance-trace-pending 面板 → 点击「触发指标合规留痕完成」→ 对照 tablet/mobile light/dark 八张 compliance-trace-pending/compliance-trace-complete 截图。

## SDPCCT-02 — DevOps 场景阶段推送通道后续合规留痕 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-compliance-trace-pending.png`、`scenario-devops-domain-tablet-dark-compliance-trace-pending.png`、`scenario-devops-domain-mobile-compliance-trace-pending.png`、`scenario-devops-domain-mobile-dark-compliance-trace-pending.png`、`scenario-devops-domain-tablet-compliance-trace-complete.png`、`scenario-devops-domain-tablet-dark-compliance-trace-complete.png`、`scenario-devops-domain-mobile-compliance-trace-complete.png`、`scenario-devops-domain-mobile-dark-compliance-trace-complete.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light compliance-trace-pending 截图 | `scenario-devops-domain-tablet-compliance-trace-pending.png` 存在且 compliance-trace-pending framing 正常 | SDPCCT-02 · RESP-06 |
| 2 | tablet dark compliance-trace-pending 截图 | `scenario-devops-domain-tablet-dark-compliance-trace-pending.png` 存在且合规事件摘要可读 | SDPCCT-02 · VIS-05 |
| 3 | mobile light compliance-trace-complete 截图 | `scenario-devops-domain-mobile-compliance-trace-complete.png` 流水线 compliance-trace-complete 首屏可见 | SDPCCT-02 · RESP-07 |
| 4 | mobile dark compliance-trace-complete 截图 | `scenario-devops-domain-mobile-dark-compliance-trace-complete.png` compliance-trace-complete 对比度可辨认 | SDPCCT-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道后续合规留痕 tablet/mobile light/dark 可见 | SDPCCT-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 compliance-trace-pending 面板 → 点击「触发阶段合规留痕完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCT-03 — Gateway 场景端点推送通道后续合规留痕 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-compliance-trace-pending.png`、`scenario-gateway-domain-tablet-dark-compliance-trace-pending.png`、`scenario-gateway-domain-mobile-compliance-trace-pending.png`、`scenario-gateway-domain-mobile-dark-compliance-trace-pending.png`、`scenario-gateway-domain-tablet-compliance-trace-complete.png`、`scenario-gateway-domain-tablet-dark-compliance-trace-complete.png`、`scenario-gateway-domain-mobile-compliance-trace-complete.png`、`scenario-gateway-domain-mobile-dark-compliance-trace-complete.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light compliance-trace-pending 截图 | `scenario-gateway-domain-tablet-compliance-trace-pending.png` 存在且 compliance-trace-pending framing 正常 | SDPCCT-03 · RESP-06 |
| 2 | tablet dark compliance-trace-pending 截图 | `scenario-gateway-domain-tablet-dark-compliance-trace-pending.png` 存在且合规事件摘要可读 | SDPCCT-03 · VIS-05 |
| 3 | mobile light compliance-trace-complete 截图 | `scenario-gateway-domain-mobile-compliance-trace-complete.png` 端点 compliance-trace-complete 首屏可见 | SDPCCT-03 · RESP-07 |
| 4 | mobile dark compliance-trace-complete 截图 | `scenario-gateway-domain-mobile-dark-compliance-trace-complete.png` compliance-trace-complete 层级不丢失 | SDPCCT-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道后续合规留痕 tablet/mobile light/dark 可见 | SDPCCT-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 compliance-trace-pending 面板 → 点击「触发端点合规留痕完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCT-04 — Governance 场景审计行推送通道后续合规留痕 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-compliance-trace-pending.png`、`scenario-governance-domain-tablet-dark-compliance-trace-pending.png`、`scenario-governance-domain-mobile-compliance-trace-pending.png`、`scenario-governance-domain-mobile-dark-compliance-trace-pending.png`、`scenario-governance-domain-tablet-compliance-trace-complete.png`、`scenario-governance-domain-tablet-dark-compliance-trace-complete.png`、`scenario-governance-domain-mobile-compliance-trace-complete.png`、`scenario-governance-domain-mobile-dark-compliance-trace-complete.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light compliance-trace-pending 截图 | `scenario-governance-domain-tablet-compliance-trace-pending.png` 存在且 compliance-trace-pending framing 正常 | SDPCCT-04 · RESP-06 |
| 2 | tablet dark compliance-trace-pending 截图 | `scenario-governance-domain-tablet-dark-compliance-trace-pending.png` 存在且合规事件摘要可读 | SDPCCT-04 · VIS-05 |
| 3 | mobile light compliance-trace-complete 截图 | `scenario-governance-domain-mobile-compliance-trace-complete.png` 审计 compliance-trace-complete 首屏可见 | SDPCCT-04 · RESP-07 |
| 4 | mobile dark compliance-trace-complete 截图 | `scenario-governance-domain-mobile-dark-compliance-trace-complete.png` compliance-trace-complete 密度一致 | SDPCCT-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道后续合规留痕 tablet/mobile light/dark 可见 | SDPCCT-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 compliance-trace-pending 面板 → 点击「触发合规合规留痕完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCT-05 — PaaS 场景容量推送通道后续合规留痕 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-compliance-trace-pending.png`、`scenario-paas-domain-tablet-dark-compliance-trace-pending.png`、`scenario-paas-domain-mobile-compliance-trace-pending.png`、`scenario-paas-domain-mobile-dark-compliance-trace-pending.png`、`scenario-paas-domain-tablet-compliance-trace-complete.png`、`scenario-paas-domain-tablet-dark-compliance-trace-complete.png`、`scenario-paas-domain-mobile-compliance-trace-complete.png`、`scenario-paas-domain-mobile-dark-compliance-trace-complete.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light compliance-trace-pending 截图 | `scenario-paas-domain-tablet-compliance-trace-pending.png` 存在且 compliance-trace-pending framing 正常 | SDPCCT-05 · RESP-06 |
| 2 | tablet dark compliance-trace-pending 截图 | `scenario-paas-domain-tablet-dark-compliance-trace-pending.png` 存在且合规事件摘要可读 | SDPCCT-05 · VIS-05 |
| 3 | mobile light compliance-trace-complete 截图 | `scenario-paas-domain-mobile-compliance-trace-complete.png` 容量 compliance-trace-complete 首屏可见 | SDPCCT-05 · RESP-07 |
| 4 | mobile dark compliance-trace-complete 截图 | `scenario-paas-domain-mobile-dark-compliance-trace-complete.png` compliance-trace-complete 列表项可辨认 | SDPCCT-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道后续合规留痕 tablet/mobile light/dark 可见 | SDPCCT-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 compliance-trace-pending 面板 → 点击「触发容量合规留痕完成」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md` SDPCCT-06～10
- 推送通道后续审计追踪 前置：`scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md` SDPCCR-01～05
- 选型表：`decision-matrix.md` G122 场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCCT-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelComplianceTraceViewportLightDarkScreenshots`
