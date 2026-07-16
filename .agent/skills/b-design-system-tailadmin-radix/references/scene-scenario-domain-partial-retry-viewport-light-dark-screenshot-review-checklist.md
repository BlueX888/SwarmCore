# 场景 Scenario Domain Partial Retry Viewport Light/Dark Screenshot 评审清单

> DOCS-054 / G103 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 partial/retry 独立截图抽检**，确保各域 section 在 partial/retry 态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md`（SDPR-01～05）、`scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md`（SDEE-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 partial/retry tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPR 块 + `quality-rubric.md` |
| BI Analytics 指标 partial/retry tablet/mobile light/dark 独立截图 | SDPR-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 partial/retry tablet/mobile light/dark 独立截图 | SDPR-07 + `scenario-devops` |
| Gateway 端点 partial/retry tablet/mobile light/dark 独立截图 | SDPR-08 + `scenario-gateway` |
| Governance 审计行 partial/retry tablet/mobile light/dark 独立截图 | SDPR-09 + `scenario-governance` |
| 场景域 partial/retry tablet/mobile light/dark 独立截图束缺门禁 | SDPR-10 + `verify:runtime` `scenarioDomainPartialRetryViewportLightDarkScreenshotStates` + `verifyScenarioDomainPartialRetryViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md` SDPR-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{partial,retry}.png` 共 40 张 partial/retry 独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark partial/retry 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 partial/retry tablet/mobile light/dark 独立截图（G103）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 partial/retry tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDPR-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDPR-06 — BI Analytics 指标 partial/retry tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-partial.png`、`scenario-bi-domain-mobile-dark-retry.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark partial | `scenario-bi-domain-tablet-partial.png` + `scenario-bi-domain-tablet-dark-partial.png` partial framing 正常 | SDPR-06 · RESP-06 |
| 2 | mobile light/dark retry | `scenario-bi-domain-mobile-retry.png` + `scenario-bi-domain-mobile-dark-retry.png` retry framing 正常 | SDPR-06 · RESP-07 |
| 3 | 指标 partial/retry | 部分数据加载失败 warning + 指标刷新失败 retry alert tablet/mobile light/dark 首屏可见 | SDPR-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 warning banner 与 retry alert 层级可辨认 | SDPR-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 partial/retry 截图全过 | SDPR-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 partial 面板 → 点击「触发指标重试」→ 对照 tablet/mobile light/dark 八张 partial/retry 截图。

## SDPR-07 — DevOps 阶段 partial/retry tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-partial.png`、`scenario-devops-domain-mobile-dark-retry.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark partial | `scenario-devops-domain-tablet-partial.png` + `scenario-devops-domain-tablet-dark-partial.png` partial framing 正常 | SDPR-07 · RESP-06 |
| 2 | mobile light/dark retry | `scenario-devops-domain-mobile-retry.png` + `scenario-devops-domain-mobile-dark-retry.png` retry framing 正常 | SDPR-07 · RESP-07 |
| 3 | 阶段 partial/retry | 流水线 partial warning + 阶段刷新失败 retry alert tablet/mobile light/dark 首屏可见 | SDPR-07 · PAT-07 |
| 4 | retry 态 | mobile dark 下 retry 文案与重试按钮可辨认 | SDPR-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 partial/retry 截图全过 | SDPR-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 partial 面板 → 点击「触发阶段重试」→ 对照 tablet/mobile light/dark 八张截图。

## SDPR-08 — Gateway 端点 partial/retry tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-partial.png`、`scenario-gateway-domain-mobile-dark-retry.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark partial | `scenario-gateway-domain-tablet-partial.png` + `scenario-gateway-domain-tablet-dark-partial.png` partial framing 正常 | SDPR-08 · RESP-06 |
| 2 | mobile light/dark retry | `scenario-gateway-domain-mobile-retry.png` + `scenario-gateway-domain-mobile-dark-retry.png` retry framing 正常 | SDPR-08 · RESP-07 |
| 3 | 端点 partial/retry | 端点 partial warning + 端点刷新失败 retry alert tablet/mobile light/dark 首屏可见 | SDPR-08 · PAT-08 |
| 4 | partial 态 | mobile dark 下 warning banner 对比度可辨认 | SDPR-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 partial/retry 截图全过 | SDPR-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 partial 面板 → 点击「触发端点重试」→ 对照 tablet/mobile light/dark 八张截图。

## SDPR-09 — Governance 审计行 partial/retry tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-partial.png`、`scenario-governance-domain-mobile-partial.png`、`scenario-governance-domain-mobile-dark-retry.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark partial | `scenario-governance-domain-tablet-partial.png` + `scenario-governance-domain-tablet-dark-partial.png` partial framing 正常 | SDPR-09 · RESP-06 |
| 2 | mobile light/dark retry | `scenario-governance-domain-mobile-retry.png` + `scenario-governance-domain-mobile-dark-retry.png` retry framing 正常 | SDPR-09 · RESP-07 |
| 3 | 审计 partial/retry | 审计 partial warning + 审计刷新失败 retry alert tablet/mobile light/dark 首屏可见 | SDPR-09 · PAT-09 |
| 4 | retry 文案 | mobile dark 下「审计刷新失败」文案可辨认 | SDPR-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 partial/retry 截图全过 | SDPR-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 partial 面板 → 点击「触发审计重试」→ 对照 tablet/mobile light/dark 八张截图。

## SDPR-10 — 场景域 partial/retry tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{partial,retry}.png` + `scenarioDomainPartialRetryViewportLightDarkScreenshotStates.partialRetryStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × partial/retry 全量 golden 存在 | SDPR-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainPartialRetryViewportLightDarkScreenshots` 通过 | SDPR-10 · PREVIEW-* |
| 3 | partial 态 | 五域 `data-audit="scenario-domain-partial-overlay"` `data-state="partial"` 可见 | SDPR-10 · LOGIC-* |
| 4 | retry 态 | 五域点击 retry trigger 后 `role="alert"` + `data-state="retry"` 可见 | SDPR-10 · ASYNC-* |
| 5 | 矩阵完整 | `partialRetryStateMatrixComplete = true` | SDPR-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张 partial/retry 截图与门禁 JSON 输出。
