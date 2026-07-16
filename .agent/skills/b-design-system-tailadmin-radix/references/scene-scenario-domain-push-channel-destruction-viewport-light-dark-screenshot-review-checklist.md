# 场景 Scenario Domain Push Channel Destruction Viewport Light/Dark Screenshot 评审清单

> DOCS-077 / G126 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道后续销毁独立截图抽检**，确保各域 section 在推送通道销毁中态与销毁完成态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md`（SDPCDEST-01～05）、`scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md`（SDPCRET-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续销毁 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCDEST 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道后续销毁 tablet/mobile light/dark 独立截图 | SDPCDEST-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道后续销毁 tablet/mobile light/dark 独立截图 | SDPCDEST-07 + `scenario-devops` |
| Gateway 端点推送通道后续销毁 tablet/mobile light/dark 独立截图 | SDPCDEST-08 + `scenario-gateway` |
| Governance 审计行推送通道后续销毁 tablet/mobile light/dark 独立截图 | SDPCDEST-09 + `scenario-governance` |
| 场景域推送通道后续销毁 tablet/mobile light/dark 独立截图束缺门禁 | SDPCDEST-10 + `verifyScenarioDomainPushChannelLifecycleViewportLightDarkScreenshots` + `verifyScenarioDomainPushChannelDestructionViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md` SDPCDEST-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-destruction-pending,channel-destruction-complete}.png` 共 40 张推送通道后续销毁独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道后续销毁独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续销毁 tablet/mobile light/dark 独立截图（G126）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续销毁 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCDEST-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCDEST-06 — BI Analytics 指标推送通道后续销毁 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-channel-destruction-pending.png`、`scenario-bi-domain-mobile-dark-channel-destruction-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-destruction-pending | `scenario-bi-domain-tablet-channel-destruction-pending.png` + `scenario-bi-domain-tablet-dark-channel-destruction-pending.png` channel-destruction-pending framing 正常 | SDPCDEST-06 · RESP-06 |
| 2 | mobile light/dark channel-destruction-complete | `scenario-bi-domain-mobile-channel-destruction-complete.png` + `scenario-bi-domain-mobile-dark-channel-destruction-complete.png` channel-destruction-complete framing 正常 | SDPCDEST-06 · RESP-07 |
| 3 | 指标推送通道后续销毁 | 销毁 banner「推送通道后续销毁中（退役归档后清除）」+ 销毁摘要 + 销毁完成 banner「销毁已完成，推送通道资源已清除，历史数据已永久删除」tablet/mobile light/dark 首屏可见 | SDPCDEST-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 channel-destruction-pending banner 与 channel-destruction-complete banner 层级可辨认 | SDPCDEST-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 channel-destruction-pending/channel-destruction-complete 截图全过 | SDPCDEST-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 channel-destruction-pending 面板 → 点击「触发指标通道销毁完成」→ 对照 tablet/mobile light/dark 八张推送通道后续销毁截图。

## SDPCDEST-07 — DevOps 阶段推送通道后续销毁 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-channel-destruction-pending.png`、`scenario-devops-domain-mobile-dark-channel-destruction-complete.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-destruction-pending | `scenario-devops-domain-tablet-channel-destruction-pending.png` + `scenario-devops-domain-tablet-dark-channel-destruction-pending.png` channel-destruction-pending framing 正常 | SDPCDEST-07 · RESP-06 |
| 2 | mobile light/dark channel-destruction-complete | `scenario-devops-domain-mobile-channel-destruction-complete.png` + `scenario-devops-domain-mobile-dark-channel-destruction-complete.png` channel-destruction-complete framing 正常 | SDPCDEST-07 · RESP-07 |
| 3 | 阶段推送通道后续销毁 | 流水线销毁 banner + 销毁完成摘要 tablet/mobile light/dark 首屏可见 | SDPCDEST-07 · PAT-07 |
| 4 | channel-destruction-complete 态 | mobile dark 下 channel-destruction-complete 文案与「查看销毁详情」按钮可辨认 | SDPCDEST-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 channel-destruction-pending/channel-destruction-complete 截图全过 | SDPCDEST-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 channel-destruction-pending 面板 → 点击「触发阶段通道销毁完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDEST-08 — Gateway 端点推送通道后续销毁 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-channel-destruction-pending.png`、`scenario-gateway-domain-mobile-dark-channel-destruction-complete.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-destruction-pending | `scenario-gateway-domain-tablet-channel-destruction-pending.png` + `scenario-gateway-domain-tablet-dark-channel-destruction-pending.png` channel-destruction-pending framing 正常 | SDPCDEST-08 · RESP-06 |
| 2 | mobile light/dark channel-destruction-complete | `scenario-gateway-domain-mobile-channel-destruction-complete.png` + `scenario-gateway-domain-mobile-dark-channel-destruction-complete.png` channel-destruction-complete framing 正常 | SDPCDEST-08 · RESP-07 |
| 3 | 端点推送通道后续销毁 | 端点销毁 banner + 销毁完成摘要 tablet/mobile light/dark 首屏可见 | SDPCDEST-08 · PAT-08 |
| 4 | channel-destruction-pending 态 | mobile dark 下销毁摘要与销毁 banner 可辨认 | SDPCDEST-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 channel-destruction-pending/channel-destruction-complete 截图全过 | SDPCDEST-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 channel-destruction-pending 面板 → 点击「触发端点通道销毁完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDEST-09 — Governance 审计行推送通道后续销毁 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-channel-destruction-pending.png`、`scenario-governance-domain-mobile-channel-destruction-pending.png`、`scenario-governance-domain-mobile-dark-channel-destruction-complete.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-destruction-pending | `scenario-governance-domain-tablet-channel-destruction-pending.png` + `scenario-governance-domain-tablet-dark-channel-destruction-pending.png` channel-destruction-pending framing 正常 | SDPCDEST-09 · RESP-06 |
| 2 | mobile light/dark channel-destruction-complete | `scenario-governance-domain-mobile-channel-destruction-complete.png` + `scenario-governance-domain-mobile-dark-channel-destruction-complete.png` channel-destruction-complete framing 正常 | SDPCDEST-09 · RESP-07 |
| 3 | 审计推送通道后续销毁 | 合规销毁 banner + 销毁完成摘要 tablet/mobile light/dark 首屏可见 | SDPCDEST-09 · PAT-09 |
| 4 | channel-destruction-complete 文案 | mobile dark 下「销毁已完成，推送通道资源已清除，历史数据已永久删除」文案可辨认 | SDPCDEST-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 channel-destruction-pending/channel-destruction-complete 截图全过 | SDPCDEST-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 channel-destruction-pending 面板 → 点击「触发合规通道销毁完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCDEST-10 — 场景域推送通道后续销毁 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-destruction-pending,channel-destruction-complete}.png` + `scenarioDomainPushChannelDestructionViewportLightDarkScreenshotStates.pushChannelDestructionStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × channel-destruction-pending/channel-destruction-complete 全量 golden 存在 | SDPCDEST-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelDestructionViewportLightDarkScreenshots` 通过 | SDPCDEST-10 · PREVIEW-* |
| 3 | channel-destruction-pending 态 | 五域 `data-audit="scenario-domain-channel-destruction-pending-overlay"` `data-state="channel-destruction-pending"` 可见 | SDPCDEST-10 · LOGIC-* |
| 4 | channel-destruction-complete 态 | 五域点击通道销毁完成 trigger 后 `role="status"` + `data-state="channel-destruction-complete"` 可见 | SDPCDEST-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelDestructionStateMatrixComplete = true` | SDPCDEST-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道后续销毁截图与门禁 JSON 输出。
