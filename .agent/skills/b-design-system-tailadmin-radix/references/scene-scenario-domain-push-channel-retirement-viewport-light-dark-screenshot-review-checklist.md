# 场景 Scenario Domain Push Channel Retirement Viewport Light/Dark Screenshot 评审清单

> DOCS-076 / G125 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道后续退役独立截图抽检**，确保各域 section 在推送通道退役中态与退役完成态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md`（SDPCRET-01～05）、`scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md`（SDPCLF-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续退役 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCRET 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道后续退役 tablet/mobile light/dark 独立截图 | SDPCRET-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道后续退役 tablet/mobile light/dark 独立截图 | SDPCRET-07 + `scenario-devops` |
| Gateway 端点推送通道后续退役 tablet/mobile light/dark 独立截图 | SDPCRET-08 + `scenario-gateway` |
| Governance 审计行推送通道后续退役 tablet/mobile light/dark 独立截图 | SDPCRET-09 + `scenario-governance` |
| 场景域推送通道后续退役 tablet/mobile light/dark 独立截图束缺门禁 | SDPCRET-10 + `verifyScenarioDomainPushChannelLifecycleViewportLightDarkScreenshots` + `verifyScenarioDomainPushChannelRetirementViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md` SDPCRET-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-retirement-pending,channel-retirement-complete}.png` 共 40 张推送通道后续退役独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道后续退役独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续退役 tablet/mobile light/dark 独立截图（G125）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续退役 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCRET-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCRET-06 — BI Analytics 指标推送通道后续退役 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-channel-retirement-pending.png`、`scenario-bi-domain-mobile-dark-channel-retirement-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-retirement-pending | `scenario-bi-domain-tablet-channel-retirement-pending.png` + `scenario-bi-domain-tablet-dark-channel-retirement-pending.png` channel-retirement-pending framing 正常 | SDPCRET-06 · RESP-06 |
| 2 | mobile light/dark channel-retirement-complete | `scenario-bi-domain-mobile-channel-retirement-complete.png` + `scenario-bi-domain-mobile-dark-channel-retirement-complete.png` channel-retirement-complete framing 正常 | SDPCRET-06 · RESP-07 |
| 3 | 指标推送通道后续退役 | 退役 banner「推送通道后续退役中（生命周期闭合后回收）」+ 退役摘要 + 退役完成 banner「退役已完成，推送通道已从路由表移除，历史订阅已归档」tablet/mobile light/dark 首屏可见 | SDPCRET-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 channel-retirement-pending banner 与 channel-retirement-complete banner 层级可辨认 | SDPCRET-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 channel-retirement-pending/channel-retirement-complete 截图全过 | SDPCRET-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 channel-retirement-pending 面板 → 点击「触发指标通道退役完成」→ 对照 tablet/mobile light/dark 八张推送通道后续退役截图。

## SDPCRET-07 — DevOps 阶段推送通道后续退役 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-channel-retirement-pending.png`、`scenario-devops-domain-mobile-dark-channel-retirement-complete.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-retirement-pending | `scenario-devops-domain-tablet-channel-retirement-pending.png` + `scenario-devops-domain-tablet-dark-channel-retirement-pending.png` channel-retirement-pending framing 正常 | SDPCRET-07 · RESP-06 |
| 2 | mobile light/dark channel-retirement-complete | `scenario-devops-domain-mobile-channel-retirement-complete.png` + `scenario-devops-domain-mobile-dark-channel-retirement-complete.png` channel-retirement-complete framing 正常 | SDPCRET-07 · RESP-07 |
| 3 | 阶段推送通道后续退役 | 流水线退役 banner + 退役完成摘要 tablet/mobile light/dark 首屏可见 | SDPCRET-07 · PAT-07 |
| 4 | channel-retirement-complete 态 | mobile dark 下 channel-retirement-complete 文案与「查看退役详情」按钮可辨认 | SDPCRET-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 channel-retirement-pending/channel-retirement-complete 截图全过 | SDPCRET-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 channel-retirement-pending 面板 → 点击「触发阶段通道退役完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCRET-08 — Gateway 端点推送通道后续退役 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-channel-retirement-pending.png`、`scenario-gateway-domain-mobile-dark-channel-retirement-complete.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-retirement-pending | `scenario-gateway-domain-tablet-channel-retirement-pending.png` + `scenario-gateway-domain-tablet-dark-channel-retirement-pending.png` channel-retirement-pending framing 正常 | SDPCRET-08 · RESP-06 |
| 2 | mobile light/dark channel-retirement-complete | `scenario-gateway-domain-mobile-channel-retirement-complete.png` + `scenario-gateway-domain-mobile-dark-channel-retirement-complete.png` channel-retirement-complete framing 正常 | SDPCRET-08 · RESP-07 |
| 3 | 端点推送通道后续退役 | 端点退役 banner + 退役完成摘要 tablet/mobile light/dark 首屏可见 | SDPCRET-08 · PAT-08 |
| 4 | channel-retirement-pending 态 | mobile dark 下退役摘要与退役 banner 可辨认 | SDPCRET-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 channel-retirement-pending/channel-retirement-complete 截图全过 | SDPCRET-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 channel-retirement-pending 面板 → 点击「触发端点通道退役完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCRET-09 — Governance 审计行推送通道后续退役 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-channel-retirement-pending.png`、`scenario-governance-domain-mobile-channel-retirement-pending.png`、`scenario-governance-domain-mobile-dark-channel-retirement-complete.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-retirement-pending | `scenario-governance-domain-tablet-channel-retirement-pending.png` + `scenario-governance-domain-tablet-dark-channel-retirement-pending.png` channel-retirement-pending framing 正常 | SDPCRET-09 · RESP-06 |
| 2 | mobile light/dark channel-retirement-complete | `scenario-governance-domain-mobile-channel-retirement-complete.png` + `scenario-governance-domain-mobile-dark-channel-retirement-complete.png` channel-retirement-complete framing 正常 | SDPCRET-09 · RESP-07 |
| 3 | 审计推送通道后续退役 | 合规退役 banner + 退役完成摘要 tablet/mobile light/dark 首屏可见 | SDPCRET-09 · PAT-09 |
| 4 | channel-retirement-complete 文案 | mobile dark 下「退役已完成，推送通道已从路由表移除，历史订阅已归档」文案可辨认 | SDPCRET-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 channel-retirement-pending/channel-retirement-complete 截图全过 | SDPCRET-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 channel-retirement-pending 面板 → 点击「触发合规通道退役完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCRET-10 — 场景域推送通道后续退役 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-retirement-pending,channel-retirement-complete}.png` + `scenarioDomainPushChannelRetirementViewportLightDarkScreenshotStates.pushChannelRetirementStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × channel-retirement-pending/channel-retirement-complete 全量 golden 存在 | SDPCRET-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelRetirementViewportLightDarkScreenshots` 通过 | SDPCRET-10 · PREVIEW-* |
| 3 | channel-retirement-pending 态 | 五域 `data-audit="scenario-domain-channel-retirement-pending-overlay"` `data-state="channel-retirement-pending"` 可见 | SDPCRET-10 · LOGIC-* |
| 4 | channel-retirement-complete 态 | 五域点击通道退役完成 trigger 后 `role="status"` + `data-state="channel-retirement-complete"` 可见 | SDPCRET-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelRetirementStateMatrixComplete = true` | SDPCRET-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道后续退役截图与门禁 JSON 输出。
