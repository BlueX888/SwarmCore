# 场景 Scenario Domain Stale Optimistic Viewport Light/Dark Screenshot 评审清单

> DOCS-056 / G105 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 stale/optimistic 独立截图抽检**，确保各域 section 在 Stale-While-Revalidate 缓存展示与乐观更新态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md`（SDSO-01～05）、`scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md`（SDRP-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 stale/optimistic tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDSO 块 + `quality-rubric.md` |
| BI Analytics 指标 stale/optimistic tablet/mobile light/dark 独立截图 | SDSO-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 stale/optimistic tablet/mobile light/dark 独立截图 | SDSO-07 + `scenario-devops` |
| Gateway 端点 stale/optimistic tablet/mobile light/dark 独立截图 | SDSO-08 + `scenario-gateway` |
| Governance 审计行 stale/optimistic tablet/mobile light/dark 独立截图 | SDSO-09 + `scenario-governance` |
| 场景域 stale/optimistic tablet/mobile light/dark 独立截图束缺门禁 | SDSO-10 + `verify:runtime` `scenarioDomainStaleOptimisticViewportLightDarkScreenshotStates` + `verifyScenarioDomainStaleOptimisticViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md` SDSO-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{stale,optimistic}.png` 共 40 张 stale/optimistic 独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark stale/optimistic 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 stale/optimistic tablet/mobile light/dark 独立截图（G105）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 stale/optimistic tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDSO-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDSO-06 — BI Analytics 指标 stale/optimistic tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-stale.png`、`scenario-bi-domain-mobile-dark-optimistic.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark stale | `scenario-bi-domain-tablet-stale.png` + `scenario-bi-domain-tablet-dark-stale.png` stale framing 正常 | SDSO-06 · RESP-06 |
| 2 | mobile light/dark optimistic | `scenario-bi-domain-mobile-optimistic.png` + `scenario-bi-domain-mobile-dark-optimistic.png` optimistic framing 正常 | SDSO-06 · RESP-07 |
| 3 | 指标 stale/optimistic | 缓存 banner + 同步指示器 + 乐观更新 banner tablet/mobile light/dark 首屏可见 | SDSO-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 stale banner 与 optimistic banner 层级可辨认 | SDSO-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 stale/optimistic 截图全过 | SDSO-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 stale 面板 → 点击「触发指标乐观更新」→ 对照 tablet/mobile light/dark 八张 stale/optimistic 截图。

## SDSO-07 — DevOps 阶段 stale/optimistic tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-stale.png`、`scenario-devops-domain-mobile-dark-optimistic.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark stale | `scenario-devops-domain-tablet-stale.png` + `scenario-devops-domain-tablet-dark-stale.png` stale framing 正常 | SDSO-07 · RESP-06 |
| 2 | mobile light/dark optimistic | `scenario-devops-domain-mobile-optimistic.png` + `scenario-devops-domain-mobile-dark-optimistic.png` optimistic framing 正常 | SDSO-07 · RESP-07 |
| 3 | 阶段 stale/optimistic | 流水线 stale banner + 乐观更新摘要 tablet/mobile light/dark 首屏可见 | SDSO-07 · PAT-07 |
| 4 | optimistic 态 | mobile dark 下 optimistic 文案与撤销按钮可辨认 | SDSO-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 stale/optimistic 截图全过 | SDSO-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 stale 面板 → 点击「触发阶段乐观更新」→ 对照 tablet/mobile light/dark 八张截图。

## SDSO-08 — Gateway 端点 stale/optimistic tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-stale.png`、`scenario-gateway-domain-mobile-dark-optimistic.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark stale | `scenario-gateway-domain-tablet-stale.png` + `scenario-gateway-domain-tablet-dark-stale.png` stale framing 正常 | SDSO-08 · RESP-06 |
| 2 | mobile light/dark optimistic | `scenario-gateway-domain-mobile-optimistic.png` + `scenario-gateway-domain-mobile-dark-optimistic.png` optimistic framing 正常 | SDSO-08 · RESP-07 |
| 3 | 端点 stale/optimistic | 端点 stale banner + 乐观更新摘要 tablet/mobile light/dark 首屏可见 | SDSO-08 · PAT-08 |
| 4 | stale 态 | mobile dark 下同步指示器与缓存文案可辨认 | SDSO-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 stale/optimistic 截图全过 | SDSO-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 stale 面板 → 点击「触发端点乐观更新」→ 对照 tablet/mobile light/dark 八张截图。

## SDSO-09 — Governance 审计行 stale/optimistic tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-stale.png`、`scenario-governance-domain-mobile-stale.png`、`scenario-governance-domain-mobile-dark-optimistic.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark stale | `scenario-governance-domain-tablet-stale.png` + `scenario-governance-domain-tablet-dark-stale.png` stale framing 正常 | SDSO-09 · RESP-06 |
| 2 | mobile light/dark optimistic | `scenario-governance-domain-mobile-optimistic.png` + `scenario-governance-domain-mobile-dark-optimistic.png` optimistic framing 正常 | SDSO-09 · RESP-07 |
| 3 | 审计 stale/optimistic | 审计 stale banner + 乐观更新摘要 tablet/mobile light/dark 首屏可见 | SDSO-09 · PAT-09 |
| 4 | optimistic 文案 | mobile dark 下「已乐观更新，等待服务端确认」文案可辨认 | SDSO-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 stale/optimistic 截图全过 | SDSO-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 stale 面板 → 点击「触发审计乐观更新」→ 对照 tablet/mobile light/dark 八张截图。

## SDSO-10 — 场景域 stale/optimistic tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{stale,optimistic}.png` + `scenarioDomainStaleOptimisticViewportLightDarkScreenshotStates.staleOptimisticStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × stale/optimistic 全量 golden 存在 | SDSO-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainStaleOptimisticViewportLightDarkScreenshots` 通过 | SDSO-10 · PREVIEW-* |
| 3 | stale 态 | 五域 `data-audit="scenario-domain-stale-overlay"` `data-state="stale"` 可见 | SDSO-10 · LOGIC-* |
| 4 | optimistic 态 | 五域点击 optimistic trigger 后 `role="status"` + `data-state="optimistic"` 可见 | SDSO-10 · ASYNC-* |
| 5 | 矩阵完整 | `staleOptimisticStateMatrixComplete = true` | SDSO-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张 stale/optimistic 截图与门禁 JSON 输出。
