# Scenario Domain Push Channel Degradation Recovery Viewport Light/Dark Screenshot 评审清单

> DOCS-065 / G114 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道降级/恢复独立截图视觉回归抽检**，确保每个场景 section 在推送通道降级态、通道恢复态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md`（SDLPS-01～05）、`scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDPCDR-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCDR 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道降级/恢复 tablet/mobile light/dark golden 对照 | SDPCDR-01 + `scenario-bi-domain-tablet-channel-degraded.png` + `scenario-bi-domain-mobile-dark-channel-recovered.png` |
| DevOps 场景阶段推送通道降级/恢复 tablet/mobile light/dark golden 对照 | SDPCDR-02 + `scenario-devops-domain-tablet-channel-degraded.png` + `scenario-devops-domain-mobile-dark-channel-recovered.png` |
| Gateway 场景端点推送通道降级/恢复 tablet/mobile light/dark golden 对照 | SDPCDR-03 + `scenario-gateway-domain-tablet-channel-degraded.png` + `scenario-gateway-domain-mobile-dark-channel-recovered.png` |
| Governance 场景审计行推送通道降级/恢复 tablet/mobile light/dark golden 对照 | SDPCDR-04 + `scenario-governance-domain-tablet-channel-degraded.png` + `scenario-governance-domain-mobile-dark-channel-recovered.png` |
| PaaS 场景容量推送通道降级/恢复 tablet/mobile light/dark golden 对照 | SDPCDR-05 + `scenario-paas-domain-tablet-channel-degraded.png` + `scenario-paas-domain-mobile-dark-channel-recovered.png` |

## 通用前置

1. 先完成 `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md` SDLPS-01～05（长轮询/流式订阅独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-degraded,channel-recovered}.png` 四视口双主题推送通道降级/恢复独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 channel-degraded 与一张 channel-recovered 独立截图；channel-degraded 必须出现降级 banner「推送通道已降级（批量拉取模式）」与降级摘要，channel-recovered 必须出现恢复 banner 与「查看恢复详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道降级/恢复截图出现文案裁切、降级 banner 对比度不足、recovered banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图（G114）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图抽检行。

## SDPCDR-01 — BI 场景指标推送通道降级/恢复 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-channel-degraded.png`、`scenario-bi-domain-tablet-dark-channel-degraded.png`、`scenario-bi-domain-mobile-channel-degraded.png`、`scenario-bi-domain-mobile-dark-channel-degraded.png`、`scenario-bi-domain-tablet-channel-recovered.png`、`scenario-bi-domain-tablet-dark-channel-recovered.png`、`scenario-bi-domain-mobile-channel-recovered.png`、`scenario-bi-domain-mobile-dark-channel-recovered.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-degraded 截图 | `scenario-bi-domain-tablet-channel-degraded.png` 存在且 channel-degraded framing 正常 | SDPCDR-01 · RESP-06 |
| 2 | tablet dark channel-degraded 截图 | `scenario-bi-domain-tablet-dark-channel-degraded.png` 存在且降级 banner 可读 | SDPCDR-01 · VIS-05 |
| 3 | mobile light channel-recovered 截图 | `scenario-bi-domain-mobile-channel-recovered.png` recovered banner 首屏可见 | SDPCDR-01 · RESP-07 |
| 4 | mobile dark channel-recovered 截图 | `scenario-bi-domain-mobile-dark-channel-recovered.png` recovered 对比度可辨认 | SDPCDR-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelDegradationRecoveryViewportLightDarkScreenshots` biDomain 全过 | SDPCDR-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 channel-degraded 面板 → 点击「触发指标通道恢复」→ 对照 tablet/mobile light/dark 八张 channel-degraded/channel-recovered 截图。

## SDPCDR-02 — DevOps 场景阶段推送通道降级/恢复 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-channel-degraded.png`、`scenario-devops-domain-tablet-dark-channel-degraded.png`、`scenario-devops-domain-mobile-channel-degraded.png`、`scenario-devops-domain-mobile-dark-channel-degraded.png`、`scenario-devops-domain-tablet-channel-recovered.png`、`scenario-devops-domain-tablet-dark-channel-recovered.png`、`scenario-devops-domain-mobile-channel-recovered.png`、`scenario-devops-domain-mobile-dark-channel-recovered.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-degraded 截图 | `scenario-devops-domain-tablet-channel-degraded.png` 存在且 channel-degraded framing 正常 | SDPCDR-02 · RESP-06 |
| 2 | tablet dark channel-degraded 截图 | `scenario-devops-domain-tablet-dark-channel-degraded.png` 存在且降级摘要可读 | SDPCDR-02 · VIS-05 |
| 3 | mobile light channel-recovered 截图 | `scenario-devops-domain-mobile-channel-recovered.png` 流水线 recovered 首屏可见 | SDPCDR-02 · RESP-07 |
| 4 | mobile dark channel-recovered 截图 | `scenario-devops-domain-mobile-dark-channel-recovered.png` recovered 对比度可辨认 | SDPCDR-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道降级/恢复 tablet/mobile light/dark 可见 | SDPCDR-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 channel-degraded 面板 → 点击「触发阶段通道恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDR-03 — Gateway 场景端点推送通道降级/恢复 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-channel-degraded.png`、`scenario-gateway-domain-tablet-dark-channel-degraded.png`、`scenario-gateway-domain-mobile-channel-degraded.png`、`scenario-gateway-domain-mobile-dark-channel-degraded.png`、`scenario-gateway-domain-tablet-channel-recovered.png`、`scenario-gateway-domain-tablet-dark-channel-recovered.png`、`scenario-gateway-domain-mobile-channel-recovered.png`、`scenario-gateway-domain-mobile-dark-channel-recovered.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-degraded 截图 | `scenario-gateway-domain-tablet-channel-degraded.png` 存在且 channel-degraded framing 正常 | SDPCDR-03 · RESP-06 |
| 2 | tablet dark channel-degraded 截图 | `scenario-gateway-domain-tablet-dark-channel-degraded.png` 存在且降级摘要可读 | SDPCDR-03 · VIS-05 |
| 3 | mobile light channel-recovered 截图 | `scenario-gateway-domain-mobile-channel-recovered.png` 端点 recovered 首屏可见 | SDPCDR-03 · RESP-07 |
| 4 | mobile dark channel-recovered 截图 | `scenario-gateway-domain-mobile-dark-channel-recovered.png` recovered 层级不丢失 | SDPCDR-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道降级/恢复 tablet/mobile light/dark 可见 | SDPCDR-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 channel-degraded 面板 → 点击「触发端点通道恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDR-04 — Governance 场景审计行推送通道降级/恢复 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-channel-degraded.png`、`scenario-governance-domain-tablet-dark-channel-degraded.png`、`scenario-governance-domain-mobile-channel-degraded.png`、`scenario-governance-domain-mobile-dark-channel-degraded.png`、`scenario-governance-domain-tablet-channel-recovered.png`、`scenario-governance-domain-tablet-dark-channel-recovered.png`、`scenario-governance-domain-mobile-channel-recovered.png`、`scenario-governance-domain-mobile-dark-channel-recovered.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-degraded 截图 | `scenario-governance-domain-tablet-channel-degraded.png` 存在且 channel-degraded framing 正常 | SDPCDR-04 · RESP-06 |
| 2 | tablet dark channel-degraded 截图 | `scenario-governance-domain-tablet-dark-channel-degraded.png` 存在且降级摘要可读 | SDPCDR-04 · VIS-05 |
| 3 | mobile light channel-recovered 截图 | `scenario-governance-domain-mobile-channel-recovered.png` 审计 recovered 首屏可见 | SDPCDR-04 · RESP-07 |
| 4 | mobile dark channel-recovered 截图 | `scenario-governance-domain-mobile-dark-channel-recovered.png` recovered 密度一致 | SDPCDR-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道降级/恢复 tablet/mobile light/dark 可见 | SDPCDR-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 channel-degraded 面板 → 点击「触发审计通道恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDR-05 — PaaS 场景容量推送通道降级/恢复 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-channel-degraded.png`、`scenario-paas-domain-tablet-dark-channel-degraded.png`、`scenario-paas-domain-mobile-channel-degraded.png`、`scenario-paas-domain-mobile-dark-channel-degraded.png`、`scenario-paas-domain-tablet-channel-recovered.png`、`scenario-paas-domain-tablet-dark-channel-recovered.png`、`scenario-paas-domain-mobile-channel-recovered.png`、`scenario-paas-domain-mobile-dark-channel-recovered.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-degraded 截图 | `scenario-paas-domain-tablet-channel-degraded.png` 存在且 channel-degraded framing 正常 | SDPCDR-05 · RESP-06 |
| 2 | tablet dark channel-degraded 截图 | `scenario-paas-domain-tablet-dark-channel-degraded.png` 存在且降级摘要可读 | SDPCDR-05 · VIS-05 |
| 3 | mobile light channel-recovered 截图 | `scenario-paas-domain-mobile-channel-recovered.png` 容量 recovered 首屏可见 | SDPCDR-05 · RESP-07 |
| 4 | mobile dark channel-recovered 截图 | `scenario-paas-domain-mobile-dark-channel-recovered.png` recovered 列表项可辨认 | SDPCDR-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道降级/恢复 tablet/mobile light/dark 可见 | SDPCDR-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 channel-degraded 面板 → 点击「触发容量通道恢复」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md` SDPCDR-06～10
- 长轮询/流式订阅 前置：`scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md` SDLPS-01～05
- 选型表：`decision-matrix.md` G114 场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCDR-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelDegradationRecoveryViewportLightDarkScreenshots`
