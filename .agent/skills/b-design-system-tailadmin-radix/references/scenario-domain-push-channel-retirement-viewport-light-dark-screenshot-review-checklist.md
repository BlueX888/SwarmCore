# Scenario Domain Push Channel Retirement Viewport Light/Dark Screenshot 评审清单

> DOCS-076 / G125 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道后续退役独立截图视觉回归抽检**，确保每个场景 section 在推送通道退役中态、退役完成态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md`（SDPCRET-01～05）、`scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md`（SDPCRET-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续退役 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCRET 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道后续退役 tablet/mobile light/dark golden 对照 | SDPCRET-01 + `scenario-bi-domain-tablet-channel-retirement-pending.png` + `scenario-bi-domain-mobile-dark-channel-retirement-complete.png` |
| DevOps 场景阶段推送通道后续退役 tablet/mobile light/dark golden 对照 | SDPCRET-02 + `scenario-devops-domain-tablet-channel-retirement-pending.png` + `scenario-devops-domain-mobile-dark-channel-retirement-complete.png` |
| Gateway 场景端点推送通道后续退役 tablet/mobile light/dark golden 对照 | SDPCRET-03 + `scenario-gateway-domain-tablet-channel-retirement-pending.png` + `scenario-gateway-domain-mobile-dark-channel-retirement-complete.png` |
| Governance 场景审计行推送通道后续退役 tablet/mobile light/dark golden 对照 | SDPCRET-04 + `scenario-governance-domain-tablet-channel-retirement-pending.png` + `scenario-governance-domain-mobile-dark-channel-retirement-complete.png` |
| PaaS 场景容量推送通道后续退役 tablet/mobile light/dark golden 对照 | SDPCRET-05 + `scenario-paas-domain-tablet-channel-retirement-pending.png` + `scenario-paas-domain-mobile-dark-channel-retirement-complete.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md` SDPCLF-01～05（推送通道后续生命周期独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-retirement-pending,channel-retirement-complete}.png` 四视口双主题推送通道后续退役独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 channel-retirement-pending 与一张 channel-retirement-complete 独立截图；channel-retirement-pending 必须出现退役 banner「推送通道后续退役中（生命周期闭合后回收）」与退役摘要，channel-retirement-complete 必须出现退役完成 banner「退役已完成，推送通道已从路由表移除，历史订阅已归档」与「查看退役详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道后续退役截图出现文案裁切、退役 banner 对比度不足、channel-retirement-complete banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续退役 tablet/mobile light/dark 独立截图（G125）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续退役 tablet/mobile light/dark 独立截图抽检行。

## SDPCRET-01 — BI 场景指标推送通道后续退役 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-channel-retirement-pending.png`、`scenario-bi-domain-tablet-dark-channel-retirement-pending.png`、`scenario-bi-domain-mobile-channel-retirement-pending.png`、`scenario-bi-domain-mobile-dark-channel-retirement-pending.png`、`scenario-bi-domain-tablet-channel-retirement-complete.png`、`scenario-bi-domain-tablet-dark-channel-retirement-complete.png`、`scenario-bi-domain-mobile-channel-retirement-complete.png`、`scenario-bi-domain-mobile-dark-channel-retirement-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-retirement-pending 截图 | `scenario-bi-domain-tablet-channel-retirement-pending.png` 存在且 channel-retirement-pending framing 正常 | SDPCRET-01 · RESP-06 |
| 2 | tablet dark channel-retirement-pending 截图 | `scenario-bi-domain-tablet-dark-channel-retirement-pending.png` 存在且退役 banner 可读 | SDPCRET-01 · VIS-05 |
| 3 | mobile light channel-retirement-complete 截图 | `scenario-bi-domain-mobile-channel-retirement-complete.png` channel-retirement-complete banner 首屏可见 | SDPCRET-01 · RESP-07 |
| 4 | mobile dark channel-retirement-complete 截图 | `scenario-bi-domain-mobile-dark-channel-retirement-complete.png` channel-retirement-complete 对比度可辨认 | SDPCRET-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelRetirementViewportLightDarkScreenshots` biDomain 全过 | SDPCRET-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 channel-retirement-pending 面板 → 点击「触发指标通道退役完成」→ 对照 tablet/mobile light/dark 八张 channel-retirement-pending/channel-retirement-complete 截图。

## SDPCRET-02 — DevOps 场景阶段推送通道后续退役 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-channel-retirement-pending.png`、`scenario-devops-domain-tablet-dark-channel-retirement-pending.png`、`scenario-devops-domain-mobile-channel-retirement-pending.png`、`scenario-devops-domain-mobile-dark-channel-retirement-pending.png`、`scenario-devops-domain-tablet-channel-retirement-complete.png`、`scenario-devops-domain-tablet-dark-channel-retirement-complete.png`、`scenario-devops-domain-mobile-channel-retirement-complete.png`、`scenario-devops-domain-mobile-dark-channel-retirement-complete.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-retirement-pending 截图 | `scenario-devops-domain-tablet-channel-retirement-pending.png` 存在且 channel-retirement-pending framing 正常 | SDPCRET-02 · RESP-06 |
| 2 | tablet dark channel-retirement-pending 截图 | `scenario-devops-domain-tablet-dark-channel-retirement-pending.png` 存在且退役摘要可读 | SDPCRET-02 · VIS-05 |
| 3 | mobile light channel-retirement-complete 截图 | `scenario-devops-domain-mobile-channel-retirement-complete.png` 流水线 channel-retirement-complete 首屏可见 | SDPCRET-02 · RESP-07 |
| 4 | mobile dark channel-retirement-complete 截图 | `scenario-devops-domain-mobile-dark-channel-retirement-complete.png` channel-retirement-complete 对比度可辨认 | SDPCRET-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道后续退役 tablet/mobile light/dark 可见 | SDPCRET-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 channel-retirement-pending 面板 → 点击「触发阶段通道退役完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCRET-03 — Gateway 场景端点推送通道后续退役 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-channel-retirement-pending.png`、`scenario-gateway-domain-tablet-dark-channel-retirement-pending.png`、`scenario-gateway-domain-mobile-channel-retirement-pending.png`、`scenario-gateway-domain-mobile-dark-channel-retirement-pending.png`、`scenario-gateway-domain-tablet-channel-retirement-complete.png`、`scenario-gateway-domain-tablet-dark-channel-retirement-complete.png`、`scenario-gateway-domain-mobile-channel-retirement-complete.png`、`scenario-gateway-domain-mobile-dark-channel-retirement-complete.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-retirement-pending 截图 | `scenario-gateway-domain-tablet-channel-retirement-pending.png` 存在且 channel-retirement-pending framing 正常 | SDPCRET-03 · RESP-06 |
| 2 | tablet dark channel-retirement-pending 截图 | `scenario-gateway-domain-tablet-dark-channel-retirement-pending.png` 存在且退役摘要可读 | SDPCRET-03 · VIS-05 |
| 3 | mobile light channel-retirement-complete 截图 | `scenario-gateway-domain-mobile-channel-retirement-complete.png` 端点 channel-retirement-complete 首屏可见 | SDPCRET-03 · RESP-07 |
| 4 | mobile dark channel-retirement-complete 截图 | `scenario-gateway-domain-mobile-dark-channel-retirement-complete.png` channel-retirement-complete 层级不丢失 | SDPCRET-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道后续退役 tablet/mobile light/dark 可见 | SDPCRET-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 channel-retirement-pending 面板 → 点击「触发端点通道退役完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCRET-04 — Governance 场景审计行推送通道后续退役 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-channel-retirement-pending.png`、`scenario-governance-domain-tablet-dark-channel-retirement-pending.png`、`scenario-governance-domain-mobile-channel-retirement-pending.png`、`scenario-governance-domain-mobile-dark-channel-retirement-pending.png`、`scenario-governance-domain-tablet-channel-retirement-complete.png`、`scenario-governance-domain-tablet-dark-channel-retirement-complete.png`、`scenario-governance-domain-mobile-channel-retirement-complete.png`、`scenario-governance-domain-mobile-dark-channel-retirement-complete.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-retirement-pending 截图 | `scenario-governance-domain-tablet-channel-retirement-pending.png` 存在且 channel-retirement-pending framing 正常 | SDPCRET-04 · RESP-06 |
| 2 | tablet dark channel-retirement-pending 截图 | `scenario-governance-domain-tablet-dark-channel-retirement-pending.png` 存在且退役摘要可读 | SDPCRET-04 · VIS-05 |
| 3 | mobile light channel-retirement-complete 截图 | `scenario-governance-domain-mobile-channel-retirement-complete.png` 审计 channel-retirement-complete 首屏可见 | SDPCRET-04 · RESP-07 |
| 4 | mobile dark channel-retirement-complete 截图 | `scenario-governance-domain-mobile-dark-channel-retirement-complete.png` channel-retirement-complete 密度一致 | SDPCRET-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道后续退役 tablet/mobile light/dark 可见 | SDPCRET-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 channel-retirement-pending 面板 → 点击「触发合规通道退役完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCRET-05 — PaaS 场景容量推送通道后续退役 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-channel-retirement-pending.png`、`scenario-paas-domain-tablet-dark-channel-retirement-pending.png`、`scenario-paas-domain-mobile-channel-retirement-pending.png`、`scenario-paas-domain-mobile-dark-channel-retirement-pending.png`、`scenario-paas-domain-tablet-channel-retirement-complete.png`、`scenario-paas-domain-tablet-dark-channel-retirement-complete.png`、`scenario-paas-domain-mobile-channel-retirement-complete.png`、`scenario-paas-domain-mobile-dark-channel-retirement-complete.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-retirement-pending 截图 | `scenario-paas-domain-tablet-channel-retirement-pending.png` 存在且 channel-retirement-pending framing 正常 | SDPCRET-05 · RESP-06 |
| 2 | tablet dark channel-retirement-pending 截图 | `scenario-paas-domain-tablet-dark-channel-retirement-pending.png` 存在且退役摘要可读 | SDPCRET-05 · VIS-05 |
| 3 | mobile light channel-retirement-complete 截图 | `scenario-paas-domain-mobile-channel-retirement-complete.png` 容量 channel-retirement-complete 首屏可见 | SDPCRET-05 · RESP-07 |
| 4 | mobile dark channel-retirement-complete 截图 | `scenario-paas-domain-mobile-dark-channel-retirement-complete.png` channel-retirement-complete 列表项可辨认 | SDPCRET-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道后续退役 tablet/mobile light/dark 可见 | SDPCRET-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 channel-retirement-pending 面板 → 点击「触发容量通道退役完成」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md` SDPCRET-06～10
- 推送通道后续生命周期 前置：`scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md` SDPCLF-01～05
- 选型表：`decision-matrix.md` G125 场景域推送通道后续退役 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCRET-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelRetirementViewportLightDarkScreenshots`
