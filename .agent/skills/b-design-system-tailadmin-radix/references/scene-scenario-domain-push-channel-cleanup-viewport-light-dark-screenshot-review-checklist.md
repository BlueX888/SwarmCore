# 场景 Scenario Domain Push Channel Cleanup Viewport Light/Dark Screenshot 评审清单

> DOCS-078 / G127 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道后续清理独立截图抽检**，确保各域 section 在推送通道清理中态与清理完成态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md`（SDPCCLN-01～05）、`scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md`（SDPCDEST-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续清理 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCCLN 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道后续清理 tablet/mobile light/dark 独立截图 | SDPCCLN-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道后续清理 tablet/mobile light/dark 独立截图 | SDPCCLN-07 + `scenario-devops` |
| Gateway 端点推送通道后续清理 tablet/mobile light/dark 独立截图 | SDPCCLN-08 + `scenario-gateway` |
| Governance 审计行推送通道后续清理 tablet/mobile light/dark 独立截图 | SDPCCLN-09 + `scenario-governance` |
| 场景域推送通道后续清理 tablet/mobile light/dark 独立截图束缺门禁 | SDPCCLN-10 + `verifyScenarioDomainPushChannelCleanupViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md` SDPCCLN-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-cleanup-pending,channel-cleanup-complete}.png` 共 40 张推送通道后续清理独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道后续清理独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续清理 tablet/mobile light/dark 独立截图（G127）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续清理 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCCLN-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCCLN-06 — BI Analytics 指标推送通道后续清理 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-channel-cleanup-pending.png`、`scenario-bi-domain-mobile-dark-channel-cleanup-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-cleanup-pending | `scenario-bi-domain-tablet-channel-cleanup-pending.png` + `scenario-bi-domain-tablet-dark-channel-cleanup-pending.png` channel-cleanup-pending framing 正常 | SDPCCLN-06 · RESP-06 |
| 2 | mobile light/dark channel-cleanup-complete | `scenario-bi-domain-mobile-channel-cleanup-complete.png` + `scenario-bi-domain-mobile-dark-channel-cleanup-complete.png` channel-cleanup-complete framing 正常 | SDPCCLN-06 · RESP-07 |
| 3 | 指标推送通道后续清理 | 清理 banner「推送通道后续清理中（销毁后残留清除）」+ 清理摘要 + 清理完成 banner「清理已完成，推送通道临时资源已回收，残留索引已清除」tablet/mobile light/dark 首屏可见 | SDPCCLN-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 channel-cleanup-pending banner 与 channel-cleanup-complete banner 层级可辨认 | SDPCCLN-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 channel-cleanup-pending/channel-cleanup-complete 截图全过 | SDPCCLN-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 channel-cleanup-pending 面板 → 点击「触发指标通道清理完成」→ 对照 tablet/mobile light/dark 八张推送通道后续清理截图。

## SDPCCLN-07 — DevOps 阶段推送通道后续清理 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-channel-cleanup-pending.png`、`scenario-devops-domain-mobile-dark-channel-cleanup-complete.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-cleanup-pending | `scenario-devops-domain-tablet-channel-cleanup-pending.png` + `scenario-devops-domain-tablet-dark-channel-cleanup-pending.png` channel-cleanup-pending framing 正常 | SDPCCLN-07 · RESP-06 |
| 2 | mobile light/dark channel-cleanup-complete | `scenario-devops-domain-mobile-channel-cleanup-complete.png` + `scenario-devops-domain-mobile-dark-channel-cleanup-complete.png` channel-cleanup-complete framing 正常 | SDPCCLN-07 · RESP-07 |
| 3 | 阶段推送通道后续清理 | 流水线清理 banner + 清理完成摘要 tablet/mobile light/dark 首屏可见 | SDPCCLN-07 · PAT-07 |
| 4 | channel-cleanup-complete 态 | mobile dark 下 channel-cleanup-complete 文案与「查看清理详情」按钮可辨认 | SDPCCLN-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 channel-cleanup-pending/channel-cleanup-complete 截图全过 | SDPCCLN-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 channel-cleanup-pending 面板 → 点击「触发阶段通道清理完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCLN-08 — Gateway 端点推送通道后续清理 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-channel-cleanup-pending.png`、`scenario-gateway-domain-mobile-dark-channel-cleanup-complete.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-cleanup-pending | `scenario-gateway-domain-tablet-channel-cleanup-pending.png` + `scenario-gateway-domain-tablet-dark-channel-cleanup-pending.png` channel-cleanup-pending framing 正常 | SDPCCLN-08 · RESP-06 |
| 2 | mobile light/dark channel-cleanup-complete | `scenario-gateway-domain-mobile-channel-cleanup-complete.png` + `scenario-gateway-domain-mobile-dark-channel-cleanup-complete.png` channel-cleanup-complete framing 正常 | SDPCCLN-08 · RESP-07 |
| 3 | 端点推送通道后续清理 | 端点清理 banner + 清理完成摘要 tablet/mobile light/dark 首屏可见 | SDPCCLN-08 · PAT-08 |
| 4 | channel-cleanup-pending 态 | mobile dark 下清理摘要与清理 banner 可辨认 | SDPCCLN-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 channel-cleanup-pending/channel-cleanup-complete 截图全过 | SDPCCLN-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 channel-cleanup-pending 面板 → 点击「触发端点通道清理完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCLN-09 — Governance 审计行推送通道后续清理 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-channel-cleanup-pending.png`、`scenario-governance-domain-mobile-channel-cleanup-pending.png`、`scenario-governance-domain-mobile-dark-channel-cleanup-complete.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-cleanup-pending | `scenario-governance-domain-tablet-channel-cleanup-pending.png` + `scenario-governance-domain-tablet-dark-channel-cleanup-pending.png` channel-cleanup-pending framing 正常 | SDPCCLN-09 · RESP-06 |
| 2 | mobile light/dark channel-cleanup-complete | `scenario-governance-domain-mobile-channel-cleanup-complete.png` + `scenario-governance-domain-mobile-dark-channel-cleanup-complete.png` channel-cleanup-complete framing 正常 | SDPCCLN-09 · RESP-07 |
| 3 | 审计推送通道后续清理 | 合规清理 banner + 清理完成摘要 tablet/mobile light/dark 首屏可见 | SDPCCLN-09 · PAT-09 |
| 4 | channel-cleanup-complete 文案 | mobile dark 下「清理已完成，推送通道临时资源已回收，残留索引已清除」文案可辨认 | SDPCCLN-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 channel-cleanup-pending/channel-cleanup-complete 截图全过 | SDPCCLN-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 channel-cleanup-pending 面板 → 点击「触发合规通道清理完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCLN-10 — 场景域推送通道后续清理 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-cleanup-pending,channel-cleanup-complete}.png` + `scenarioDomainPushChannelCleanupViewportLightDarkScreenshotStates.pushChannelCleanupStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × channel-cleanup-pending/channel-cleanup-complete 全量 golden 存在 | SDPCCLN-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelCleanupViewportLightDarkScreenshots` 通过 | SDPCCLN-10 · PREVIEW-* |
| 3 | channel-cleanup-pending 态 | 五域 `data-audit="scenario-domain-channel-cleanup-pending-overlay"` `data-state="channel-cleanup-pending"` 可见 | SDPCCLN-10 · LOGIC-* |
| 4 | channel-cleanup-complete 态 | 五域点击通道清理完成 trigger 后 `role="status"` + `data-state="channel-cleanup-complete"` 可见 | SDPCCLN-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelCleanupStateMatrixComplete = true` | SDPCCLN-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道后续清理截图与门禁 JSON 输出。
