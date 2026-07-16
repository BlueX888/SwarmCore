# 场景 Scenario Domain Push Channel Archive Viewport Light/Dark Screenshot 评审清单

> DOCS-074 / G123 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题推送通道后续归档独立截图抽检**，确保各域 section 在推送通道归档中态与归档完成态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md`（SDPCARCH-01～05）、`scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md`（SDPCCT-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续归档 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPCARCH 块 + `quality-rubric.md` |
| BI Analytics 指标推送通道后续归档 tablet/mobile light/dark 独立截图 | SDPCARCH-06 + `tailadmin-bi-analytics` |
| DevOps 阶段推送通道后续归档 tablet/mobile light/dark 独立截图 | SDPCARCH-07 + `scenario-devops` |
| Gateway 端点推送通道后续归档 tablet/mobile light/dark 独立截图 | SDPCARCH-08 + `scenario-gateway` |
| Governance 审计行推送通道后续归档 tablet/mobile light/dark 独立截图 | SDPCARCH-09 + `scenario-governance` |
| 场景域推送通道后续归档 tablet/mobile light/dark 独立截图束缺门禁 | SDPCARCH-10 + `verifyScenarioDomainPushChannelComplianceTraceViewportLightDarkScreenshots` + `verifyScenarioDomainPushChannelArchiveViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md` SDPCARCH-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-archive-pending,channel-archive-complete}.png` 共 40 张推送通道后续归档独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 推送通道后续归档独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续归档 tablet/mobile light/dark 独立截图（G123）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续归档 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPCARCH-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPCARCH-06 — BI Analytics 指标推送通道后续归档 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-channel-archive-pending.png`、`scenario-bi-domain-mobile-dark-channel-archive-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-archive-pending | `scenario-bi-domain-tablet-channel-archive-pending.png` + `scenario-bi-domain-tablet-dark-channel-archive-pending.png` channel-archive-pending framing 正常 | SDPCARCH-06 · RESP-06 |
| 2 | mobile light/dark channel-archive-complete | `scenario-bi-domain-mobile-channel-archive-complete.png` + `scenario-bi-domain-mobile-dark-channel-archive-complete.png` channel-archive-complete framing 正常 | SDPCARCH-06 · RESP-07 |
| 3 | 指标推送通道后续归档 | 归档 banner「推送通道后续归档中（历史事件排队）」+ 历史事件摘要 + 归档完成 banner「归档已完成，指标推送通道归档可审计，可继续接收实时变更事件」tablet/mobile light/dark 首屏可见 | SDPCARCH-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 channel-archive-pending banner 与 channel-archive-complete banner 层级可辨认 | SDPCARCH-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 channel-archive-pending/channel-archive-complete 截图全过 | SDPCARCH-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 channel-archive-pending 面板 → 点击「触发指标归档完成」→ 对照 tablet/mobile light/dark 八张推送通道后续归档截图。

## SDPCARCH-07 — DevOps 阶段推送通道后续归档 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-channel-archive-pending.png`、`scenario-devops-domain-mobile-dark-channel-archive-complete.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-archive-pending | `scenario-devops-domain-tablet-channel-archive-pending.png` + `scenario-devops-domain-tablet-dark-channel-archive-pending.png` channel-archive-pending framing 正常 | SDPCARCH-07 · RESP-06 |
| 2 | mobile light/dark channel-archive-complete | `scenario-devops-domain-mobile-channel-archive-complete.png` + `scenario-devops-domain-mobile-dark-channel-archive-complete.png` channel-archive-complete framing 正常 | SDPCARCH-07 · RESP-07 |
| 3 | 阶段推送通道后续归档 | 流水线归档 banner + 归档完成摘要 tablet/mobile light/dark 首屏可见 | SDPCARCH-07 · PAT-07 |
| 4 | channel-archive-complete 态 | mobile dark 下 channel-archive-complete 文案与「查看归档详情」按钮可辨认 | SDPCARCH-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 channel-archive-pending/channel-archive-complete 截图全过 | SDPCARCH-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 channel-archive-pending 面板 → 点击「触发阶段归档完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCARCH-08 — Gateway 端点推送通道后续归档 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-channel-archive-pending.png`、`scenario-gateway-domain-mobile-dark-channel-archive-complete.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-archive-pending | `scenario-gateway-domain-tablet-channel-archive-pending.png` + `scenario-gateway-domain-tablet-dark-channel-archive-pending.png` channel-archive-pending framing 正常 | SDPCARCH-08 · RESP-06 |
| 2 | mobile light/dark channel-archive-complete | `scenario-gateway-domain-mobile-channel-archive-complete.png` + `scenario-gateway-domain-mobile-dark-channel-archive-complete.png` channel-archive-complete framing 正常 | SDPCARCH-08 · RESP-07 |
| 3 | 端点推送通道后续归档 | 端点归档 banner + 归档完成摘要 tablet/mobile light/dark 首屏可见 | SDPCARCH-08 · PAT-08 |
| 4 | channel-archive-pending 态 | mobile dark 下历史事件摘要与归档 banner 可辨认 | SDPCARCH-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 channel-archive-pending/channel-archive-complete 截图全过 | SDPCARCH-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 channel-archive-pending 面板 → 点击「触发端点归档完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCARCH-09 — Governance 审计行推送通道后续归档 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-channel-archive-pending.png`、`scenario-governance-domain-mobile-channel-archive-pending.png`、`scenario-governance-domain-mobile-dark-channel-archive-complete.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark channel-archive-pending | `scenario-governance-domain-tablet-channel-archive-pending.png` + `scenario-governance-domain-tablet-dark-channel-archive-pending.png` channel-archive-pending framing 正常 | SDPCARCH-09 · RESP-06 |
| 2 | mobile light/dark channel-archive-complete | `scenario-governance-domain-mobile-channel-archive-complete.png` + `scenario-governance-domain-mobile-dark-channel-archive-complete.png` channel-archive-complete framing 正常 | SDPCARCH-09 · RESP-07 |
| 3 | 审计推送通道后续归档 | 合规归档 banner + 归档完成摘要 tablet/mobile light/dark 首屏可见 | SDPCARCH-09 · PAT-09 |
| 4 | channel-archive-complete 文案 | mobile dark 下「归档已完成，历史事件推送通道归档可审计，可继续提交策略变更」文案可辨认 | SDPCARCH-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 channel-archive-pending/channel-archive-complete 截图全过 | SDPCARCH-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 channel-archive-pending 面板 → 点击「触发合规归档完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCARCH-10 — 场景域推送通道后续归档 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{channel-archive-pending,channel-archive-complete}.png` + `scenarioDomainPushChannelArchiveViewportLightDarkScreenshotStates.pushChannelArchiveStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × channel-archive-pending/channel-archive-complete 全量 golden 存在 | SDPCARCH-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPushChannelArchiveViewportLightDarkScreenshots` 通过 | SDPCARCH-10 · PREVIEW-* |
| 3 | channel-archive-pending 态 | 五域 `data-audit="scenario-domain-channel-archive-pending-overlay"` `data-state="channel-archive-pending"` 可见 | SDPCARCH-10 · LOGIC-* |
| 4 | channel-archive-complete 态 | 五域点击归档完成 trigger 后 `role="status"` + `data-state="channel-archive-complete"` 可见 | SDPCARCH-10 · ASYNC-* |
| 5 | 矩阵完整 | `pushChannelArchiveStateMatrixComplete = true` | SDPCARCH-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张推送通道后续归档截图与门禁 JSON 输出。
