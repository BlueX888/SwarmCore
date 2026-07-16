# 场景 Scenario Domain Mutation Rollback Viewport Light/Dark Screenshot 评审清单

> DOCS-057 / G106 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 mutation pending/rollback 独立截图抽检**，确保各域 section 在变更提交中与服务端拒绝回滚态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md`（SDMR-01～05）、`scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md`（SDSO-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 mutation pending/rollback tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDMR 块 + `quality-rubric.md` |
| BI Analytics 指标 mutation pending/rollback tablet/mobile light/dark 独立截图 | SDMR-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 mutation pending/rollback tablet/mobile light/dark 独立截图 | SDMR-07 + `scenario-devops` |
| Gateway 端点 mutation pending/rollback tablet/mobile light/dark 独立截图 | SDMR-08 + `scenario-gateway` |
| Governance 审计行 mutation pending/rollback tablet/mobile light/dark 独立截图 | SDMR-09 + `scenario-governance` |
| 场景域 mutation pending/rollback tablet/mobile light/dark 独立截图束缺门禁 | SDMR-10 + `verify:runtime` `scenarioDomainMutationRollbackViewportLightDarkScreenshotStates` + `verifyScenarioDomainMutationRollbackViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md` SDMR-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{mutation-pending,rollback}.png` 共 40 张 mutation pending/rollback 独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark mutation pending/rollback 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 mutation pending/rollback tablet/mobile light/dark 独立截图（G106）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 mutation pending/rollback tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDMR-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDMR-06 — BI Analytics 指标 mutation pending/rollback tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-mutation-pending.png`、`scenario-bi-domain-mobile-dark-rollback.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark stale | `scenario-bi-domain-tablet-mutation-pending.png` + `scenario-bi-domain-tablet-dark-mutation-pending.png` mutation-pending framing 正常 | SDMR-06 · RESP-06 |
| 2 | mobile light/dark optimistic | `scenario-bi-domain-mobile-rollback.png` + `scenario-bi-domain-mobile-dark-rollback.png` rollback framing 正常 | SDMR-06 · RESP-07 |
| 3 | 指标 mutation pending/rollback | 提交 banner + spinner + 回滚 banner tablet/mobile light/dark 首屏可见 | SDMR-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 提交 banner 与 rollback banner 层级可辨认 | SDMR-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 mutation pending/rollback 截图全过 | SDMR-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 stale 面板 → 点击「触发指标变更回滚」→ 对照 tablet/mobile light/dark 八张 mutation pending/rollback 截图。

## SDMR-07 — DevOps 阶段 mutation pending/rollback tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-mutation-pending.png`、`scenario-devops-domain-mobile-dark-rollback.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark stale | `scenario-devops-domain-tablet-mutation-pending.png` + `scenario-devops-domain-tablet-dark-mutation-pending.png` mutation-pending framing 正常 | SDMR-07 · RESP-06 |
| 2 | mobile light/dark optimistic | `scenario-devops-domain-mobile-rollback.png` + `scenario-devops-domain-mobile-dark-rollback.png` rollback framing 正常 | SDMR-07 · RESP-07 |
| 3 | 阶段 mutation pending/rollback | 流水线 stale banner + 乐观更新摘要 tablet/mobile light/dark 首屏可见 | SDMR-07 · PAT-07 |
| 4 | optimistic 态 | mobile dark 下 rollback 文案与恢复按钮可辨认 | SDMR-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 mutation pending/rollback 截图全过 | SDMR-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 stale 面板 → 点击「触发阶段变更回滚」→ 对照 tablet/mobile light/dark 八张截图。

## SDMR-08 — Gateway 端点 mutation pending/rollback tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-mutation-pending.png`、`scenario-gateway-domain-mobile-dark-rollback.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark stale | `scenario-gateway-domain-tablet-mutation-pending.png` + `scenario-gateway-domain-tablet-dark-mutation-pending.png` mutation-pending framing 正常 | SDMR-08 · RESP-06 |
| 2 | mobile light/dark optimistic | `scenario-gateway-domain-mobile-rollback.png` + `scenario-gateway-domain-mobile-dark-rollback.png` rollback framing 正常 | SDMR-08 · RESP-07 |
| 3 | 端点 mutation pending/rollback | 端点 stale banner + 乐观更新摘要 tablet/mobile light/dark 首屏可见 | SDMR-08 · PAT-08 |
| 4 | stale 态 | mobile dark 下spinner 与提交文案可辨认 | SDMR-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 mutation pending/rollback 截图全过 | SDMR-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 stale 面板 → 点击「触发端点变更回滚」→ 对照 tablet/mobile light/dark 八张截图。

## SDMR-09 — Governance 审计行 mutation pending/rollback tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-mutation-pending.png`、`scenario-governance-domain-mobile-mutation-pending.png`、`scenario-governance-domain-mobile-dark-rollback.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark stale | `scenario-governance-domain-tablet-mutation-pending.png` + `scenario-governance-domain-tablet-dark-mutation-pending.png` mutation-pending framing 正常 | SDMR-09 · RESP-06 |
| 2 | mobile light/dark optimistic | `scenario-governance-domain-mobile-rollback.png` + `scenario-governance-domain-mobile-dark-rollback.png` rollback framing 正常 | SDMR-09 · RESP-07 |
| 3 | 审计 mutation pending/rollback | 审计 stale banner + 乐观更新摘要 tablet/mobile light/dark 首屏可见 | SDMR-09 · PAT-09 |
| 4 | optimistic 文案 | mobile dark 下「服务端拒绝变更，已自动回滚至上一版本」文案可辨认 | SDMR-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 mutation pending/rollback 截图全过 | SDMR-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 stale 面板 → 点击「触发审计变更回滚」→ 对照 tablet/mobile light/dark 八张截图。

## SDMR-10 — 场景域 mutation pending/rollback tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{mutation-pending,rollback}.png` + `scenarioDomainMutationRollbackViewportLightDarkScreenshotStates.mutationRollbackStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × mutation pending/rollback 全量 golden 存在 | SDMR-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainMutationRollbackViewportLightDarkScreenshots` 通过 | SDMR-10 · PREVIEW-* |
| 3 | stale 态 | 五域 `data-audit="scenario-domain-mutation-pending-overlay"` `data-state="mutation-pending"` 可见 | SDMR-10 · LOGIC-* |
| 4 | optimistic 态 | 五域点击 rollback trigger 后 `role="status"` + `data-state="rollback"` 可见 | SDMR-10 · ASYNC-* |
| 5 | 矩阵完整 | `mutationRollbackStateMatrixComplete = true` | SDMR-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张 mutation pending/rollback 截图与门禁 JSON 输出。
