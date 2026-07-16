# 场景 Scenario Domain Refetch Pending Viewport Light/Dark Screenshot 评审清单

> DOCS-055 / G104 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 refetch/pending 独立截图抽检**，确保各域 section 在 refetch/pending 态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md`（SDRP-01～05）、`scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md`（SDPR-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 refetch/pending tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDRP 块 + `quality-rubric.md` |
| BI Analytics 指标 refetch/pending tablet/mobile light/dark 独立截图 | SDRP-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 refetch/pending tablet/mobile light/dark 独立截图 | SDRP-07 + `scenario-devops` |
| Gateway 端点 refetch/pending tablet/mobile light/dark 独立截图 | SDRP-08 + `scenario-gateway` |
| Governance 审计行 refetch/pending tablet/mobile light/dark 独立截图 | SDRP-09 + `scenario-governance` |
| 场景域 refetch/pending tablet/mobile light/dark 独立截图束缺门禁 | SDRP-10 + `verify:runtime` `scenarioDomainRefetchPendingViewportLightDarkScreenshotStates` + `verifyScenarioDomainRefetchPendingViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md` SDRP-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{pending,refetch}.png` 共 40 张 refetch/pending 独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark refetch/pending 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 refetch/pending tablet/mobile light/dark 独立截图（G104）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 refetch/pending tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDRP-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDRP-06 — BI Analytics 指标 refetch/pending tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-pending.png`、`scenario-bi-domain-mobile-dark-refetch.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark pending | `scenario-bi-domain-tablet-pending.png` + `scenario-bi-domain-tablet-dark-pending.png` pending framing 正常 | SDRP-06 · RESP-06 |
| 2 | mobile light/dark refetch | `scenario-bi-domain-mobile-refetch.png` + `scenario-bi-domain-mobile-dark-refetch.png` refetch framing 正常 | SDRP-06 · RESP-07 |
| 3 | 指标 refetch/pending | 待加载 spinner + 后台刷新 stale banner tablet/mobile light/dark 首屏可见 | SDRP-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 spinner 与 refetch banner 层级可辨认 | SDRP-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 refetch/pending 截图全过 | SDRP-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 pending 面板 → 点击「触发指标刷新」→ 对照 tablet/mobile light/dark 八张 refetch/pending 截图。

## SDRP-07 — DevOps 阶段 refetch/pending tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-pending.png`、`scenario-devops-domain-mobile-dark-refetch.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark pending | `scenario-devops-domain-tablet-pending.png` + `scenario-devops-domain-tablet-dark-pending.png` pending framing 正常 | SDRP-07 · RESP-06 |
| 2 | mobile light/dark refetch | `scenario-devops-domain-mobile-refetch.png` + `scenario-devops-domain-mobile-dark-refetch.png` refetch framing 正常 | SDRP-07 · RESP-07 |
| 3 | 阶段 refetch/pending | 流水线 pending spinner + 阶段后台刷新 stale banner tablet/mobile light/dark 首屏可见 | SDRP-07 · PAT-07 |
| 4 | refetch 态 | mobile dark 下 refetch 文案与刷新按钮可辨认 | SDRP-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 refetch/pending 截图全过 | SDRP-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 pending 面板 → 点击「触发阶段刷新」→ 对照 tablet/mobile light/dark 八张截图。

## SDRP-08 — Gateway 端点 refetch/pending tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-pending.png`、`scenario-gateway-domain-mobile-dark-refetch.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark pending | `scenario-gateway-domain-tablet-pending.png` + `scenario-gateway-domain-tablet-dark-pending.png` pending framing 正常 | SDRP-08 · RESP-06 |
| 2 | mobile light/dark refetch | `scenario-gateway-domain-mobile-refetch.png` + `scenario-gateway-domain-mobile-dark-refetch.png` refetch framing 正常 | SDRP-08 · RESP-07 |
| 3 | 端点 refetch/pending | 端点 pending spinner + 后台刷新 stale banner tablet/mobile light/dark 首屏可见 | SDRP-08 · PAT-08 |
| 4 | pending 态 | mobile dark 下 spinner 与待加载文案可辨认 | SDRP-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 refetch/pending 截图全过 | SDRP-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 pending 面板 → 点击「触发端点刷新」→ 对照 tablet/mobile light/dark 八张截图。

## SDRP-09 — Governance 审计行 refetch/pending tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-pending.png`、`scenario-governance-domain-mobile-pending.png`、`scenario-governance-domain-mobile-dark-refetch.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark pending | `scenario-governance-domain-tablet-pending.png` + `scenario-governance-domain-tablet-dark-pending.png` pending framing 正常 | SDRP-09 · RESP-06 |
| 2 | mobile light/dark refetch | `scenario-governance-domain-mobile-refetch.png` + `scenario-governance-domain-mobile-dark-refetch.png` refetch framing 正常 | SDRP-09 · RESP-07 |
| 3 | 审计 refetch/pending | 审计 pending spinner + 后台刷新 stale banner tablet/mobile light/dark 首屏可见 | SDRP-09 · PAT-09 |
| 4 | refetch 文案 | mobile dark 下「数据已过期，正在后台刷新」文案可辨认 | SDRP-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 refetch/pending 截图全过 | SDRP-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 pending 面板 → 点击「触发审计刷新」→ 对照 tablet/mobile light/dark 八张截图。

## SDRP-10 — 场景域 refetch/pending tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{pending,refetch}.png` + `scenarioDomainRefetchPendingViewportLightDarkScreenshotStates.refetchPendingStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × pending/refetch 全量 golden 存在 | SDRP-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainRefetchPendingViewportLightDarkScreenshots` 通过 | SDRP-10 · PREVIEW-* |
| 3 | pending 态 | 五域 `data-audit="scenario-domain-pending-overlay"` `data-state="pending"` 可见 | SDRP-10 · LOGIC-* |
| 4 | refetch 态 | 五域点击 refetch trigger 后 `role="status"` + `data-state="refetch"` 可见 | SDRP-10 · ASYNC-* |
| 5 | 矩阵完整 | `refetchPendingStateMatrixComplete = true` | SDRP-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张 refetch/pending 截图与门禁 JSON 输出。
