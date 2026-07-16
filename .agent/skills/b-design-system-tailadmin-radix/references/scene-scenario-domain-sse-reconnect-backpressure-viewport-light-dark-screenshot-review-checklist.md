# 场景 Scenario Domain SSE Reconnect Backpressure Viewport Light/Dark Screenshot 评审清单

> DOCS-063 / G112 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 SSE 重连/背压释放独立截图抽检**，确保各域 section 在 SSE 重连态与背压释放态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md`（SDSRB-01～05）、`scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md`（SDWRCB-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDSRB 块 + `quality-rubric.md` |
| BI Analytics 指标 SSE 重连/背压释放 tablet/mobile light/dark 独立截图 | SDSRB-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 SSE 重连/背压释放 tablet/mobile light/dark 独立截图 | SDSRB-07 + `scenario-devops` |
| Gateway 端点 SSE 重连/背压释放 tablet/mobile light/dark 独立截图 | SDSRB-08 + `scenario-gateway` |
| Governance 审计行 SSE 重连/背压释放 tablet/mobile light/dark 独立截图 | SDSRB-09 + `scenario-governance` |
| 场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图束缺门禁 | SDSRB-10 + `verify:runtime` `scenarioDomainWebsocketReconnectCircuitBreakerViewportLightDarkScreenshotStates` + `verifyScenarioDomainSseReconnectBackpressureViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md` SDSRB-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{sse-reconnecting,backpressure-released}.png` 共 40 张 SSE 重连/背压释放独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark SSE 重连/背压释放独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图（G112）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDSRB-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDSRB-06 — BI Analytics 指标 SSE 重连/背压释放 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-sse-reconnecting.png`、`scenario-bi-domain-mobile-dark-backpressure-released.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark sse-reconnecting | `scenario-bi-domain-tablet-sse-reconnecting.png` + `scenario-bi-domain-tablet-dark-sse-reconnecting.png` sse-reconnecting framing 正常 | SDSRB-06 · RESP-06 |
| 2 | mobile light/dark backpressure-released | `scenario-bi-domain-mobile-backpressure-released.png` + `scenario-bi-domain-mobile-dark-backpressure-released.png` released framing 正常 | SDSRB-06 · RESP-07 |
| 3 | 指标 SSE 重连/背压释放 | 重连 banner + 背压队列摘要 + 释放完成 banner tablet/mobile light/dark 首屏可见 | SDSRB-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 sse-reconnecting banner 与 released banner 层级可辨认 | SDSRB-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 sse-reconnecting/backpressure-released 截图全过 | SDSRB-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 sse-reconnecting 面板 → 点击「触发指标背压释放」→ 对照 tablet/mobile light/dark 八张 SSE 重连/背压释放截图。

## SDSRB-07 — DevOps 阶段 SSE 重连/背压释放 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-sse-reconnecting.png`、`scenario-devops-domain-mobile-dark-backpressure-released.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark sse-reconnecting | `scenario-devops-domain-tablet-sse-reconnecting.png` + `scenario-devops-domain-tablet-dark-sse-reconnecting.png` sse-reconnecting framing 正常 | SDSRB-07 · RESP-06 |
| 2 | mobile light/dark backpressure-released | `scenario-devops-domain-mobile-backpressure-released.png` + `scenario-devops-domain-mobile-dark-backpressure-released.png` released framing 正常 | SDSRB-07 · RESP-07 |
| 3 | 阶段 SSE 重连/背压释放 | 流水线重连 banner + 背压释放摘要 tablet/mobile light/dark 首屏可见 | SDSRB-07 · PAT-07 |
| 4 | released 态 | mobile dark 下 released 文案与查看详情按钮可辨认 | SDSRB-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 sse-reconnecting/backpressure-released 截图全过 | SDSRB-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 sse-reconnecting 面板 → 点击「触发阶段背压释放」→ 对照 tablet/mobile light/dark 八张截图。

## SDSRB-08 — Gateway 端点 SSE 重连/背压释放 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-sse-reconnecting.png`、`scenario-gateway-domain-mobile-dark-backpressure-released.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark sse-reconnecting | `scenario-gateway-domain-tablet-sse-reconnecting.png` + `scenario-gateway-domain-tablet-dark-sse-reconnecting.png` sse-reconnecting framing 正常 | SDSRB-08 · RESP-06 |
| 2 | mobile light/dark backpressure-released | `scenario-gateway-domain-mobile-backpressure-released.png` + `scenario-gateway-domain-mobile-dark-backpressure-released.png` released framing 正常 | SDSRB-08 · RESP-07 |
| 3 | 端点 SSE 重连/背压释放 | 端点重连 banner + 背压释放摘要 tablet/mobile light/dark 首屏可见 | SDSRB-08 · PAT-08 |
| 4 | sse-reconnecting 态 | mobile dark 下重连进度与 banner 可辨认 | SDSRB-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 sse-reconnecting/backpressure-released 截图全过 | SDSRB-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 sse-reconnecting 面板 → 点击「触发端点背压释放」→ 对照 tablet/mobile light/dark 八张截图。

## SDSRB-09 — Governance 审计行 SSE 重连/背压释放 tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-sse-reconnecting.png`、`scenario-governance-domain-mobile-sse-reconnecting.png`、`scenario-governance-domain-mobile-dark-backpressure-released.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark sse-reconnecting | `scenario-governance-domain-tablet-sse-reconnecting.png` + `scenario-governance-domain-tablet-dark-sse-reconnecting.png` sse-reconnecting framing 正常 | SDSRB-09 · RESP-06 |
| 2 | mobile light/dark backpressure-released | `scenario-governance-domain-mobile-backpressure-released.png` + `scenario-governance-domain-mobile-dark-backpressure-released.png` released framing 正常 | SDSRB-09 · RESP-07 |
| 3 | 审计 SSE 重连/背压释放 | 审计重连 banner + 背压释放摘要 tablet/mobile light/dark 首屏可见 | SDSRB-09 · PAT-09 |
| 4 | released 文案 | mobile dark 下「背压已释放，合规事件流式通道稳定，可继续提交策略变更」文案可辨认 | SDSRB-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 sse-reconnecting/backpressure-released 截图全过 | SDSRB-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 sse-reconnecting 面板 → 点击「触发审计背压释放」→ 对照 tablet/mobile light/dark 八张截图。

## SDSRB-10 — 场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{sse-reconnecting,backpressure-released}.png` + `scenarioDomainSseReconnectBackpressureViewportLightDarkScreenshotStates.sseReconnectBackpressureStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × sse-reconnecting/backpressure-released 全量 golden 存在 | SDSRB-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainSseReconnectBackpressureViewportLightDarkScreenshots` 通过 | SDSRB-10 · PREVIEW-* |
| 3 | sse-reconnecting 态 | 五域 `data-audit="scenario-domain-sse-reconnecting-overlay"` `data-state="sse-reconnecting"` 可见 | SDSRB-10 · LOGIC-* |
| 4 | backpressure-released 态 | 五域点击 backpressure release trigger 后 `role="status"` + `data-state="backpressure-released"` 可见 | SDSRB-10 · ASYNC-* |
| 5 | 矩阵完整 | `sseReconnectBackpressureStateMatrixComplete = true` | SDSRB-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张 SSE 重连/背压释放截图与门禁 JSON 输出。
