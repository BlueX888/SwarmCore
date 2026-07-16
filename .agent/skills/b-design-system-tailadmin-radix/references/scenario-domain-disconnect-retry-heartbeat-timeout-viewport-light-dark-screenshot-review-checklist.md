# Scenario Domain Disconnect Retry Heartbeat Timeout Viewport Light/Dark Screenshot 评审清单

> DOCS-061 / G110 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题断连重试/心跳超时独立截图视觉回归抽检**，确保每个场景 section 在断连重试态、心跳恢复态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDNPR-01～05）、`scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md`（SDRHT-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图抽检 | 对应 SDRHT 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标断连重试/心跳超时 tablet/mobile light/dark golden 对照 | SDRHT-01 + `scenario-bi-domain-tablet-retrying.png` + `scenario-bi-domain-mobile-dark-heartbeat-restored.png` |
| DevOps 场景阶段断连重试/心跳超时 tablet/mobile light/dark golden 对照 | SDRHT-02 + `scenario-devops-domain-tablet-retrying.png` + `scenario-devops-domain-mobile-dark-heartbeat-restored.png` |
| Gateway 场景端点断连重试/心跳超时 tablet/mobile light/dark golden 对照 | SDRHT-03 + `scenario-gateway-domain-tablet-retrying.png` + `scenario-gateway-domain-mobile-dark-heartbeat-restored.png` |
| Governance 场景审计行断连重试/心跳超时 tablet/mobile light/dark golden 对照 | SDRHT-04 + `scenario-governance-domain-tablet-retrying.png` + `scenario-governance-domain-mobile-dark-heartbeat-restored.png` |
| PaaS 场景容量断连重试/心跳超时 tablet/mobile light/dark golden 对照 | SDRHT-05 + `scenario-paas-domain-tablet-retrying.png` + `scenario-paas-domain-mobile-dark-heartbeat-restored.png` |

## 通用前置

1. 先完成 `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md` SDNPR-01～05（network partition/recovery 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{retrying,heartbeat-restored}.png` 四视口双主题断连重试/心跳超时独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 retrying 与一张 heartbeat-restored 独立截图；retrying 必须出现 retrying banner 与重试进度摘要，heartbeat-restored 必须出现 restored banner 与查看重试详情 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 断连重试/心跳超时截图出现文案裁切、重试 banner 对比度不足、restored banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图（G110）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图抽检行。

## SDRHT-01 — BI 场景指标断连重试/心跳超时 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-retrying.png`、`scenario-bi-domain-tablet-dark-retrying.png`、`scenario-bi-domain-mobile-retrying.png`、`scenario-bi-domain-mobile-dark-retrying.png`、`scenario-bi-domain-tablet-heartbeat-restored.png`、`scenario-bi-domain-tablet-dark-heartbeat-restored.png`、`scenario-bi-domain-mobile-heartbeat-restored.png`、`scenario-bi-domain-mobile-dark-heartbeat-restored.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retrying 截图 | `scenario-bi-domain-tablet-retrying.png` 存在且 retrying framing 正常 | SDRHT-01 · RESP-06 |
| 2 | tablet dark retrying 截图 | `scenario-bi-domain-tablet-dark-retrying.png` 存在且重试 banner 可读 | SDRHT-01 · VIS-05 |
| 3 | mobile light heartbeat-restored 截图 | `scenario-bi-domain-mobile-heartbeat-restored.png` restored banner 首屏可见 | SDRHT-01 · RESP-07 |
| 4 | mobile dark heartbeat-restored 截图 | `scenario-bi-domain-mobile-dark-heartbeat-restored.png` restored 对比度可辨认 | SDRHT-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainDisconnectRetryHeartbeatViewportLightDarkScreenshots` biDomain 全过 | SDRHT-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 retrying 面板 → 点击「触发指标心跳恢复」→ 对照 tablet/mobile light/dark 八张 retrying/heartbeat-restored 截图。

## SDRHT-02 — DevOps 场景阶段断连重试/心跳超时 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-retrying.png`、`scenario-devops-domain-tablet-dark-retrying.png`、`scenario-devops-domain-mobile-retrying.png`、`scenario-devops-domain-mobile-dark-retrying.png`、`scenario-devops-domain-tablet-heartbeat-restored.png`、`scenario-devops-domain-tablet-dark-heartbeat-restored.png`、`scenario-devops-domain-mobile-heartbeat-restored.png`、`scenario-devops-domain-mobile-dark-heartbeat-restored.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retrying 截图 | `scenario-devops-domain-tablet-retrying.png` 存在且 retrying framing 正常 | SDRHT-02 · RESP-06 |
| 2 | tablet dark retrying 截图 | `scenario-devops-domain-tablet-dark-retrying.png` 存在且断连重试可读 | SDRHT-02 · VIS-05 |
| 3 | mobile light heartbeat-restored 截图 | `scenario-devops-domain-mobile-heartbeat-restored.png` 流水线 restored 首屏可见 | SDRHT-02 · RESP-07 |
| 4 | mobile dark heartbeat-restored 截图 | `scenario-devops-domain-mobile-dark-heartbeat-restored.png` restored 对比度可辨认 | SDRHT-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 断连重试/心跳超时 tablet/mobile light/dark 可见 | SDRHT-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 retrying 面板 → 点击「触发阶段心跳恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDRHT-03 — Gateway 场景端点断连重试/心跳超时 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-retrying.png`、`scenario-gateway-domain-tablet-dark-retrying.png`、`scenario-gateway-domain-mobile-retrying.png`、`scenario-gateway-domain-mobile-dark-retrying.png`、`scenario-gateway-domain-tablet-heartbeat-restored.png`、`scenario-gateway-domain-tablet-dark-heartbeat-restored.png`、`scenario-gateway-domain-mobile-heartbeat-restored.png`、`scenario-gateway-domain-mobile-dark-heartbeat-restored.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retrying 截图 | `scenario-gateway-domain-tablet-retrying.png` 存在且 retrying framing 正常 | SDRHT-03 · RESP-06 |
| 2 | tablet dark retrying 截图 | `scenario-gateway-domain-tablet-dark-retrying.png` 存在且断连重试可读 | SDRHT-03 · VIS-05 |
| 3 | mobile light heartbeat-restored 截图 | `scenario-gateway-domain-mobile-heartbeat-restored.png` 端点 restored 首屏可见 | SDRHT-03 · RESP-07 |
| 4 | mobile dark heartbeat-restored 截图 | `scenario-gateway-domain-mobile-dark-heartbeat-restored.png` restored 层级不丢失 | SDRHT-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 断连重试/心跳超时 tablet/mobile light/dark 可见 | SDRHT-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 retrying 面板 → 点击「触发端点心跳恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDRHT-04 — Governance 场景审计行断连重试/心跳超时 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-retrying.png`、`scenario-governance-domain-tablet-dark-retrying.png`、`scenario-governance-domain-mobile-retrying.png`、`scenario-governance-domain-mobile-dark-retrying.png`、`scenario-governance-domain-tablet-heartbeat-restored.png`、`scenario-governance-domain-tablet-dark-heartbeat-restored.png`、`scenario-governance-domain-mobile-heartbeat-restored.png`、`scenario-governance-domain-mobile-dark-heartbeat-restored.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retrying 截图 | `scenario-governance-domain-tablet-retrying.png` 存在且 retrying framing 正常 | SDRHT-04 · RESP-06 |
| 2 | tablet dark retrying 截图 | `scenario-governance-domain-tablet-dark-retrying.png` 存在且断连重试可读 | SDRHT-04 · VIS-05 |
| 3 | mobile light heartbeat-restored 截图 | `scenario-governance-domain-mobile-heartbeat-restored.png` 审计 restored 首屏可见 | SDRHT-04 · RESP-07 |
| 4 | mobile dark heartbeat-restored 截图 | `scenario-governance-domain-mobile-dark-heartbeat-restored.png` restored 密度一致 | SDRHT-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 断连重试/心跳超时 tablet/mobile light/dark 可见 | SDRHT-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 retrying 面板 → 点击「触发审计心跳恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDRHT-05 — PaaS 场景容量断连重试/心跳超时 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-retrying.png`、`scenario-paas-domain-tablet-dark-retrying.png`、`scenario-paas-domain-mobile-retrying.png`、`scenario-paas-domain-mobile-dark-retrying.png`、`scenario-paas-domain-tablet-heartbeat-restored.png`、`scenario-paas-domain-tablet-dark-heartbeat-restored.png`、`scenario-paas-domain-mobile-heartbeat-restored.png`、`scenario-paas-domain-mobile-dark-heartbeat-restored.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light retrying 截图 | `scenario-paas-domain-tablet-retrying.png` 存在且 retrying framing 正常 | SDRHT-05 · RESP-06 |
| 2 | tablet dark retrying 截图 | `scenario-paas-domain-tablet-dark-retrying.png` 存在且断连重试可读 | SDRHT-05 · VIS-05 |
| 3 | mobile light heartbeat-restored 截图 | `scenario-paas-domain-mobile-heartbeat-restored.png` 容量 restored 首屏可见 | SDRHT-05 · RESP-07 |
| 4 | mobile dark heartbeat-restored 截图 | `scenario-paas-domain-mobile-dark-heartbeat-restored.png` restored 列表项可辨认 | SDRHT-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 断连重试/心跳超时 tablet/mobile light/dark 可见 | SDRHT-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 retrying 面板 → 点击「触发容量心跳恢复」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md` SDRHT-06～10
- network partition/recovery 前置：`scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md` SDNPR-01～05
- 选型表：`decision-matrix.md` G110 场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDRHT-01～10
- Runtime 门禁：`verifyScenarioDomainDisconnectRetryHeartbeatViewportLightDarkScreenshots`
