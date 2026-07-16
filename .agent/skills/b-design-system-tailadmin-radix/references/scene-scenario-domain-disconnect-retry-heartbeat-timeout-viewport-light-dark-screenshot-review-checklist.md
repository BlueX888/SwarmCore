# 场景 Scenario Domain Disconnect Retry Heartbeat Timeout Viewport Light/Dark Screenshot 评审清单

> DOCS-061 / G110 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题断连重试/心跳超时独立截图抽检**，确保各域 section 在断连重试态与心跳恢复态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md`（SDRHT-01～05）、`scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDNPR-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDRHT 块 + `quality-rubric.md` |
| BI Analytics 指标断连重试/心跳超时 tablet/mobile light/dark 独立截图 | SDRHT-06 + `tailadmin-bi-analytics` |
| DevOps 阶段断连重试/心跳超时 tablet/mobile light/dark 独立截图 | SDRHT-07 + `scenario-devops` |
| Gateway 端点断连重试/心跳超时 tablet/mobile light/dark 独立截图 | SDRHT-08 + `scenario-gateway` |
| Governance 审计行断连重试/心跳超时 tablet/mobile light/dark 独立截图 | SDRHT-09 + `scenario-governance` |
| 场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图束缺门禁 | SDRHT-10 + `verify:runtime` `scenarioDomainDisconnectRetryHeartbeatViewportLightDarkScreenshotStates` + `verifyScenarioDomainDisconnectRetryHeartbeatViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md` SDRHT-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{retrying,heartbeat-restored}.png` 共 40 张断连重试/心跳超时独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 断连重试/心跳超时独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图（G110）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDRHT-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDRHT-06 — BI Analytics 指标断连重试/心跳超时 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-retrying.png`、`scenario-bi-domain-mobile-dark-heartbeat-restored.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark retrying | `scenario-bi-domain-tablet-retrying.png` + `scenario-bi-domain-tablet-dark-retrying.png` retrying framing 正常 | SDRHT-06 · RESP-06 |
| 2 | mobile light/dark heartbeat-restored | `scenario-bi-domain-mobile-heartbeat-restored.png` + `scenario-bi-domain-mobile-dark-heartbeat-restored.png` restored framing 正常 | SDRHT-06 · RESP-07 |
| 3 | 指标断连重试/心跳超时 | 重试 banner + 心跳超时摘要 + 恢复完成 banner tablet/mobile light/dark 首屏可见 | SDRHT-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 retrying banner 与 restored banner 层级可辨认 | SDRHT-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 retrying/heartbeat-restored 截图全过 | SDRHT-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 retrying 面板 → 点击「触发指标心跳恢复」→ 对照 tablet/mobile light/dark 八张断连重试/心跳超时截图。

## SDRHT-07 — DevOps 阶段断连重试/心跳超时 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-retrying.png`、`scenario-devops-domain-mobile-dark-heartbeat-restored.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark retrying | `scenario-devops-domain-tablet-retrying.png` + `scenario-devops-domain-tablet-dark-retrying.png` retrying framing 正常 | SDRHT-07 · RESP-06 |
| 2 | mobile light/dark heartbeat-restored | `scenario-devops-domain-mobile-heartbeat-restored.png` + `scenario-devops-domain-mobile-dark-heartbeat-restored.png` restored framing 正常 | SDRHT-07 · RESP-07 |
| 3 | 阶段断连重试/心跳超时 | 流水线重试 banner + 心跳恢复摘要 tablet/mobile light/dark 首屏可见 | SDRHT-07 · PAT-07 |
| 4 | restored 态 | mobile dark 下 restored 文案与查看详情按钮可辨认 | SDRHT-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 retrying/heartbeat-restored 截图全过 | SDRHT-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 retrying 面板 → 点击「触发阶段心跳恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDRHT-08 — Gateway 端点断连重试/心跳超时 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-retrying.png`、`scenario-gateway-domain-mobile-dark-heartbeat-restored.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark retrying | `scenario-gateway-domain-tablet-retrying.png` + `scenario-gateway-domain-tablet-dark-retrying.png` retrying framing 正常 | SDRHT-08 · RESP-06 |
| 2 | mobile light/dark heartbeat-restored | `scenario-gateway-domain-mobile-heartbeat-restored.png` + `scenario-gateway-domain-mobile-dark-heartbeat-restored.png` restored framing 正常 | SDRHT-08 · RESP-07 |
| 3 | 端点断连重试/心跳超时 | 端点重试 banner + 心跳恢复摘要 tablet/mobile light/dark 首屏可见 | SDRHT-08 · PAT-08 |
| 4 | retrying 态 | mobile dark 下重试进度与 banner 可辨认 | SDRHT-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 retrying/heartbeat-restored 截图全过 | SDRHT-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 retrying 面板 → 点击「触发端点心跳恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDRHT-09 — Governance 审计行断连重试/心跳超时 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-retrying.png`、`scenario-governance-domain-mobile-retrying.png`、`scenario-governance-domain-mobile-dark-heartbeat-restored.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark retrying | `scenario-governance-domain-tablet-retrying.png` + `scenario-governance-domain-tablet-dark-retrying.png` retrying framing 正常 | SDRHT-09 · RESP-06 |
| 2 | mobile light/dark heartbeat-restored | `scenario-governance-domain-mobile-heartbeat-restored.png` + `scenario-governance-domain-mobile-dark-heartbeat-restored.png` restored framing 正常 | SDRHT-09 · RESP-07 |
| 3 | 审计断连重试/心跳超时 | 审计重试 banner + 心跳恢复摘要 tablet/mobile light/dark 首屏可见 | SDRHT-09 · PAT-09 |
| 4 | restored 文案 | mobile dark 下「心跳已恢复，合规链路连接稳定，可继续提交策略变更」文案可辨认 | SDRHT-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 retrying/heartbeat-restored 截图全过 | SDRHT-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 retrying 面板 → 点击「触发审计心跳恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDRHT-10 — 场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{retrying,heartbeat-restored}.png` + `scenarioDomainDisconnectRetryHeartbeatViewportLightDarkScreenshotStates.disconnectRetryHeartbeatStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × retrying/heartbeat-restored 全量 golden 存在 | SDRHT-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainDisconnectRetryHeartbeatViewportLightDarkScreenshots` 通过 | SDRHT-10 · PREVIEW-* |
| 3 | retrying 态 | 五域 `data-audit="scenario-domain-retrying-overlay"` `data-state="retrying"` 可见 | SDRHT-10 · LOGIC-* |
| 4 | heartbeat-restored 态 | 五域点击 heartbeat trigger 后 `role="status"` + `data-state="heartbeat-restored"` 可见 | SDRHT-10 · ASYNC-* |
| 5 | 矩阵完整 | `disconnectRetryHeartbeatStateMatrixComplete = true` | SDRHT-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张断连重试/心跳超时截图与门禁 JSON 输出。
