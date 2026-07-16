# 场景 Scenario Domain Push Channel Degradation Recovery Viewport Light/Dark Screenshot 评审清单

> DOCS-065 / G114 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道降级/恢复独立截图抽检**，确保各域 section 在推送通道降级态与通道恢复态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDPCDR-01～05）、`scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md`（SDLPS-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCDR 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道降级/恢复 tablet/mobile light/dark 独立截图 | SDPCDR-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道降级/恢复 tablet/mobile light/dark 独立截图 | SDPCDR-07 + `scenario-devops` |
| Gateway 端点推送通道降级/恢复 tablet/mobile light/dark 独立截图 | SDPCDR-08 + `scenario-gateway` |
| Governance 审计行推送通道降级/恢复 tablet/mobile light/dark 独立截图 | SDPCDR-09 + `scenario-governance` |
| 场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图束缺门禁 | SDPCDR-10 + `verifyScenarioDomainLongPollingStreamSubscriptionViewportLightDarkScreenshots` + `verifyScenarioDomainPushChannelDegradationRecoveryViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md` SDPCDR-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-degraded,channel-recovered}.png` 共 40 张推送通道降级/恢复独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道降级/恢复独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图（G114）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCDR-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCDR-06 — BI Analytics 指标推送通道降级/恢复 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-channel-degraded.png`、`scenario-bi-domain-mobile-dark-channel-recovered.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-degraded | `scenario-bi-domain-tablet-channel-degraded.png` + `scenario-bi-domain-tablet-dark-channel-degraded.png` channel-degraded framing 正常 | SDPCDR-06 · RESP-06 |
| 2 | mobile light/dark channel-recovered | `scenario-bi-domain-mobile-channel-recovered.png` + `scenario-bi-domain-mobile-dark-channel-recovered.png` recovered framing 正常 | SDPCDR-06 · RESP-07 |
| 3 | 指标推送通道降级/恢复 | 降级 banner「推送通道已降级（批量拉取模式）」+ 降级摘要 + 恢复完成 banner tablet/mobile light/dark 首屏可见 | SDPCDR-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 channel-degraded banner 与 channel-recovered banner 层级可辨认 | SDPCDR-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 channel-degraded/channel-recovered 截图全过 | SDPCDR-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 channel-degraded 面板 → 点击「触发指标通道恢复」→ 对照 tablet/mobile light/dark 八张推送通道降级/恢复截图。

## SDPCDR-07 — DevOps 阶段推送通道降级/恢复 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-channel-degraded.png`、`scenario-devops-domain-mobile-dark-channel-recovered.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-degraded | `scenario-devops-domain-tablet-channel-degraded.png` + `scenario-devops-domain-tablet-dark-channel-degraded.png` channel-degraded framing 正常 | SDPCDR-07 · RESP-06 |
| 2 | mobile light/dark channel-recovered | `scenario-devops-domain-mobile-channel-recovered.png` + `scenario-devops-domain-mobile-dark-channel-recovered.png` recovered framing 正常 | SDPCDR-07 · RESP-07 |
| 3 | 阶段推送通道降级/恢复 | 流水线降级 banner + 恢复完成摘要 tablet/mobile light/dark 首屏可见 | SDPCDR-07 · PAT-07 |
| 4 | channel-recovered 态 | mobile dark 下 recovered 文案与「查看恢复详情」按钮可辨认 | SDPCDR-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 channel-degraded/channel-recovered 截图全过 | SDPCDR-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 channel-degraded 面板 → 点击「触发阶段通道恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDR-08 — Gateway 端点推送通道降级/恢复 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-channel-degraded.png`、`scenario-gateway-domain-mobile-dark-channel-recovered.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-degraded | `scenario-gateway-domain-tablet-channel-degraded.png` + `scenario-gateway-domain-tablet-dark-channel-degraded.png` channel-degraded framing 正常 | SDPCDR-08 · RESP-06 |
| 2 | mobile light/dark channel-recovered | `scenario-gateway-domain-mobile-channel-recovered.png` + `scenario-gateway-domain-mobile-dark-channel-recovered.png` recovered framing 正常 | SDPCDR-08 · RESP-07 |
| 3 | 端点推送通道降级/恢复 | 端点降级 banner + 恢复完成摘要 tablet/mobile light/dark 首屏可见 | SDPCDR-08 · PAT-08 |
| 4 | channel-degraded 态 | mobile dark 下降级进度与 banner 可辨认 | SDPCDR-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 channel-degraded/channel-recovered 截图全过 | SDPCDR-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 channel-degraded 面板 → 点击「触发端点通道恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDR-09 — Governance 审计行推送通道降级/恢复 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-channel-degraded.png`、`scenario-governance-domain-mobile-channel-degraded.png`、`scenario-governance-domain-mobile-dark-channel-recovered.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-degraded | `scenario-governance-domain-tablet-channel-degraded.png` + `scenario-governance-domain-tablet-dark-channel-degraded.png` channel-degraded framing 正常 | SDPCDR-09 · RESP-06 |
| 2 | mobile light/dark channel-recovered | `scenario-governance-domain-mobile-channel-recovered.png` + `scenario-governance-domain-mobile-dark-channel-recovered.png` recovered framing 正常 | SDPCDR-09 · RESP-07 |
| 3 | 审计推送通道降级/恢复 | 审计降级 banner + 恢复完成摘要 tablet/mobile light/dark 首屏可见 | SDPCDR-09 · PAT-09 |
| 4 | recovered 文案 | mobile dark 下「推送通道已恢复，合规事件推送稳定，可继续提交策略变更」文案可辨认 | SDPCDR-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 channel-degraded/channel-recovered 截图全过 | SDPCDR-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 channel-degraded 面板 → 点击「触发审计通道恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDR-10 — 场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-degraded,channel-recovered}.png` + `scenarioDomainPushChannelDegradationRecoveryViewportLightDarkScreenshotStates.pushChannelDegradationRecoveryStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × channel-degraded/channel-recovered 全量 golden 存在 | SDPCDR-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelDegradationRecoveryViewportLightDarkScreenshots` 通过 | SDPCDR-10 · PREVIEW-* |
| 3 | channel-degraded 态 | 五域 `data-audit="scenario-domain-channel-degraded-overlay"` `data-state="channel-degraded"` 可见 | SDPCDR-10 · LOGIC-* |
| 4 | channel-recovered 态 | 五域点击 channel recovery trigger 后 `role="status"` + `data-state="channel-recovered"` 可见 | SDPCDR-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelDegradationRecoveryStateMatrixComplete = true` | SDPCDR-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道降级/恢复截图与门禁 JSON 输出。
