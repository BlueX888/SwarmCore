# Scenario Domain Push Channel Destruction Viewport Light/Dark Screenshot 评审清单

> DOCS-077 / G126 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道后续销毁独立截图视觉回归抽检**，确保每个场景 section 在推送通道销毁中态、销毁完成态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md`（SDPCDEST-01～05）、`scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md`（SDPCDEST-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续销毁 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCDEST 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道后续销毁 tablet/mobile light/dark golden 对照 | SDPCDEST-01 + `scenario-bi-domain-tablet-channel-destruction-pending.png` + `scenario-bi-domain-mobile-dark-channel-destruction-complete.png` |
| DevOps 场景阶段推送通道后续销毁 tablet/mobile light/dark golden 对照 | SDPCDEST-02 + `scenario-devops-domain-tablet-channel-destruction-pending.png` + `scenario-devops-domain-mobile-dark-channel-destruction-complete.png` |
| Gateway 场景端点推送通道后续销毁 tablet/mobile light/dark golden 对照 | SDPCDEST-03 + `scenario-gateway-domain-tablet-channel-destruction-pending.png` + `scenario-gateway-domain-mobile-dark-channel-destruction-complete.png` |
| Governance 场景审计行推送通道后续销毁 tablet/mobile light/dark golden 对照 | SDPCDEST-04 + `scenario-governance-domain-tablet-channel-destruction-pending.png` + `scenario-governance-domain-mobile-dark-channel-destruction-complete.png` |
| PaaS 场景容量推送通道后续销毁 tablet/mobile light/dark golden 对照 | SDPCDEST-05 + `scenario-paas-domain-tablet-channel-destruction-pending.png` + `scenario-paas-domain-mobile-dark-channel-destruction-complete.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md` SDPCRET-01～05（推送通道后续退役独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-destruction-pending,channel-destruction-complete}.png` 四视口双主题推送通道后续销毁独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 channel-destruction-pending 与一张 channel-destruction-complete 独立截图；channel-destruction-pending 必须出现销毁 banner「推送通道后续销毁中（退役归档后清除）」与销毁摘要，channel-destruction-complete 必须出现销毁完成 banner「销毁已完成，推送通道资源已清除，历史数据已永久删除」与「查看销毁详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道后续销毁截图出现文案裁切、销毁 banner 对比度不足、channel-destruction-complete banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续销毁 tablet/mobile light/dark 独立截图（G126）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续销毁 tablet/mobile light/dark 独立截图抽检行。

## SDPCDEST-01 — BI 场景指标推送通道后续销毁 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-channel-destruction-pending.png`、`scenario-bi-domain-tablet-dark-channel-destruction-pending.png`、`scenario-bi-domain-mobile-channel-destruction-pending.png`、`scenario-bi-domain-mobile-dark-channel-destruction-pending.png`、`scenario-bi-domain-tablet-channel-destruction-complete.png`、`scenario-bi-domain-tablet-dark-channel-destruction-complete.png`、`scenario-bi-domain-mobile-channel-destruction-complete.png`、`scenario-bi-domain-mobile-dark-channel-destruction-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-destruction-pending 截图 | `scenario-bi-domain-tablet-channel-destruction-pending.png` 存在且 channel-destruction-pending framing 正常 | SDPCDEST-01 · RESP-06 |
| 2 | tablet dark channel-destruction-pending 截图 | `scenario-bi-domain-tablet-dark-channel-destruction-pending.png` 存在且销毁 banner 可读 | SDPCDEST-01 · VIS-05 |
| 3 | mobile light channel-destruction-complete 截图 | `scenario-bi-domain-mobile-channel-destruction-complete.png` channel-destruction-complete banner 首屏可见 | SDPCDEST-01 · RESP-07 |
| 4 | mobile dark channel-destruction-complete 截图 | `scenario-bi-domain-mobile-dark-channel-destruction-complete.png` channel-destruction-complete 对比度可辨认 | SDPCDEST-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelDestructionViewportLightDarkScreenshots` biDomain 全过 | SDPCDEST-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 channel-destruction-pending 面板 → 点击「触发指标通道销毁完成」→ 对照 tablet/mobile light/dark 八张 channel-destruction-pending/channel-destruction-complete 截图。

## SDPCDEST-02 — DevOps 场景阶段推送通道后续销毁 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-channel-destruction-pending.png`、`scenario-devops-domain-tablet-dark-channel-destruction-pending.png`、`scenario-devops-domain-mobile-channel-destruction-pending.png`、`scenario-devops-domain-mobile-dark-channel-destruction-pending.png`、`scenario-devops-domain-tablet-channel-destruction-complete.png`、`scenario-devops-domain-tablet-dark-channel-destruction-complete.png`、`scenario-devops-domain-mobile-channel-destruction-complete.png`、`scenario-devops-domain-mobile-dark-channel-destruction-complete.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-destruction-pending 截图 | `scenario-devops-domain-tablet-channel-destruction-pending.png` 存在且 channel-destruction-pending framing 正常 | SDPCDEST-02 · RESP-06 |
| 2 | tablet dark channel-destruction-pending 截图 | `scenario-devops-domain-tablet-dark-channel-destruction-pending.png` 存在且销毁摘要可读 | SDPCDEST-02 · VIS-05 |
| 3 | mobile light channel-destruction-complete 截图 | `scenario-devops-domain-mobile-channel-destruction-complete.png` 流水线 channel-destruction-complete 首屏可见 | SDPCDEST-02 · RESP-07 |
| 4 | mobile dark channel-destruction-complete 截图 | `scenario-devops-domain-mobile-dark-channel-destruction-complete.png` channel-destruction-complete 对比度可辨认 | SDPCDEST-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道后续销毁 tablet/mobile light/dark 可见 | SDPCDEST-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 channel-destruction-pending 面板 → 点击「触发阶段通道销毁完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDEST-03 — Gateway 场景端点推送通道后续销毁 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-channel-destruction-pending.png`、`scenario-gateway-domain-tablet-dark-channel-destruction-pending.png`、`scenario-gateway-domain-mobile-channel-destruction-pending.png`、`scenario-gateway-domain-mobile-dark-channel-destruction-pending.png`、`scenario-gateway-domain-tablet-channel-destruction-complete.png`、`scenario-gateway-domain-tablet-dark-channel-destruction-complete.png`、`scenario-gateway-domain-mobile-channel-destruction-complete.png`、`scenario-gateway-domain-mobile-dark-channel-destruction-complete.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-destruction-pending 截图 | `scenario-gateway-domain-tablet-channel-destruction-pending.png` 存在且 channel-destruction-pending framing 正常 | SDPCDEST-03 · RESP-06 |
| 2 | tablet dark channel-destruction-pending 截图 | `scenario-gateway-domain-tablet-dark-channel-destruction-pending.png` 存在且销毁摘要可读 | SDPCDEST-03 · VIS-05 |
| 3 | mobile light channel-destruction-complete 截图 | `scenario-gateway-domain-mobile-channel-destruction-complete.png` 端点 channel-destruction-complete 首屏可见 | SDPCDEST-03 · RESP-07 |
| 4 | mobile dark channel-destruction-complete 截图 | `scenario-gateway-domain-mobile-dark-channel-destruction-complete.png` channel-destruction-complete 层级不丢失 | SDPCDEST-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道后续销毁 tablet/mobile light/dark 可见 | SDPCDEST-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 channel-destruction-pending 面板 → 点击「触发端点通道销毁完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDEST-04 — Governance 场景审计行推送通道后续销毁 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-channel-destruction-pending.png`、`scenario-governance-domain-tablet-dark-channel-destruction-pending.png`、`scenario-governance-domain-mobile-channel-destruction-pending.png`、`scenario-governance-domain-mobile-dark-channel-destruction-pending.png`、`scenario-governance-domain-tablet-channel-destruction-complete.png`、`scenario-governance-domain-tablet-dark-channel-destruction-complete.png`、`scenario-governance-domain-mobile-channel-destruction-complete.png`、`scenario-governance-domain-mobile-dark-channel-destruction-complete.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-destruction-pending 截图 | `scenario-governance-domain-tablet-channel-destruction-pending.png` 存在且 channel-destruction-pending framing 正常 | SDPCDEST-04 · RESP-06 |
| 2 | tablet dark channel-destruction-pending 截图 | `scenario-governance-domain-tablet-dark-channel-destruction-pending.png` 存在且销毁摘要可读 | SDPCDEST-04 · VIS-05 |
| 3 | mobile light channel-destruction-complete 截图 | `scenario-governance-domain-mobile-channel-destruction-complete.png` 审计 channel-destruction-complete 首屏可见 | SDPCDEST-04 · RESP-07 |
| 4 | mobile dark channel-destruction-complete 截图 | `scenario-governance-domain-mobile-dark-channel-destruction-complete.png` channel-destruction-complete 密度一致 | SDPCDEST-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道后续销毁 tablet/mobile light/dark 可见 | SDPCDEST-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 channel-destruction-pending 面板 → 点击「触发合规通道销毁完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDEST-05 — PaaS 场景容量推送通道后续销毁 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-channel-destruction-pending.png`、`scenario-paas-domain-tablet-dark-channel-destruction-pending.png`、`scenario-paas-domain-mobile-channel-destruction-pending.png`、`scenario-paas-domain-mobile-dark-channel-destruction-pending.png`、`scenario-paas-domain-tablet-channel-destruction-complete.png`、`scenario-paas-domain-tablet-dark-channel-destruction-complete.png`、`scenario-paas-domain-mobile-channel-destruction-complete.png`、`scenario-paas-domain-mobile-dark-channel-destruction-complete.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-destruction-pending 截图 | `scenario-paas-domain-tablet-channel-destruction-pending.png` 存在且 channel-destruction-pending framing 正常 | SDPCDEST-05 · RESP-06 |
| 2 | tablet dark channel-destruction-pending 截图 | `scenario-paas-domain-tablet-dark-channel-destruction-pending.png` 存在且销毁摘要可读 | SDPCDEST-05 · VIS-05 |
| 3 | mobile light channel-destruction-complete 截图 | `scenario-paas-domain-mobile-channel-destruction-complete.png` 容量 channel-destruction-complete 首屏可见 | SDPCDEST-05 · RESP-07 |
| 4 | mobile dark channel-destruction-complete 截图 | `scenario-paas-domain-mobile-dark-channel-destruction-complete.png` channel-destruction-complete 列表项可辨认 | SDPCDEST-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道后续销毁 tablet/mobile light/dark 可见 | SDPCDEST-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 channel-destruction-pending 面板 → 点击「触发容量通道销毁完成」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md` SDPCDEST-06～10
- 推送通道后续退役 前置：`scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md` SDPCRET-01～05
- 选型表：`decision-matrix.md` G126 场景域推送通道后续销毁 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCDEST-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelDestructionViewportLightDarkScreenshots`
