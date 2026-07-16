# 场景 Scenario Domain Push Channel Compensation Reconciliation Viewport Light/Dark Screenshot 评审清单

> DOCS-071 / G120 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道后续补偿/对账独立截图抽检**，确保各域 section 在推送通道补偿对账中态与补偿对账完成态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md`（SDPCCR-01～05）、`scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md`（SDPCAR-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCCR 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道后续补偿/对账 tablet/mobile light/dark 独立截图 | SDPCCR-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道后续补偿/对账 tablet/mobile light/dark 独立截图 | SDPCCR-07 + `scenario-devops` |
| Gateway 端点推送通道后续补偿/对账 tablet/mobile light/dark 独立截图 | SDPCCR-08 + `scenario-gateway` |
| Governance 审计行推送通道后续补偿/对账 tablet/mobile light/dark 独立截图 | SDPCCR-09 + `scenario-governance` |
| 场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图束缺门禁 | SDPCCR-10 + `verifyScenarioDomainPushChannelAsyncResilienceViewportLightDarkScreenshots` + `verifyScenarioDomainPushChannelCompensationReconciliationViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md` SDPCCR-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{compensation-pending,reconciliation-complete}.png` 共 40 张推送通道后续补偿/对账独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道后续补偿/对账独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图（G120）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCCR-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCCR-06 — BI Analytics 指标推送通道后续补偿/对账 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-compensation-pending.png`、`scenario-bi-domain-mobile-dark-reconciliation-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark compensation-pending | `scenario-bi-domain-tablet-compensation-pending.png` + `scenario-bi-domain-tablet-dark-compensation-pending.png` compensation-pending framing 正常 | SDPCCR-06 · RESP-06 |
| 2 | mobile light/dark reconciliation-complete | `scenario-bi-domain-mobile-reconciliation-complete.png` + `scenario-bi-domain-mobile-dark-reconciliation-complete.png` reconciliation-complete framing 正常 | SDPCCR-06 · RESP-07 |
| 3 | 指标推送通道后续补偿/对账 | 补偿对账 banner「推送通道后续补偿对账中（差异事件排队）」+ 差异事件摘要 + 补偿对账完成 banner「补偿对账已完成，指标推送通道账实一致，可继续接收实时变更事件」tablet/mobile light/dark 首屏可见 | SDPCCR-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 compensation-pending banner 与 reconciliation-complete banner 层级可辨认 | SDPCCR-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 compensation-pending/reconciliation-complete 截图全过 | SDPCCR-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 compensation-pending 面板 → 点击「触发指标补偿对账完成」→ 对照 tablet/mobile light/dark 八张推送通道后续补偿/对账截图。

## SDPCCR-07 — DevOps 阶段推送通道后续补偿/对账 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-compensation-pending.png`、`scenario-devops-domain-mobile-dark-reconciliation-complete.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark compensation-pending | `scenario-devops-domain-tablet-compensation-pending.png` + `scenario-devops-domain-tablet-dark-compensation-pending.png` compensation-pending framing 正常 | SDPCCR-07 · RESP-06 |
| 2 | mobile light/dark reconciliation-complete | `scenario-devops-domain-mobile-reconciliation-complete.png` + `scenario-devops-domain-mobile-dark-reconciliation-complete.png` reconciliation-complete framing 正常 | SDPCCR-07 · RESP-07 |
| 3 | 阶段推送通道后续补偿/对账 | 流水线补偿对账 banner + 补偿对账完成摘要 tablet/mobile light/dark 首屏可见 | SDPCCR-07 · PAT-07 |
| 4 | reconciliation-complete 态 | mobile dark 下 reconciliation-complete 文案与「查看补偿对账详情」按钮可辨认 | SDPCCR-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 compensation-pending/reconciliation-complete 截图全过 | SDPCCR-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 compensation-pending 面板 → 点击「触发阶段补偿对账完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCR-08 — Gateway 端点推送通道后续补偿/对账 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-compensation-pending.png`、`scenario-gateway-domain-mobile-dark-reconciliation-complete.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark compensation-pending | `scenario-gateway-domain-tablet-compensation-pending.png` + `scenario-gateway-domain-tablet-dark-compensation-pending.png` compensation-pending framing 正常 | SDPCCR-08 · RESP-06 |
| 2 | mobile light/dark reconciliation-complete | `scenario-gateway-domain-mobile-reconciliation-complete.png` + `scenario-gateway-domain-mobile-dark-reconciliation-complete.png` reconciliation-complete framing 正常 | SDPCCR-08 · RESP-07 |
| 3 | 端点推送通道后续补偿/对账 | 端点补偿对账 banner + 补偿对账完成摘要 tablet/mobile light/dark 首屏可见 | SDPCCR-08 · PAT-08 |
| 4 | compensation-pending 态 | mobile dark 下差异事件摘要与补偿对账 banner 可辨认 | SDPCCR-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 compensation-pending/reconciliation-complete 截图全过 | SDPCCR-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 compensation-pending 面板 → 点击「触发端点补偿对账完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCR-09 — Governance 审计行推送通道后续补偿/对账 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-compensation-pending.png`、`scenario-governance-domain-mobile-compensation-pending.png`、`scenario-governance-domain-mobile-dark-reconciliation-complete.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark compensation-pending | `scenario-governance-domain-tablet-compensation-pending.png` + `scenario-governance-domain-tablet-dark-compensation-pending.png` compensation-pending framing 正常 | SDPCCR-09 · RESP-06 |
| 2 | mobile light/dark reconciliation-complete | `scenario-governance-domain-mobile-reconciliation-complete.png` + `scenario-governance-domain-mobile-dark-reconciliation-complete.png` reconciliation-complete framing 正常 | SDPCCR-09 · RESP-07 |
| 3 | 审计推送通道后续补偿/对账 | 审计补偿对账 banner + 补偿对账完成摘要 tablet/mobile light/dark 首屏可见 | SDPCCR-09 · PAT-09 |
| 4 | reconciliation-complete 文案 | mobile dark 下「补偿对账已完成，合规事件推送通道账实一致，可继续提交策略变更」文案可辨认 | SDPCCR-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 compensation-pending/reconciliation-complete 截图全过 | SDPCCR-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 compensation-pending 面板 → 点击「触发审计补偿对账完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCR-10 — 场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{compensation-pending,reconciliation-complete}.png` + `scenarioDomainPushChannelCompensationReconciliationViewportLightDarkScreenshotStates.pushChannelCompensationReconciliationStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × compensation-pending/reconciliation-complete 全量 golden 存在 | SDPCCR-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelCompensationReconciliationViewportLightDarkScreenshots` 通过 | SDPCCR-10 · PREVIEW-* |
| 3 | compensation-pending 态 | 五域 `data-audit="scenario-domain-compensation-pending-overlay"` `data-state="compensation-pending"` 可见 | SDPCCR-10 · LOGIC-* |
| 4 | reconciliation-complete 态 | 五域点击补偿对账完成 trigger 后 `role="status"` + `data-state="reconciliation-complete"` 可见 | SDPCCR-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelCompensationReconciliationStateMatrixComplete = true` | SDPCCR-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道后续补偿/对账截图与门禁 JSON 输出。
