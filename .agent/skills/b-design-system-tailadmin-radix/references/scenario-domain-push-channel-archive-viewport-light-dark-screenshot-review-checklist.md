# Scenario Domain Push Channel Archive Viewport Light/Dark Screenshot 评审清单

> DOCS-074 / G123 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道后续归档独立截图视觉回归抽检**，确保每个场景 section 在推送通道归档中态、归档完成态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md`（SDPCARCH-01～05）、`scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md`（SDPCARCH-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续归档 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCARCH 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道后续归档 tablet/mobile light/dark golden 对照 | SDPCARCH-01 + `scenario-bi-domain-tablet-channel-archive-pending.png` + `scenario-bi-domain-mobile-dark-channel-archive-complete.png` |
| DevOps 场景阶段推送通道后续归档 tablet/mobile light/dark golden 对照 | SDPCARCH-02 + `scenario-devops-domain-tablet-channel-archive-pending.png` + `scenario-devops-domain-mobile-dark-channel-archive-complete.png` |
| Gateway 场景端点推送通道后续归档 tablet/mobile light/dark golden 对照 | SDPCARCH-03 + `scenario-gateway-domain-tablet-channel-archive-pending.png` + `scenario-gateway-domain-mobile-dark-channel-archive-complete.png` |
| Governance 场景审计行推送通道后续归档 tablet/mobile light/dark golden 对照 | SDPCARCH-04 + `scenario-governance-domain-tablet-channel-archive-pending.png` + `scenario-governance-domain-mobile-dark-channel-archive-complete.png` |
| PaaS 场景容量推送通道后续归档 tablet/mobile light/dark golden 对照 | SDPCARCH-05 + `scenario-paas-domain-tablet-channel-archive-pending.png` + `scenario-paas-domain-mobile-dark-channel-archive-complete.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md` SDPCCT-01～05（推送通道后续合规留痕独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-archive-pending,channel-archive-complete}.png` 四视口双主题推送通道后续归档独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 channel-archive-pending 与一张 channel-archive-complete 独立截图；channel-archive-pending 必须出现归档 banner「推送通道后续归档中（历史事件打包）」与历史事件摘要，channel-archive-complete 必须出现归档完成 banner 与「查看归档详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道后续归档截图出现文案裁切、归档 banner 对比度不足、channel-archive-complete banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续归档 tablet/mobile light/dark 独立截图（G123）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续归档 tablet/mobile light/dark 独立截图抽检行。

## SDPCARCH-01 — BI 场景指标推送通道后续归档 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-channel-archive-pending.png`、`scenario-bi-domain-tablet-dark-channel-archive-pending.png`、`scenario-bi-domain-mobile-channel-archive-pending.png`、`scenario-bi-domain-mobile-dark-channel-archive-pending.png`、`scenario-bi-domain-tablet-channel-archive-complete.png`、`scenario-bi-domain-tablet-dark-channel-archive-complete.png`、`scenario-bi-domain-mobile-channel-archive-complete.png`、`scenario-bi-domain-mobile-dark-channel-archive-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-archive-pending 截图 | `scenario-bi-domain-tablet-channel-archive-pending.png` 存在且 channel-archive-pending framing 正常 | SDPCARCH-01 · RESP-06 |
| 2 | tablet dark channel-archive-pending 截图 | `scenario-bi-domain-tablet-dark-channel-archive-pending.png` 存在且归档 banner 可读 | SDPCARCH-01 · VIS-05 |
| 3 | mobile light channel-archive-complete 截图 | `scenario-bi-domain-mobile-channel-archive-complete.png` channel-archive-complete banner 首屏可见 | SDPCARCH-01 · RESP-07 |
| 4 | mobile dark channel-archive-complete 截图 | `scenario-bi-domain-mobile-dark-channel-archive-complete.png` channel-archive-complete 对比度可辨认 | SDPCARCH-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelArchiveViewportLightDarkScreenshots` biDomain 全过 | SDPCARCH-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 channel-archive-pending 面板 → 点击「触发指标归档完成」→ 对照 tablet/mobile light/dark 八张 channel-archive-pending/channel-archive-complete 截图。

## SDPCARCH-02 — DevOps 场景阶段推送通道后续归档 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-channel-archive-pending.png`、`scenario-devops-domain-tablet-dark-channel-archive-pending.png`、`scenario-devops-domain-mobile-channel-archive-pending.png`、`scenario-devops-domain-mobile-dark-channel-archive-pending.png`、`scenario-devops-domain-tablet-channel-archive-complete.png`、`scenario-devops-domain-tablet-dark-channel-archive-complete.png`、`scenario-devops-domain-mobile-channel-archive-complete.png`、`scenario-devops-domain-mobile-dark-channel-archive-complete.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-archive-pending 截图 | `scenario-devops-domain-tablet-channel-archive-pending.png` 存在且 channel-archive-pending framing 正常 | SDPCARCH-02 · RESP-06 |
| 2 | tablet dark channel-archive-pending 截图 | `scenario-devops-domain-tablet-dark-channel-archive-pending.png` 存在且历史事件摘要可读 | SDPCARCH-02 · VIS-05 |
| 3 | mobile light channel-archive-complete 截图 | `scenario-devops-domain-mobile-channel-archive-complete.png` 流水线 channel-archive-complete 首屏可见 | SDPCARCH-02 · RESP-07 |
| 4 | mobile dark channel-archive-complete 截图 | `scenario-devops-domain-mobile-dark-channel-archive-complete.png` channel-archive-complete 对比度可辨认 | SDPCARCH-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道后续归档 tablet/mobile light/dark 可见 | SDPCARCH-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 channel-archive-pending 面板 → 点击「触发阶段归档完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCARCH-03 — Gateway 场景端点推送通道后续归档 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-channel-archive-pending.png`、`scenario-gateway-domain-tablet-dark-channel-archive-pending.png`、`scenario-gateway-domain-mobile-channel-archive-pending.png`、`scenario-gateway-domain-mobile-dark-channel-archive-pending.png`、`scenario-gateway-domain-tablet-channel-archive-complete.png`、`scenario-gateway-domain-tablet-dark-channel-archive-complete.png`、`scenario-gateway-domain-mobile-channel-archive-complete.png`、`scenario-gateway-domain-mobile-dark-channel-archive-complete.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-archive-pending 截图 | `scenario-gateway-domain-tablet-channel-archive-pending.png` 存在且 channel-archive-pending framing 正常 | SDPCARCH-03 · RESP-06 |
| 2 | tablet dark channel-archive-pending 截图 | `scenario-gateway-domain-tablet-dark-channel-archive-pending.png` 存在且历史事件摘要可读 | SDPCARCH-03 · VIS-05 |
| 3 | mobile light channel-archive-complete 截图 | `scenario-gateway-domain-mobile-channel-archive-complete.png` 端点 channel-archive-complete 首屏可见 | SDPCARCH-03 · RESP-07 |
| 4 | mobile dark channel-archive-complete 截图 | `scenario-gateway-domain-mobile-dark-channel-archive-complete.png` channel-archive-complete 层级不丢失 | SDPCARCH-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道后续归档 tablet/mobile light/dark 可见 | SDPCARCH-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 channel-archive-pending 面板 → 点击「触发端点归档完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCARCH-04 — Governance 场景审计行推送通道后续归档 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-channel-archive-pending.png`、`scenario-governance-domain-tablet-dark-channel-archive-pending.png`、`scenario-governance-domain-mobile-channel-archive-pending.png`、`scenario-governance-domain-mobile-dark-channel-archive-pending.png`、`scenario-governance-domain-tablet-channel-archive-complete.png`、`scenario-governance-domain-tablet-dark-channel-archive-complete.png`、`scenario-governance-domain-mobile-channel-archive-complete.png`、`scenario-governance-domain-mobile-dark-channel-archive-complete.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-archive-pending 截图 | `scenario-governance-domain-tablet-channel-archive-pending.png` 存在且 channel-archive-pending framing 正常 | SDPCARCH-04 · RESP-06 |
| 2 | tablet dark channel-archive-pending 截图 | `scenario-governance-domain-tablet-dark-channel-archive-pending.png` 存在且历史事件摘要可读 | SDPCARCH-04 · VIS-05 |
| 3 | mobile light channel-archive-complete 截图 | `scenario-governance-domain-mobile-channel-archive-complete.png` 审计 channel-archive-complete 首屏可见 | SDPCARCH-04 · RESP-07 |
| 4 | mobile dark channel-archive-complete 截图 | `scenario-governance-domain-mobile-dark-channel-archive-complete.png` channel-archive-complete 密度一致 | SDPCARCH-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道后续归档 tablet/mobile light/dark 可见 | SDPCARCH-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 channel-archive-pending 面板 → 点击「触发合规归档完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCARCH-05 — PaaS 场景容量推送通道后续归档 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-channel-archive-pending.png`、`scenario-paas-domain-tablet-dark-channel-archive-pending.png`、`scenario-paas-domain-mobile-channel-archive-pending.png`、`scenario-paas-domain-mobile-dark-channel-archive-pending.png`、`scenario-paas-domain-tablet-channel-archive-complete.png`、`scenario-paas-domain-tablet-dark-channel-archive-complete.png`、`scenario-paas-domain-mobile-channel-archive-complete.png`、`scenario-paas-domain-mobile-dark-channel-archive-complete.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-archive-pending 截图 | `scenario-paas-domain-tablet-channel-archive-pending.png` 存在且 channel-archive-pending framing 正常 | SDPCARCH-05 · RESP-06 |
| 2 | tablet dark channel-archive-pending 截图 | `scenario-paas-domain-tablet-dark-channel-archive-pending.png` 存在且历史事件摘要可读 | SDPCARCH-05 · VIS-05 |
| 3 | mobile light channel-archive-complete 截图 | `scenario-paas-domain-mobile-channel-archive-complete.png` 容量 channel-archive-complete 首屏可见 | SDPCARCH-05 · RESP-07 |
| 4 | mobile dark channel-archive-complete 截图 | `scenario-paas-domain-mobile-dark-channel-archive-complete.png` channel-archive-complete 列表项可辨认 | SDPCARCH-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道后续归档 tablet/mobile light/dark 可见 | SDPCARCH-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 channel-archive-pending 面板 → 点击「触发容量归档完成」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-channel-archive-viewport-light-dark-screenshot-review-checklist.md` SDPCARCH-06～10
- 推送通道后续审计追踪 前置：`scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md` SDPCCR-01～05
- 选型表：`decision-matrix.md` G123 场景域推送通道后续归档 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCARCH-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelArchiveViewportLightDarkScreenshots`
