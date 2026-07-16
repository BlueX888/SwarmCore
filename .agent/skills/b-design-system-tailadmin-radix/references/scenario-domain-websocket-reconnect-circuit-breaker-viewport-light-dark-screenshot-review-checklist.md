# Scenario Domain Websocket Reconnect Circuit Breaker Viewport Light/Dark Screenshot 评审清单

> DOCS-062 / G111 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题WebSocket 重连/熔断恢复独立截图视觉回归抽检**，确保每个场景 section 在断连重试态、心跳恢复态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md`（SDRHT-01～05）、`scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md`（SDWRCB-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图抽检 | 对应 SDWRCB 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标WebSocket 重连/熔断恢复 tablet/mobile light/dark golden 对照 | SDWRCB-01 + `scenario-bi-domain-tablet-reconnecting.png` + `scenario-bi-domain-mobile-dark-circuit-closed.png` |
| DevOps 场景阶段WebSocket 重连/熔断恢复 tablet/mobile light/dark golden 对照 | SDWRCB-02 + `scenario-devops-domain-tablet-reconnecting.png` + `scenario-devops-domain-mobile-dark-circuit-closed.png` |
| Gateway 场景端点WebSocket 重连/熔断恢复 tablet/mobile light/dark golden 对照 | SDWRCB-03 + `scenario-gateway-domain-tablet-reconnecting.png` + `scenario-gateway-domain-mobile-dark-circuit-closed.png` |
| Governance 场景审计行WebSocket 重连/熔断恢复 tablet/mobile light/dark golden 对照 | SDWRCB-04 + `scenario-governance-domain-tablet-reconnecting.png` + `scenario-governance-domain-mobile-dark-circuit-closed.png` |
| PaaS 场景容量WebSocket 重连/熔断恢复 tablet/mobile light/dark golden 对照 | SDWRCB-05 + `scenario-paas-domain-tablet-reconnecting.png` + `scenario-paas-domain-mobile-dark-circuit-closed.png` |

## 通用前置

1. 先完成 `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md` SDRHT-01～05（断连重试/心跳超时 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{reconnecting,circuit-closed}.png` 四视口双主题WebSocket 重连/熔断恢复独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 retrying 与一张 heartbeat-restored 独立截图；reconnecting 必须出现 reconnecting banner 与重连进度摘要，circuit-closed 必须出现 closed banner 与查看重连详情 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. WebSocket 重连/熔断恢复截图出现文案裁切、重试 banner 对比度不足、closed banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图（G111）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图抽检行。

## SDWRCB-01 — BI 场景指标WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-reconnecting.png`、`scenario-bi-domain-tablet-dark-reconnecting.png`、`scenario-bi-domain-mobile-reconnecting.png`、`scenario-bi-domain-mobile-dark-reconnecting.png`、`scenario-bi-domain-tablet-circuit-closed.png`、`scenario-bi-domain-tablet-dark-circuit-closed.png`、`scenario-bi-domain-mobile-circuit-closed.png`、`scenario-bi-domain-mobile-dark-circuit-closed.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retrying 截图 | `scenario-bi-domain-tablet-reconnecting.png` 存在且 retrying framing 正常 | SDWRCB-01 · RESP-06 |
| 2 | tablet dark retrying 截图 | `scenario-bi-domain-tablet-dark-reconnecting.png` 存在且重试 banner 可读 | SDWRCB-01 · VIS-05 |
| 3 | mobile light heartbeat-restored 截图 | `scenario-bi-domain-mobile-circuit-closed.png` closed banner 首屏可见 | SDWRCB-01 · RESP-07 |
| 4 | mobile dark heartbeat-restored 截图 | `scenario-bi-domain-mobile-dark-circuit-closed.png` restored 对比度可辨认 | SDWRCB-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainWebsocketReconnectCircuitBreakerViewportLightDarkScreenshots` biDomain 全过 | SDWRCB-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 retrying 面板 → 点击「触发指标心跳恢复」→ 对照 tablet/mobile light/dark 八张 reconnecting/circuit-closed 截图。

## SDWRCB-02 — DevOps 场景阶段WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-reconnecting.png`、`scenario-devops-domain-tablet-dark-reconnecting.png`、`scenario-devops-domain-mobile-reconnecting.png`、`scenario-devops-domain-mobile-dark-reconnecting.png`、`scenario-devops-domain-tablet-circuit-closed.png`、`scenario-devops-domain-tablet-dark-circuit-closed.png`、`scenario-devops-domain-mobile-circuit-closed.png`、`scenario-devops-domain-mobile-dark-circuit-closed.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retrying 截图 | `scenario-devops-domain-tablet-reconnecting.png` 存在且 retrying framing 正常 | SDWRCB-02 · RESP-06 |
| 2 | tablet dark retrying 截图 | `scenario-devops-domain-tablet-dark-reconnecting.png` 存在且重连进度可读 | SDWRCB-02 · VIS-05 |
| 3 | mobile light heartbeat-restored 截图 | `scenario-devops-domain-mobile-circuit-closed.png` 流水线 closed 首屏可见 | SDWRCB-02 · RESP-07 |
| 4 | mobile dark heartbeat-restored 截图 | `scenario-devops-domain-mobile-dark-circuit-closed.png` restored 对比度可辨认 | SDWRCB-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + WebSocket 重连/熔断恢复 tablet/mobile light/dark 可见 | SDWRCB-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 retrying 面板 → 点击「触发阶段心跳恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDWRCB-03 — Gateway 场景端点WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-reconnecting.png`、`scenario-gateway-domain-tablet-dark-reconnecting.png`、`scenario-gateway-domain-mobile-reconnecting.png`、`scenario-gateway-domain-mobile-dark-reconnecting.png`、`scenario-gateway-domain-tablet-circuit-closed.png`、`scenario-gateway-domain-tablet-dark-circuit-closed.png`、`scenario-gateway-domain-mobile-circuit-closed.png`、`scenario-gateway-domain-mobile-dark-circuit-closed.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retrying 截图 | `scenario-gateway-domain-tablet-reconnecting.png` 存在且 retrying framing 正常 | SDWRCB-03 · RESP-06 |
| 2 | tablet dark retrying 截图 | `scenario-gateway-domain-tablet-dark-reconnecting.png` 存在且重连进度可读 | SDWRCB-03 · VIS-05 |
| 3 | mobile light heartbeat-restored 截图 | `scenario-gateway-domain-mobile-circuit-closed.png` 端点 closed 首屏可见 | SDWRCB-03 · RESP-07 |
| 4 | mobile dark heartbeat-restored 截图 | `scenario-gateway-domain-mobile-dark-circuit-closed.png` restored 层级不丢失 | SDWRCB-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + WebSocket 重连/熔断恢复 tablet/mobile light/dark 可见 | SDWRCB-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 retrying 面板 → 点击「触发端点心跳恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDWRCB-04 — Governance 场景审计行WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-reconnecting.png`、`scenario-governance-domain-tablet-dark-reconnecting.png`、`scenario-governance-domain-mobile-reconnecting.png`、`scenario-governance-domain-mobile-dark-reconnecting.png`、`scenario-governance-domain-tablet-circuit-closed.png`、`scenario-governance-domain-tablet-dark-circuit-closed.png`、`scenario-governance-domain-mobile-circuit-closed.png`、`scenario-governance-domain-mobile-dark-circuit-closed.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retrying 截图 | `scenario-governance-domain-tablet-reconnecting.png` 存在且 retrying framing 正常 | SDWRCB-04 · RESP-06 |
| 2 | tablet dark retrying 截图 | `scenario-governance-domain-tablet-dark-reconnecting.png` 存在且重连进度可读 | SDWRCB-04 · VIS-05 |
| 3 | mobile light heartbeat-restored 截图 | `scenario-governance-domain-mobile-circuit-closed.png` 审计 closed 首屏可见 | SDWRCB-04 · RESP-07 |
| 4 | mobile dark heartbeat-restored 截图 | `scenario-governance-domain-mobile-dark-circuit-closed.png` restored 密度一致 | SDWRCB-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + WebSocket 重连/熔断恢复 tablet/mobile light/dark 可见 | SDWRCB-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 retrying 面板 → 点击「触发审计心跳恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDWRCB-05 — PaaS 场景容量WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-reconnecting.png`、`scenario-paas-domain-tablet-dark-reconnecting.png`、`scenario-paas-domain-mobile-reconnecting.png`、`scenario-paas-domain-mobile-dark-reconnecting.png`、`scenario-paas-domain-tablet-circuit-closed.png`、`scenario-paas-domain-tablet-dark-circuit-closed.png`、`scenario-paas-domain-mobile-circuit-closed.png`、`scenario-paas-domain-mobile-dark-circuit-closed.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retrying 截图 | `scenario-paas-domain-tablet-reconnecting.png` 存在且 retrying framing 正常 | SDWRCB-05 · RESP-06 |
| 2 | tablet dark retrying 截图 | `scenario-paas-domain-tablet-dark-reconnecting.png` 存在且重连进度可读 | SDWRCB-05 · VIS-05 |
| 3 | mobile light heartbeat-restored 截图 | `scenario-paas-domain-mobile-circuit-closed.png` 容量 closed 首屏可见 | SDWRCB-05 · RESP-07 |
| 4 | mobile dark heartbeat-restored 截图 | `scenario-paas-domain-mobile-dark-circuit-closed.png` restored 列表项可辨认 | SDWRCB-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + WebSocket 重连/熔断恢复 tablet/mobile light/dark 可见 | SDWRCB-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 retrying 面板 → 点击「触发容量心跳恢复」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md` SDWRCB-06～10
- 断连重试/心跳超时 前置：`scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md` SDRHT-01～05
- 选型表：`decision-matrix.md` G110 场景域WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDWRCB-01～10
- Runtime 门禁：`verifyScenarioDomainWebsocketReconnectCircuitBreakerViewportLightDarkScreenshots`
