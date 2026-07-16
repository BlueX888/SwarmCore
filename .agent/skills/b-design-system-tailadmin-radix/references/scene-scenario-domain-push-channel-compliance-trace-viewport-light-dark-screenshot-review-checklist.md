# 场景 Scenario Domain Push Channel Compliance Trace Viewport Light/Dark Screenshot 评审清单

> DOCS-073 / G122 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道后续合规留痕独立截图抽检**，确保各域 section 在推送通道合规留痕中态与合规留痕完成态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md`（SDPCCT-01～05）、`scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md`（SDPCAT-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCCT 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道后续合规留痕 tablet/mobile light/dark 独立截图 | SDPCCT-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道后续合规留痕 tablet/mobile light/dark 独立截图 | SDPCCT-07 + `scenario-devops` |
| Gateway 端点推送通道后续合规留痕 tablet/mobile light/dark 独立截图 | SDPCCT-08 + `scenario-gateway` |
| Governance 审计行推送通道后续合规留痕 tablet/mobile light/dark 独立截图 | SDPCCT-09 + `scenario-governance` |
| 场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图束缺门禁 | SDPCCT-10 + `verifyScenarioDomainPushChannelAuditTrackingViewportLightDarkScreenshots` + `verifyScenarioDomainPushChannelComplianceTraceViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md` SDPCCT-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{compliance-trace-pending,compliance-trace-complete}.png` 共 40 张推送通道后续合规留痕独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道后续合规留痕独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图（G122）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCCT-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCCT-06 — BI Analytics 指标推送通道后续合规留痕 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-compliance-trace-pending.png`、`scenario-bi-domain-mobile-dark-compliance-trace-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark compliance-trace-pending | `scenario-bi-domain-tablet-compliance-trace-pending.png` + `scenario-bi-domain-tablet-dark-compliance-trace-pending.png` compliance-trace-pending framing 正常 | SDPCCT-06 · RESP-06 |
| 2 | mobile light/dark compliance-trace-complete | `scenario-bi-domain-mobile-compliance-trace-complete.png` + `scenario-bi-domain-mobile-dark-compliance-trace-complete.png` compliance-trace-complete framing 正常 | SDPCCT-06 · RESP-07 |
| 3 | 指标推送通道后续合规留痕 | 合规留痕 banner「推送通道后续合规留痕中（合规事件排队）」+ 合规事件摘要 + 合规留痕完成 banner「合规留痕已完成，指标推送通道留痕可审计，可继续接收实时变更事件」tablet/mobile light/dark 首屏可见 | SDPCCT-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 compliance-trace-pending banner 与 compliance-trace-complete banner 层级可辨认 | SDPCCT-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 compliance-trace-pending/compliance-trace-complete 截图全过 | SDPCCT-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 compliance-trace-pending 面板 → 点击「触发指标合规留痕完成」→ 对照 tablet/mobile light/dark 八张推送通道后续合规留痕截图。

## SDPCCT-07 — DevOps 阶段推送通道后续合规留痕 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-compliance-trace-pending.png`、`scenario-devops-domain-mobile-dark-compliance-trace-complete.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark compliance-trace-pending | `scenario-devops-domain-tablet-compliance-trace-pending.png` + `scenario-devops-domain-tablet-dark-compliance-trace-pending.png` compliance-trace-pending framing 正常 | SDPCCT-07 · RESP-06 |
| 2 | mobile light/dark compliance-trace-complete | `scenario-devops-domain-mobile-compliance-trace-complete.png` + `scenario-devops-domain-mobile-dark-compliance-trace-complete.png` compliance-trace-complete framing 正常 | SDPCCT-07 · RESP-07 |
| 3 | 阶段推送通道后续合规留痕 | 流水线合规留痕 banner + 合规留痕完成摘要 tablet/mobile light/dark 首屏可见 | SDPCCT-07 · PAT-07 |
| 4 | compliance-trace-complete 态 | mobile dark 下 compliance-trace-complete 文案与「查看合规留痕详情」按钮可辨认 | SDPCCT-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 compliance-trace-pending/compliance-trace-complete 截图全过 | SDPCCT-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 compliance-trace-pending 面板 → 点击「触发阶段合规留痕完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCT-08 — Gateway 端点推送通道后续合规留痕 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-compliance-trace-pending.png`、`scenario-gateway-domain-mobile-dark-compliance-trace-complete.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark compliance-trace-pending | `scenario-gateway-domain-tablet-compliance-trace-pending.png` + `scenario-gateway-domain-tablet-dark-compliance-trace-pending.png` compliance-trace-pending framing 正常 | SDPCCT-08 · RESP-06 |
| 2 | mobile light/dark compliance-trace-complete | `scenario-gateway-domain-mobile-compliance-trace-complete.png` + `scenario-gateway-domain-mobile-dark-compliance-trace-complete.png` compliance-trace-complete framing 正常 | SDPCCT-08 · RESP-07 |
| 3 | 端点推送通道后续合规留痕 | 端点合规留痕 banner + 合规留痕完成摘要 tablet/mobile light/dark 首屏可见 | SDPCCT-08 · PAT-08 |
| 4 | compliance-trace-pending 态 | mobile dark 下合规事件摘要与合规留痕 banner 可辨认 | SDPCCT-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 compliance-trace-pending/compliance-trace-complete 截图全过 | SDPCCT-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 compliance-trace-pending 面板 → 点击「触发端点合规留痕完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCT-09 — Governance 审计行推送通道后续合规留痕 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-compliance-trace-pending.png`、`scenario-governance-domain-mobile-compliance-trace-pending.png`、`scenario-governance-domain-mobile-dark-compliance-trace-complete.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark compliance-trace-pending | `scenario-governance-domain-tablet-compliance-trace-pending.png` + `scenario-governance-domain-tablet-dark-compliance-trace-pending.png` compliance-trace-pending framing 正常 | SDPCCT-09 · RESP-06 |
| 2 | mobile light/dark compliance-trace-complete | `scenario-governance-domain-mobile-compliance-trace-complete.png` + `scenario-governance-domain-mobile-dark-compliance-trace-complete.png` compliance-trace-complete framing 正常 | SDPCCT-09 · RESP-07 |
| 3 | 审计推送通道后续合规留痕 | 合规合规留痕 banner + 合规留痕完成摘要 tablet/mobile light/dark 首屏可见 | SDPCCT-09 · PAT-09 |
| 4 | compliance-trace-complete 文案 | mobile dark 下「合规留痕已完成，合规事件推送通道留痕可审计，可继续提交策略变更」文案可辨认 | SDPCCT-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 compliance-trace-pending/compliance-trace-complete 截图全过 | SDPCCT-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 compliance-trace-pending 面板 → 点击「触发合规合规留痕完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCT-10 — 场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{compliance-trace-pending,compliance-trace-complete}.png` + `scenarioDomainPushChannelComplianceTraceViewportLightDarkScreenshotStates.pushChannelComplianceTraceStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × compliance-trace-pending/compliance-trace-complete 全量 golden 存在 | SDPCCT-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelComplianceTraceViewportLightDarkScreenshots` 通过 | SDPCCT-10 · PREVIEW-* |
| 3 | compliance-trace-pending 态 | 五域 `data-audit="scenario-domain-compliance-trace-pending-overlay"` `data-state="compliance-trace-pending"` 可见 | SDPCCT-10 · LOGIC-* |
| 4 | compliance-trace-complete 态 | 五域点击合规留痕完成 trigger 后 `role="status"` + `data-state="compliance-trace-complete"` 可见 | SDPCCT-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelComplianceTraceStateMatrixComplete = true` | SDPCCT-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道后续合规留痕截图与门禁 JSON 输出。
