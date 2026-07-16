# Scenario Domain Push Channel Circuit Breaker Rate Limit Viewport Light/Dark Screenshot 评审清单

> DOCS-066 / G115 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道熔断/限流解除独立截图视觉回归抽检**，确保每个场景 section 在推送通道熔断态、限流解除态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDPCDR-01～05）、`scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md`（SDPCBRL-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道熔断/限流解除 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCBRL 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道熔断/限流解除 tablet/mobile light/dark golden 对照 | SDPCBRL-01 + `scenario-bi-domain-tablet-channel-breaker-open.png` + `scenario-bi-domain-mobile-dark-rate-limit-released.png` |
| DevOps 场景阶段推送通道熔断/限流解除 tablet/mobile light/dark golden 对照 | SDPCBRL-02 + `scenario-devops-domain-tablet-channel-breaker-open.png` + `scenario-devops-domain-mobile-dark-rate-limit-released.png` |
| Gateway 场景端点推送通道熔断/限流解除 tablet/mobile light/dark golden 对照 | SDPCBRL-03 + `scenario-gateway-domain-tablet-channel-breaker-open.png` + `scenario-gateway-domain-mobile-dark-rate-limit-released.png` |
| Governance 场景审计行推送通道熔断/限流解除 tablet/mobile light/dark golden 对照 | SDPCBRL-04 + `scenario-governance-domain-tablet-channel-breaker-open.png` + `scenario-governance-domain-mobile-dark-rate-limit-released.png` |
| PaaS 场景容量推送通道熔断/限流解除 tablet/mobile light/dark golden 对照 | SDPCBRL-05 + `scenario-paas-domain-tablet-channel-breaker-open.png` + `scenario-paas-domain-mobile-dark-rate-limit-released.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md` SDPCDR-01～05（推送通道降级/恢复独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-breaker-open,rate-limit-released}.png` 四视口双主题推送通道熔断/限流解除独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 channel-breaker-open 与一张 rate-limit-released 独立截图；channel-breaker-open 必须出现熔断 banner「推送通道已熔断（限流保护模式）」与熔断摘要，rate-limit-released 必须出现限流解除 banner 与「查看限流解除详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道熔断/限流解除截图出现文案裁切、熔断 banner 对比度不足、rate-limit-released banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道熔断/限流解除 tablet/mobile light/dark 独立截图（G115）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道熔断/限流解除 tablet/mobile light/dark 独立截图抽检行。

## SDPCBRL-01 — BI 场景指标推送通道熔断/限流解除 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-channel-breaker-open.png`、`scenario-bi-domain-tablet-dark-channel-breaker-open.png`、`scenario-bi-domain-mobile-channel-breaker-open.png`、`scenario-bi-domain-mobile-dark-channel-breaker-open.png`、`scenario-bi-domain-tablet-rate-limit-released.png`、`scenario-bi-domain-tablet-dark-rate-limit-released.png`、`scenario-bi-domain-mobile-rate-limit-released.png`、`scenario-bi-domain-mobile-dark-rate-limit-released.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-breaker-open 截图 | `scenario-bi-domain-tablet-channel-breaker-open.png` 存在且 channel-breaker-open framing 正常 | SDPCBRL-01 · RESP-06 |
| 2 | tablet dark channel-breaker-open 截图 | `scenario-bi-domain-tablet-dark-channel-breaker-open.png` 存在且熔断 banner 可读 | SDPCBRL-01 · VIS-05 |
| 3 | mobile light rate-limit-released 截图 | `scenario-bi-domain-mobile-rate-limit-released.png` rate-limit-released banner 首屏可见 | SDPCBRL-01 · RESP-07 |
| 4 | mobile dark rate-limit-released 截图 | `scenario-bi-domain-mobile-dark-rate-limit-released.png` rate-limit-released 对比度可辨认 | SDPCBRL-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelCircuitBreakerRateLimitViewportLightDarkScreenshots` biDomain 全过 | SDPCBRL-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 channel-breaker-open 面板 → 点击「触发指标限流解除」→ 对照 tablet/mobile light/dark 八张 channel-breaker-open/rate-limit-released 截图。

## SDPCBRL-02 — DevOps 场景阶段推送通道熔断/限流解除 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-channel-breaker-open.png`、`scenario-devops-domain-tablet-dark-channel-breaker-open.png`、`scenario-devops-domain-mobile-channel-breaker-open.png`、`scenario-devops-domain-mobile-dark-channel-breaker-open.png`、`scenario-devops-domain-tablet-rate-limit-released.png`、`scenario-devops-domain-tablet-dark-rate-limit-released.png`、`scenario-devops-domain-mobile-rate-limit-released.png`、`scenario-devops-domain-mobile-dark-rate-limit-released.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-breaker-open 截图 | `scenario-devops-domain-tablet-channel-breaker-open.png` 存在且 channel-breaker-open framing 正常 | SDPCBRL-02 · RESP-06 |
| 2 | tablet dark channel-breaker-open 截图 | `scenario-devops-domain-tablet-dark-channel-breaker-open.png` 存在且熔断摘要可读 | SDPCBRL-02 · VIS-05 |
| 3 | mobile light rate-limit-released 截图 | `scenario-devops-domain-mobile-rate-limit-released.png` 流水线 rate-limit-released 首屏可见 | SDPCBRL-02 · RESP-07 |
| 4 | mobile dark rate-limit-released 截图 | `scenario-devops-domain-mobile-dark-rate-limit-released.png` rate-limit-released 对比度可辨认 | SDPCBRL-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道熔断/限流解除 tablet/mobile light/dark 可见 | SDPCBRL-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 channel-breaker-open 面板 → 点击「触发阶段限流解除」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBRL-03 — Gateway 场景端点推送通道熔断/限流解除 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-channel-breaker-open.png`、`scenario-gateway-domain-tablet-dark-channel-breaker-open.png`、`scenario-gateway-domain-mobile-channel-breaker-open.png`、`scenario-gateway-domain-mobile-dark-channel-breaker-open.png`、`scenario-gateway-domain-tablet-rate-limit-released.png`、`scenario-gateway-domain-tablet-dark-rate-limit-released.png`、`scenario-gateway-domain-mobile-rate-limit-released.png`、`scenario-gateway-domain-mobile-dark-rate-limit-released.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-breaker-open 截图 | `scenario-gateway-domain-tablet-channel-breaker-open.png` 存在且 channel-breaker-open framing 正常 | SDPCBRL-03 · RESP-06 |
| 2 | tablet dark channel-breaker-open 截图 | `scenario-gateway-domain-tablet-dark-channel-breaker-open.png` 存在且熔断摘要可读 | SDPCBRL-03 · VIS-05 |
| 3 | mobile light rate-limit-released 截图 | `scenario-gateway-domain-mobile-rate-limit-released.png` 端点 rate-limit-released 首屏可见 | SDPCBRL-03 · RESP-07 |
| 4 | mobile dark rate-limit-released 截图 | `scenario-gateway-domain-mobile-dark-rate-limit-released.png` rate-limit-released 层级不丢失 | SDPCBRL-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道熔断/限流解除 tablet/mobile light/dark 可见 | SDPCBRL-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 channel-breaker-open 面板 → 点击「触发端点限流解除」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBRL-04 — Governance 场景审计行推送通道熔断/限流解除 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-channel-breaker-open.png`、`scenario-governance-domain-tablet-dark-channel-breaker-open.png`、`scenario-governance-domain-mobile-channel-breaker-open.png`、`scenario-governance-domain-mobile-dark-channel-breaker-open.png`、`scenario-governance-domain-tablet-rate-limit-released.png`、`scenario-governance-domain-tablet-dark-rate-limit-released.png`、`scenario-governance-domain-mobile-rate-limit-released.png`、`scenario-governance-domain-mobile-dark-rate-limit-released.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-breaker-open 截图 | `scenario-governance-domain-tablet-channel-breaker-open.png` 存在且 channel-breaker-open framing 正常 | SDPCBRL-04 · RESP-06 |
| 2 | tablet dark channel-breaker-open 截图 | `scenario-governance-domain-tablet-dark-channel-breaker-open.png` 存在且熔断摘要可读 | SDPCBRL-04 · VIS-05 |
| 3 | mobile light rate-limit-released 截图 | `scenario-governance-domain-mobile-rate-limit-released.png` 审计 rate-limit-released 首屏可见 | SDPCBRL-04 · RESP-07 |
| 4 | mobile dark rate-limit-released 截图 | `scenario-governance-domain-mobile-dark-rate-limit-released.png` rate-limit-released 密度一致 | SDPCBRL-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道熔断/限流解除 tablet/mobile light/dark 可见 | SDPCBRL-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 channel-breaker-open 面板 → 点击「触发审计限流解除」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCBRL-05 — PaaS 场景容量推送通道熔断/限流解除 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-channel-breaker-open.png`、`scenario-paas-domain-tablet-dark-channel-breaker-open.png`、`scenario-paas-domain-mobile-channel-breaker-open.png`、`scenario-paas-domain-mobile-dark-channel-breaker-open.png`、`scenario-paas-domain-tablet-rate-limit-released.png`、`scenario-paas-domain-tablet-dark-rate-limit-released.png`、`scenario-paas-domain-mobile-rate-limit-released.png`、`scenario-paas-domain-mobile-dark-rate-limit-released.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-breaker-open 截图 | `scenario-paas-domain-tablet-channel-breaker-open.png` 存在且 channel-breaker-open framing 正常 | SDPCBRL-05 · RESP-06 |
| 2 | tablet dark channel-breaker-open 截图 | `scenario-paas-domain-tablet-dark-channel-breaker-open.png` 存在且熔断摘要可读 | SDPCBRL-05 · VIS-05 |
| 3 | mobile light rate-limit-released 截图 | `scenario-paas-domain-mobile-rate-limit-released.png` 容量 rate-limit-released 首屏可见 | SDPCBRL-05 · RESP-07 |
| 4 | mobile dark rate-limit-released 截图 | `scenario-paas-domain-mobile-dark-rate-limit-released.png` rate-limit-released 列表项可辨认 | SDPCBRL-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道熔断/限流解除 tablet/mobile light/dark 可见 | SDPCBRL-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 channel-breaker-open 面板 → 点击「触发容量限流解除」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md` SDPCBRL-06～10
- 推送通道降级/恢复 前置：`scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md` SDPCDR-01～05
- 选型表：`decision-matrix.md` G115 场景域推送通道熔断/限流解除 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCBRL-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelCircuitBreakerRateLimitViewportLightDarkScreenshots`
