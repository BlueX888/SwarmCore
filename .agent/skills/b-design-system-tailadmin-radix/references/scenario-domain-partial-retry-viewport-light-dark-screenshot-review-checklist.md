# Scenario Domain Partial Retry Viewport Light/Dark Screenshot 评审清单

> DOCS-054 / G103 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 partial/retry 独立截图视觉回归抽检**，确保每个场景 section 在局部失败、重试态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md`（SDEE-01～05）、`scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md`（SDPR-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 partial/retry tablet/mobile light/dark 独立截图抽检 | 对应 SDPR 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标 partial/retry tablet/mobile light/dark golden 对照 | SDPR-01 + `scenario-bi-domain-tablet-partial.png` + `scenario-bi-domain-mobile-dark-retry.png` |
| DevOps 场景阶段 partial/retry tablet/mobile light/dark golden 对照 | SDPR-02 + `scenario-devops-domain-tablet-partial.png` + `scenario-devops-domain-mobile-dark-retry.png` |
| Gateway 场景端点 partial/retry tablet/mobile light/dark golden 对照 | SDPR-03 + `scenario-gateway-domain-tablet-partial.png` + `scenario-gateway-domain-mobile-dark-retry.png` |
| Governance 场景审计行 partial/retry tablet/mobile light/dark golden 对照 | SDPR-04 + `scenario-governance-domain-tablet-partial.png` + `scenario-governance-domain-mobile-dark-retry.png` |
| PaaS 场景容量 partial/retry tablet/mobile light/dark golden 对照 | SDPR-05 + `scenario-paas-domain-tablet-partial.png` + `scenario-paas-domain-mobile-dark-retry.png` |

## 通用前置

1. 先完成 `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md` SDEE-01～05（empty/error 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{partial,retry}.png` 四视口双主题 partial/retry 独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 partial 与一张 retry 独立截图；partial 必须出现 warning banner 与缓存数据列表，retry 必须出现 `role="alert"` 与重试 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. partial/retry 截图出现文案裁切、warning banner 对比度不足、retry 无重试按钮或 dark 层级丢失时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 partial/retry tablet/mobile light/dark 独立截图（G103）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 partial/retry tablet/mobile light/dark 独立截图抽检行。

## SDPR-01 — BI 场景指标 partial/retry tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-partial.png`、`scenario-bi-domain-tablet-dark-partial.png`、`scenario-bi-domain-mobile-partial.png`、`scenario-bi-domain-mobile-dark-partial.png`、`scenario-bi-domain-tablet-retry.png`、`scenario-bi-domain-tablet-dark-retry.png`、`scenario-bi-domain-mobile-retry.png`、`scenario-bi-domain-mobile-dark-retry.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light partial 截图 | `scenario-bi-domain-tablet-partial.png` 存在且 partial framing 正常 | SDPR-01 · RESP-06 |
| 2 | tablet dark partial 截图 | `scenario-bi-domain-tablet-dark-partial.png` 存在且 warning banner 可读 | SDPR-01 · VIS-05 |
| 3 | mobile light retry 截图 | `scenario-bi-domain-mobile-retry.png` retry alert 首屏可见 | SDPR-01 · RESP-07 |
| 4 | mobile dark retry 截图 | `scenario-bi-domain-mobile-dark-retry.png` retry 对比度可辨认 | SDPR-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPartialRetryViewportLightDarkScreenshots` biDomain 全过 | SDPR-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 partial 面板 → 点击「触发指标重试」→ 对照 tablet/mobile light/dark 八张 partial/retry 截图。

## SDPR-02 — DevOps 场景阶段 partial/retry tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-partial.png`、`scenario-devops-domain-tablet-dark-partial.png`、`scenario-devops-domain-mobile-partial.png`、`scenario-devops-domain-mobile-dark-partial.png`、`scenario-devops-domain-tablet-retry.png`、`scenario-devops-domain-tablet-dark-retry.png`、`scenario-devops-domain-mobile-retry.png`、`scenario-devops-domain-mobile-dark-retry.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light partial 截图 | `scenario-devops-domain-tablet-partial.png` 存在且 partial framing 正常 | SDPR-02 · RESP-06 |
| 2 | tablet dark partial 截图 | `scenario-devops-domain-tablet-dark-partial.png` 存在且阶段 partial 可读 | SDPR-02 · VIS-05 |
| 3 | mobile light retry 截图 | `scenario-devops-domain-mobile-retry.png` 流水线 retry 首屏可见 | SDPR-02 · RESP-07 |
| 4 | mobile dark retry 截图 | `scenario-devops-domain-mobile-dark-retry.png` retry 对比度可辨认 | SDPR-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + partial/retry tablet/mobile light/dark 可见 | SDPR-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 partial 面板 → 点击「触发阶段重试」→ 对照 tablet/mobile light/dark 八张截图。

## SDPR-03 — Gateway 场景端点 partial/retry tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-partial.png`、`scenario-gateway-domain-tablet-dark-partial.png`、`scenario-gateway-domain-mobile-partial.png`、`scenario-gateway-domain-mobile-dark-partial.png`、`scenario-gateway-domain-tablet-retry.png`、`scenario-gateway-domain-tablet-dark-retry.png`、`scenario-gateway-domain-mobile-retry.png`、`scenario-gateway-domain-mobile-dark-retry.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light partial 截图 | `scenario-gateway-domain-tablet-partial.png` 存在且 partial framing 正常 | SDPR-03 · RESP-06 |
| 2 | tablet dark partial 截图 | `scenario-gateway-domain-tablet-dark-partial.png` 存在且端点 partial 可读 | SDPR-03 · VIS-05 |
| 3 | mobile light retry 截图 | `scenario-gateway-domain-mobile-retry.png` 端点 retry 首屏可见 | SDPR-03 · RESP-07 |
| 4 | mobile dark retry 截图 | `scenario-gateway-domain-mobile-dark-retry.png` retry 层级不丢失 | SDPR-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + partial/retry tablet/mobile light/dark 可见 | SDPR-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 partial 面板 → 点击「触发端点重试」→ 对照 tablet/mobile light/dark 八张截图。

## SDPR-04 — Governance 场景审计行 partial/retry tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-partial.png`、`scenario-governance-domain-tablet-dark-partial.png`、`scenario-governance-domain-mobile-partial.png`、`scenario-governance-domain-mobile-dark-partial.png`、`scenario-governance-domain-tablet-retry.png`、`scenario-governance-domain-tablet-dark-retry.png`、`scenario-governance-domain-mobile-retry.png`、`scenario-governance-domain-mobile-dark-retry.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light partial 截图 | `scenario-governance-domain-tablet-partial.png` 存在且 partial framing 正常 | SDPR-04 · RESP-06 |
| 2 | tablet dark partial 截图 | `scenario-governance-domain-tablet-dark-partial.png` 存在且审计 partial 可读 | SDPR-04 · VIS-05 |
| 3 | mobile light retry 截图 | `scenario-governance-domain-mobile-retry.png` 审计 retry 首屏可见 | SDPR-04 · RESP-07 |
| 4 | mobile dark retry 截图 | `scenario-governance-domain-mobile-dark-retry.png` retry 密度一致 | SDPR-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + partial/retry tablet/mobile light/dark 可见 | SDPR-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 partial 面板 → 点击「触发审计重试」→ 对照 tablet/mobile light/dark 八张截图。

## SDPR-05 — PaaS 场景容量 partial/retry tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-partial.png`、`scenario-paas-domain-tablet-dark-partial.png`、`scenario-paas-domain-mobile-partial.png`、`scenario-paas-domain-mobile-dark-partial.png`、`scenario-paas-domain-tablet-retry.png`、`scenario-paas-domain-tablet-dark-retry.png`、`scenario-paas-domain-mobile-retry.png`、`scenario-paas-domain-mobile-dark-retry.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light partial 截图 | `scenario-paas-domain-tablet-partial.png` 存在且 partial framing 正常 | SDPR-05 · RESP-06 |
| 2 | tablet dark partial 截图 | `scenario-paas-domain-tablet-dark-partial.png` 存在且容量 partial 可读 | SDPR-05 · VIS-05 |
| 3 | mobile light retry 截图 | `scenario-paas-domain-mobile-retry.png` 容量 retry 首屏可见 | SDPR-05 · RESP-07 |
| 4 | mobile dark retry 截图 | `scenario-paas-domain-mobile-dark-retry.png` retry 列表项可辨认 | SDPR-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + partial/retry tablet/mobile light/dark 可见 | SDPR-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 partial 面板 → 点击「触发容量重试」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md` SDPR-06～10
- empty/error 前置：`scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md` SDEE-01～05
- 选型表：`decision-matrix.md` G103 场景域 partial/retry tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPR-01～10
- Runtime 门禁：`verifyScenarioDomainPartialRetryViewportLightDarkScreenshots`
