# 场景 Scenario Domain Push Channel Lifecycle Viewport Light/Dark Screenshot 评审清单

> DOCS-075 / G124 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道后续生命周期独立截图抽检**，确保各域 section 在推送通道生命周期收尾中态与生命周期闭合态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md`（SDPCLF-01～05）、`scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md`（SDPCARCH-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCLF 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道后续生命周期 tablet/mobile light/dark 独立截图 | SDPCLF-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道后续生命周期 tablet/mobile light/dark 独立截图 | SDPCLF-07 + `scenario-devops` |
| Gateway 端点推送通道后续生命周期 tablet/mobile light/dark 独立截图 | SDPCLF-08 + `scenario-gateway` |
| Governance 审计行推送通道后续生命周期 tablet/mobile light/dark 独立截图 | SDPCLF-09 + `scenario-governance` |
| 场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图束缺门禁 | SDPCLF-10 + `verifyScenarioDomainPushChannelArchiveViewportLightDarkScreenshots` + `verifyScenarioDomainPushChannelLifecycleViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md` SDPCLF-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-lifecycle-pending,channel-lifecycle-complete}.png` 共 40 张推送通道后续生命周期独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道后续生命周期独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图（G124）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCLF-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCLF-06 — BI Analytics 指标推送通道后续生命周期 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-channel-lifecycle-pending.png`、`scenario-bi-domain-mobile-dark-channel-lifecycle-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-lifecycle-pending | `scenario-bi-domain-tablet-channel-lifecycle-pending.png` + `scenario-bi-domain-tablet-dark-channel-lifecycle-pending.png` channel-lifecycle-pending framing 正常 | SDPCLF-06 · RESP-06 |
| 2 | mobile light/dark channel-lifecycle-complete | `scenario-bi-domain-mobile-channel-lifecycle-complete.png` + `scenario-bi-domain-mobile-dark-channel-lifecycle-complete.png` channel-lifecycle-complete framing 正常 | SDPCLF-06 · RESP-07 |
| 3 | 指标推送通道后续生命周期 | 生命周期 banner「推送通道后续生命周期收尾中（归档后清理）」+ 生命周期收尾摘要 + 生命周期闭合 banner「生命周期已闭合，推送通道可正式下线或进入下一周期」tablet/mobile light/dark 首屏可见 | SDPCLF-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 channel-lifecycle-pending banner 与 channel-lifecycle-complete banner 层级可辨认 | SDPCLF-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 channel-lifecycle-pending/channel-lifecycle-complete 截图全过 | SDPCLF-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 channel-lifecycle-pending 面板 → 点击「触发指标生命周期闭合」→ 对照 tablet/mobile light/dark 八张推送通道后续生命周期截图。

## SDPCLF-07 — DevOps 阶段推送通道后续生命周期 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-channel-lifecycle-pending.png`、`scenario-devops-domain-mobile-dark-channel-lifecycle-complete.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-lifecycle-pending | `scenario-devops-domain-tablet-channel-lifecycle-pending.png` + `scenario-devops-domain-tablet-dark-channel-lifecycle-pending.png` channel-lifecycle-pending framing 正常 | SDPCLF-07 · RESP-06 |
| 2 | mobile light/dark channel-lifecycle-complete | `scenario-devops-domain-mobile-channel-lifecycle-complete.png` + `scenario-devops-domain-mobile-dark-channel-lifecycle-complete.png` channel-lifecycle-complete framing 正常 | SDPCLF-07 · RESP-07 |
| 3 | 阶段推送通道后续生命周期 | 流水线生命周期 banner + 生命周期闭合摘要 tablet/mobile light/dark 首屏可见 | SDPCLF-07 · PAT-07 |
| 4 | channel-lifecycle-complete 态 | mobile dark 下 channel-lifecycle-complete 文案与「查看生命周期详情」按钮可辨认 | SDPCLF-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 channel-lifecycle-pending/channel-lifecycle-complete 截图全过 | SDPCLF-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 channel-lifecycle-pending 面板 → 点击「触发阶段生命周期闭合」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCLF-08 — Gateway 端点推送通道后续生命周期 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-channel-lifecycle-pending.png`、`scenario-gateway-domain-mobile-dark-channel-lifecycle-complete.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-lifecycle-pending | `scenario-gateway-domain-tablet-channel-lifecycle-pending.png` + `scenario-gateway-domain-tablet-dark-channel-lifecycle-pending.png` channel-lifecycle-pending framing 正常 | SDPCLF-08 · RESP-06 |
| 2 | mobile light/dark channel-lifecycle-complete | `scenario-gateway-domain-mobile-channel-lifecycle-complete.png` + `scenario-gateway-domain-mobile-dark-channel-lifecycle-complete.png` channel-lifecycle-complete framing 正常 | SDPCLF-08 · RESP-07 |
| 3 | 端点推送通道后续生命周期 | 端点生命周期 banner + 生命周期闭合摘要 tablet/mobile light/dark 首屏可见 | SDPCLF-08 · PAT-08 |
| 4 | channel-lifecycle-pending 态 | mobile dark 下生命周期收尾摘要与生命周期 banner 可辨认 | SDPCLF-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 channel-lifecycle-pending/channel-lifecycle-complete 截图全过 | SDPCLF-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 channel-lifecycle-pending 面板 → 点击「触发端点生命周期闭合」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCLF-09 — Governance 审计行推送通道后续生命周期 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-channel-lifecycle-pending.png`、`scenario-governance-domain-mobile-channel-lifecycle-pending.png`、`scenario-governance-domain-mobile-dark-channel-lifecycle-complete.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-lifecycle-pending | `scenario-governance-domain-tablet-channel-lifecycle-pending.png` + `scenario-governance-domain-tablet-dark-channel-lifecycle-pending.png` channel-lifecycle-pending framing 正常 | SDPCLF-09 · RESP-06 |
| 2 | mobile light/dark channel-lifecycle-complete | `scenario-governance-domain-mobile-channel-lifecycle-complete.png` + `scenario-governance-domain-mobile-dark-channel-lifecycle-complete.png` channel-lifecycle-complete framing 正常 | SDPCLF-09 · RESP-07 |
| 3 | 审计推送通道后续生命周期 | 合规生命周期 banner + 生命周期闭合摘要 tablet/mobile light/dark 首屏可见 | SDPCLF-09 · PAT-09 |
| 4 | channel-lifecycle-complete 文案 | mobile dark 下「生命周期已闭合，推送通道可正式下线或进入下一周期」文案可辨认 | SDPCLF-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 channel-lifecycle-pending/channel-lifecycle-complete 截图全过 | SDPCLF-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 channel-lifecycle-pending 面板 → 点击「触发合规生命周期闭合」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCLF-10 — 场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-lifecycle-pending,channel-lifecycle-complete}.png` + `scenarioDomainPushChannelLifecycleViewportLightDarkScreenshotStates.pushChannelLifecycleStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × channel-lifecycle-pending/channel-lifecycle-complete 全量 golden 存在 | SDPCLF-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelLifecycleViewportLightDarkScreenshots` 通过 | SDPCLF-10 · PREVIEW-* |
| 3 | channel-lifecycle-pending 态 | 五域 `data-audit="scenario-domain-channel-lifecycle-pending-overlay"` `data-state="channel-lifecycle-pending"` 可见 | SDPCLF-10 · LOGIC-* |
| 4 | channel-lifecycle-complete 态 | 五域点击生命周期闭合 trigger 后 `role="status"` + `data-state="channel-lifecycle-complete"` 可见 | SDPCLF-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelLifecycleStateMatrixComplete = true` | SDPCLF-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道后续生命周期截图与门禁 JSON 输出。
