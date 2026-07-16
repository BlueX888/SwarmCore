# Scenario Domain SSE Reconnect Backpressure Viewport Light/Dark Screenshot 评审清单

> DOCS-063 / G112 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 SSE 重连/背压释放独立截图视觉回归抽检**，确保每个场景 section 在 SSE 重连态、背压释放态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md`（SDWRCB-01～05）、`scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md`（SDSRB-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图抽检 | 对应 SDSRB 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标 SSE 重连/背压释放 tablet/mobile light/dark golden 对照 | SDSRB-01 + `scenario-bi-domain-tablet-sse-reconnecting.png` + `scenario-bi-domain-mobile-dark-backpressure-released.png` |
| DevOps 场景阶段 SSE 重连/背压释放 tablet/mobile light/dark golden 对照 | SDSRB-02 + `scenario-devops-domain-tablet-sse-reconnecting.png` + `scenario-devops-domain-mobile-dark-backpressure-released.png` |
| Gateway 场景端点 SSE 重连/背压释放 tablet/mobile light/dark golden 对照 | SDSRB-03 + `scenario-gateway-domain-tablet-sse-reconnecting.png` + `scenario-gateway-domain-mobile-dark-backpressure-released.png` |
| Governance 场景审计行 SSE 重连/背压释放 tablet/mobile light/dark golden 对照 | SDSRB-04 + `scenario-governance-domain-tablet-sse-reconnecting.png` + `scenario-governance-domain-mobile-dark-backpressure-released.png` |
| PaaS 场景容量 SSE 重连/背压释放 tablet/mobile light/dark golden 对照 | SDSRB-05 + `scenario-paas-domain-tablet-sse-reconnecting.png` + `scenario-paas-domain-mobile-dark-backpressure-released.png` |

## 通用前置

1. 先完成 `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md` SDWRCB-01～05（WebSocket 重连/熔断恢复 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{sse-reconnecting,backpressure-released}.png` 四视口双主题 SSE 重连/背压释放独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 sse-reconnecting 与一张 backpressure-released 独立截图；sse-reconnecting 必须出现重连 banner 与背压队列摘要，backpressure-released 必须出现释放 banner 与查看重连详情 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. SSE 重连/背压释放截图出现文案裁切、重连 banner 对比度不足、released banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图（G112）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图抽检行。

## SDSRB-01 — BI 场景指标 SSE 重连/背压释放 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-sse-reconnecting.png`、`scenario-bi-domain-tablet-dark-sse-reconnecting.png`、`scenario-bi-domain-mobile-sse-reconnecting.png`、`scenario-bi-domain-mobile-dark-sse-reconnecting.png`、`scenario-bi-domain-tablet-backpressure-released.png`、`scenario-bi-domain-tablet-dark-backpressure-released.png`、`scenario-bi-domain-mobile-backpressure-released.png`、`scenario-bi-domain-mobile-dark-backpressure-released.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light sse-reconnecting 截图 | `scenario-bi-domain-tablet-sse-reconnecting.png` 存在且 sse-reconnecting framing 正常 | SDSRB-01 · RESP-06 |
| 2 | tablet dark sse-reconnecting 截图 | `scenario-bi-domain-tablet-dark-sse-reconnecting.png` 存在且重连 banner 可读 | SDSRB-01 · VIS-05 |
| 3 | mobile light backpressure-released 截图 | `scenario-bi-domain-mobile-backpressure-released.png` released banner 首屏可见 | SDSRB-01 · RESP-07 |
| 4 | mobile dark backpressure-released 截图 | `scenario-bi-domain-mobile-dark-backpressure-released.png` released 对比度可辨认 | SDSRB-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainSseReconnectBackpressureViewportLightDarkScreenshots` biDomain 全过 | SDSRB-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 sse-reconnecting 面板 → 点击「触发指标背压释放」→ 对照 tablet/mobile light/dark 八张 sse-reconnecting/backpressure-released 截图。

## SDSRB-02 — DevOps 场景阶段 SSE 重连/背压释放 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-sse-reconnecting.png`、`scenario-devops-domain-tablet-dark-sse-reconnecting.png`、`scenario-devops-domain-mobile-sse-reconnecting.png`、`scenario-devops-domain-mobile-dark-sse-reconnecting.png`、`scenario-devops-domain-tablet-backpressure-released.png`、`scenario-devops-domain-tablet-dark-backpressure-released.png`、`scenario-devops-domain-mobile-backpressure-released.png`、`scenario-devops-domain-mobile-dark-backpressure-released.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light sse-reconnecting 截图 | `scenario-devops-domain-tablet-sse-reconnecting.png` 存在且 sse-reconnecting framing 正常 | SDSRB-02 · RESP-06 |
| 2 | tablet dark sse-reconnecting 截图 | `scenario-devops-domain-tablet-dark-sse-reconnecting.png` 存在且背压队列摘要可读 | SDSRB-02 · VIS-05 |
| 3 | mobile light backpressure-released 截图 | `scenario-devops-domain-mobile-backpressure-released.png` 流水线 released 首屏可见 | SDSRB-02 · RESP-07 |
| 4 | mobile dark backpressure-released 截图 | `scenario-devops-domain-mobile-dark-backpressure-released.png` released 对比度可辨认 | SDSRB-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + SSE 重连/背压释放 tablet/mobile light/dark 可见 | SDSRB-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 sse-reconnecting 面板 → 点击「触发阶段背压释放」→ 对照 tablet/mobile light/dark 八张截图。

## SDSRB-03 — Gateway 场景端点 SSE 重连/背压释放 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-sse-reconnecting.png`、`scenario-gateway-domain-tablet-dark-sse-reconnecting.png`、`scenario-gateway-domain-mobile-sse-reconnecting.png`、`scenario-gateway-domain-mobile-dark-sse-reconnecting.png`、`scenario-gateway-domain-tablet-backpressure-released.png`、`scenario-gateway-domain-tablet-dark-backpressure-released.png`、`scenario-gateway-domain-mobile-backpressure-released.png`、`scenario-gateway-domain-mobile-dark-backpressure-released.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light sse-reconnecting 截图 | `scenario-gateway-domain-tablet-sse-reconnecting.png` 存在且 sse-reconnecting framing 正常 | SDSRB-03 · RESP-06 |
| 2 | tablet dark sse-reconnecting 截图 | `scenario-gateway-domain-tablet-dark-sse-reconnecting.png` 存在且背压队列摘要可读 | SDSRB-03 · VIS-05 |
| 3 | mobile light backpressure-released 截图 | `scenario-gateway-domain-mobile-backpressure-released.png` 端点 released 首屏可见 | SDSRB-03 · RESP-07 |
| 4 | mobile dark backpressure-released 截图 | `scenario-gateway-domain-mobile-dark-backpressure-released.png` released 层级不丢失 | SDSRB-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + SSE 重连/背压释放 tablet/mobile light/dark 可见 | SDSRB-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 sse-reconnecting 面板 → 点击「触发端点背压释放」→ 对照 tablet/mobile light/dark 八张截图。

## SDSRB-04 — Governance 场景审计行 SSE 重连/背压释放 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-sse-reconnecting.png`、`scenario-governance-domain-tablet-dark-sse-reconnecting.png`、`scenario-governance-domain-mobile-sse-reconnecting.png`、`scenario-governance-domain-mobile-dark-sse-reconnecting.png`、`scenario-governance-domain-tablet-backpressure-released.png`、`scenario-governance-domain-tablet-dark-backpressure-released.png`、`scenario-governance-domain-mobile-backpressure-released.png`、`scenario-governance-domain-mobile-dark-backpressure-released.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light sse-reconnecting 截图 | `scenario-governance-domain-tablet-sse-reconnecting.png` 存在且 sse-reconnecting framing 正常 | SDSRB-04 · RESP-06 |
| 2 | tablet dark sse-reconnecting 截图 | `scenario-governance-domain-tablet-dark-sse-reconnecting.png` 存在且背压队列摘要可读 | SDSRB-04 · VIS-05 |
| 3 | mobile light backpressure-released 截图 | `scenario-governance-domain-mobile-backpressure-released.png` 审计 released 首屏可见 | SDSRB-04 · RESP-07 |
| 4 | mobile dark backpressure-released 截图 | `scenario-governance-domain-mobile-dark-backpressure-released.png` released 密度一致 | SDSRB-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + SSE 重连/背压释放 tablet/mobile light/dark 可见 | SDSRB-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 sse-reconnecting 面板 → 点击「触发审计背压释放」→ 对照 tablet/mobile light/dark 八张截图。

## SDSRB-05 — PaaS 场景容量 SSE 重连/背压释放 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-sse-reconnecting.png`、`scenario-paas-domain-tablet-dark-sse-reconnecting.png`、`scenario-paas-domain-mobile-sse-reconnecting.png`、`scenario-paas-domain-mobile-dark-sse-reconnecting.png`、`scenario-paas-domain-tablet-backpressure-released.png`、`scenario-paas-domain-tablet-dark-backpressure-released.png`、`scenario-paas-domain-mobile-backpressure-released.png`、`scenario-paas-domain-mobile-dark-backpressure-released.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light sse-reconnecting 截图 | `scenario-paas-domain-tablet-sse-reconnecting.png` 存在且 sse-reconnecting framing 正常 | SDSRB-05 · RESP-06 |
| 2 | tablet dark sse-reconnecting 截图 | `scenario-paas-domain-tablet-dark-sse-reconnecting.png` 存在且背压队列摘要可读 | SDSRB-05 · VIS-05 |
| 3 | mobile light backpressure-released 截图 | `scenario-paas-domain-mobile-backpressure-released.png` 容量 released 首屏可见 | SDSRB-05 · RESP-07 |
| 4 | mobile dark backpressure-released 截图 | `scenario-paas-domain-mobile-dark-backpressure-released.png` released 列表项可辨认 | SDSRB-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + SSE 重连/背压释放 tablet/mobile light/dark 可见 | SDSRB-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 sse-reconnecting 面板 → 点击「触发容量背压释放」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md` SDSRB-06～10
- WebSocket 重连/熔断恢复 前置：`scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md` SDWRCB-01～05
- 选型表：`decision-matrix.md` G112 场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDSRB-01～10
- Runtime 门禁：`verifyScenarioDomainSseReconnectBackpressureViewportLightDarkScreenshots`
