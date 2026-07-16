# 场景 Scenario Domain Websocket Reconnect Circuit Breaker Viewport Light/Dark Screenshot 评审清单

> DOCS-062 / G111 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题WebSocket 重连/熔断恢复独立截图抽检**，确保各域 section 在断连重试态与熔断闭合态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md`（SDWRCB-01～05）、`scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md`（SDNPR-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDWRCB 块 + `quality-rubric.md` |
| BI Analytics 指标WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图 | SDWRCB-06 + `tailadmin-bi-analytics` |
| DevOps 阶段WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图 | SDWRCB-07 + `scenario-devops` |
| Gateway 端点WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图 | SDWRCB-08 + `scenario-gateway` |
| Governance 审计行WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图 | SDWRCB-09 + `scenario-governance` |
| 场景域WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图束缺门禁 | SDWRCB-10 + `verify:runtime` `scenarioDomainDisconnectRetryHeartbeatViewportLightDarkScreenshotStates` + `verifyScenarioDomainWebsocketReconnectCircuitBreakerViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md` SDWRCB-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{reconnecting,circuit-closed}.png` 共 40 张WebSocket 重连/熔断恢复独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark WebSocket 重连/熔断恢复独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图（G111）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDWRCB-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDWRCB-06 — BI Analytics 指标WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-reconnecting.png`、`scenario-bi-domain-mobile-dark-circuit-closed.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark reconnecting | `scenario-bi-domain-tablet-reconnecting.png` + `scenario-bi-domain-tablet-dark-reconnecting.png` reconnecting framing 正常 | SDWRCB-06 · RESP-06 |
| 2 | mobile light/dark circuit-closed | `scenario-bi-domain-mobile-circuit-closed.png` + `scenario-bi-domain-mobile-dark-circuit-closed.png` restored framing 正常 | SDWRCB-06 · RESP-07 |
| 3 | 指标WebSocket 重连/熔断恢复 | 重试 banner + 心跳超时摘要 + 恢复完成 banner tablet/mobile light/dark 首屏可见 | SDWRCB-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 reconnecting banner 与 closed banner 层级可辨认 | SDWRCB-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 reconnecting/circuit-closed 截图全过 | SDWRCB-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 reconnecting 面板 → 点击「触发指标熔断闭合」→ 对照 tablet/mobile light/dark 八张WebSocket 重连/熔断恢复截图。

## SDWRCB-07 — DevOps 阶段WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-reconnecting.png`、`scenario-devops-domain-mobile-dark-circuit-closed.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark reconnecting | `scenario-devops-domain-tablet-reconnecting.png` + `scenario-devops-domain-tablet-dark-reconnecting.png` reconnecting framing 正常 | SDWRCB-07 · RESP-06 |
| 2 | mobile light/dark circuit-closed | `scenario-devops-domain-mobile-circuit-closed.png` + `scenario-devops-domain-mobile-dark-circuit-closed.png` restored framing 正常 | SDWRCB-07 · RESP-07 |
| 3 | 阶段WebSocket 重连/熔断恢复 | 流水线重试 banner + 熔断闭合摘要 tablet/mobile light/dark 首屏可见 | SDWRCB-07 · PAT-07 |
| 4 | restored 态 | mobile dark 下 restored 文案与查看详情按钮可辨认 | SDWRCB-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 reconnecting/circuit-closed 截图全过 | SDWRCB-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 reconnecting 面板 → 点击「触发阶段熔断闭合」→ 对照 tablet/mobile light/dark 八张截图。

## SDWRCB-08 — Gateway 端点WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-reconnecting.png`、`scenario-gateway-domain-mobile-dark-circuit-closed.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark reconnecting | `scenario-gateway-domain-tablet-reconnecting.png` + `scenario-gateway-domain-tablet-dark-reconnecting.png` reconnecting framing 正常 | SDWRCB-08 · RESP-06 |
| 2 | mobile light/dark circuit-closed | `scenario-gateway-domain-mobile-circuit-closed.png` + `scenario-gateway-domain-mobile-dark-circuit-closed.png` restored framing 正常 | SDWRCB-08 · RESP-07 |
| 3 | 端点WebSocket 重连/熔断恢复 | 端点重试 banner + 熔断闭合摘要 tablet/mobile light/dark 首屏可见 | SDWRCB-08 · PAT-08 |
| 4 | reconnecting 态 | mobile dark 下重试进度与 banner 可辨认 | SDWRCB-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 reconnecting/circuit-closed 截图全过 | SDWRCB-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 reconnecting 面板 → 点击「触发端点熔断闭合」→ 对照 tablet/mobile light/dark 八张截图。

## SDWRCB-09 — Governance 审计行WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-reconnecting.png`、`scenario-governance-domain-mobile-reconnecting.png`、`scenario-governance-domain-mobile-dark-circuit-closed.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark reconnecting | `scenario-governance-domain-tablet-reconnecting.png` + `scenario-governance-domain-tablet-dark-reconnecting.png` reconnecting framing 正常 | SDWRCB-09 · RESP-06 |
| 2 | mobile light/dark circuit-closed | `scenario-governance-domain-mobile-circuit-closed.png` + `scenario-governance-domain-mobile-dark-circuit-closed.png` restored framing 正常 | SDWRCB-09 · RESP-07 |
| 3 | 审计WebSocket 重连/熔断恢复 | 审计重试 banner + 熔断闭合摘要 tablet/mobile light/dark 首屏可见 | SDWRCB-09 · PAT-09 |
| 4 | restored 文案 | mobile dark 下「心跳已恢复，合规链路连接稳定，可继续提交策略变更」文案可辨认 | SDWRCB-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 reconnecting/circuit-closed 截图全过 | SDWRCB-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 reconnecting 面板 → 点击「触发审计熔断闭合」→ 对照 tablet/mobile light/dark 八张截图。

## SDWRCB-10 — 场景域WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{reconnecting,circuit-closed}.png` + `scenarioDomainWebsocketReconnectCircuitBreakerViewportLightDarkScreenshotStates.websocketReconnectCircuitBreakerStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × reconnecting/circuit-closed 全量 golden 存在 | SDWRCB-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainWebsocketReconnectCircuitBreakerViewportLightDarkScreenshots` 通过 | SDWRCB-10 · PREVIEW-* |
| 3 | reconnecting 态 | 五域 `data-audit="scenario-domain-reconnecting-overlay"` `data-state="reconnecting"` 可见 | SDWRCB-10 · LOGIC-* |
| 4 | circuit-closed 态 | 五域点击 circuit close trigger 后 `role="status"` + `data-state="circuit-closed"` 可见 | SDWRCB-10 · ASYNC-* |
| 5 | 矩阵完整 | `websocketReconnectCircuitBreakerStateMatrixComplete = true` | SDWRCB-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张WebSocket 重连/熔断恢复截图与门禁 JSON 输出。
