# 场景 Scenario Domain Conflict Merge Viewport Light/Dark Screenshot 评审清单

> DOCS-058 / G107 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 conflict/merged 独立截图抽检**，确保各域 section 在版本冲突检测态与合并完成态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md`（SDCM-01～05）、`scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md`（SDMR-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 conflict/merge tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDCM 块 + `quality-rubric.md` |
| BI Analytics 指标 conflict/merge tablet/mobile light/dark 独立截图 | SDCM-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 conflict/merge tablet/mobile light/dark 独立截图 | SDCM-07 + `scenario-devops` |
| Gateway 端点 conflict/merge tablet/mobile light/dark 独立截图 | SDCM-08 + `scenario-gateway` |
| Governance 审计行 conflict/merge tablet/mobile light/dark 独立截图 | SDCM-09 + `scenario-governance` |
| 场景域 conflict/merge tablet/mobile light/dark 独立截图束缺门禁 | SDCM-10 + `verify:runtime` `scenarioDomainConflictMergeViewportLightDarkScreenshotStates` + `verifyScenarioDomainConflictMergeViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md` SDCM-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{conflict,merged}.png` 共 40 张 conflict/merged 独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark conflict/merged 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 conflict/merge tablet/mobile light/dark 独立截图（G107）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 conflict/merge tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDCM-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDCM-06 — BI Analytics 指标 conflict/merge tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-conflict.png`、`scenario-bi-domain-mobile-dark-merged.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark conflict | `scenario-bi-domain-tablet-conflict.png` + `scenario-bi-domain-tablet-dark-conflict.png` conflict framing 正常 | SDCM-06 · RESP-06 |
| 2 | mobile light/dark merged | `scenario-bi-domain-mobile-merged.png` + `scenario-bi-domain-mobile-dark-merged.png` merged framing 正常 | SDCM-06 · RESP-07 |
| 3 | 指标 conflict/merge | 冲突 banner + 冲突字段摘要 + 合并完成 banner tablet/mobile light/dark 首屏可见 | SDCM-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 conflict banner 与 merged banner 层级可辨认 | SDCM-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 conflict/merged 截图全过 | SDCM-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 conflict 面板 → 点击「触发指标冲突合并」→ 对照 tablet/mobile light/dark 八张 conflict/merged 截图。

## SDCM-07 — DevOps 阶段 conflict/merge tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-conflict.png`、`scenario-devops-domain-mobile-dark-merged.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark conflict | `scenario-devops-domain-tablet-conflict.png` + `scenario-devops-domain-tablet-dark-conflict.png` conflict framing 正常 | SDCM-07 · RESP-06 |
| 2 | mobile light/dark merged | `scenario-devops-domain-mobile-merged.png` + `scenario-devops-domain-mobile-dark-merged.png` merged framing 正常 | SDCM-07 · RESP-07 |
| 3 | 阶段 conflict/merge | 流水线冲突 banner + 合并完成摘要 tablet/mobile light/dark 首屏可见 | SDCM-07 · PAT-07 |
| 4 | merged 态 | mobile dark 下 merged 文案与查看详情按钮可辨认 | SDCM-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 conflict/merged 截图全过 | SDCM-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 conflict 面板 → 点击「触发阶段冲突合并」→ 对照 tablet/mobile light/dark 八张截图。

## SDCM-08 — Gateway 端点 conflict/merge tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-conflict.png`、`scenario-gateway-domain-mobile-dark-merged.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark conflict | `scenario-gateway-domain-tablet-conflict.png` + `scenario-gateway-domain-tablet-dark-conflict.png` conflict framing 正常 | SDCM-08 · RESP-06 |
| 2 | mobile light/dark merged | `scenario-gateway-domain-mobile-merged.png` + `scenario-gateway-domain-mobile-dark-merged.png` merged framing 正常 | SDCM-08 · RESP-07 |
| 3 | 端点 conflict/merge | 端点冲突 banner + 合并完成摘要 tablet/mobile light/dark 首屏可见 | SDCM-08 · PAT-08 |
| 4 | conflict 态 | mobile dark 下冲突字段与 banner 可辨认 | SDCM-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 conflict/merged 截图全过 | SDCM-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 conflict 面板 → 点击「触发端点冲突合并」→ 对照 tablet/mobile light/dark 八张截图。

## SDCM-09 — Governance 审计行 conflict/merge tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-conflict.png`、`scenario-governance-domain-mobile-conflict.png`、`scenario-governance-domain-mobile-dark-merged.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark conflict | `scenario-governance-domain-tablet-conflict.png` + `scenario-governance-domain-tablet-dark-conflict.png` conflict framing 正常 | SDCM-09 · RESP-06 |
| 2 | mobile light/dark merged | `scenario-governance-domain-mobile-merged.png` + `scenario-governance-domain-mobile-dark-merged.png` merged framing 正常 | SDCM-09 · RESP-07 |
| 3 | 审计 conflict/merge | 审计冲突 banner + 合并完成摘要 tablet/mobile light/dark 首屏可见 | SDCM-09 · PAT-09 |
| 4 | merged 文案 | mobile dark 下「冲突已合并，可继续发布策略变更」文案可辨认 | SDCM-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 conflict/merged 截图全过 | SDCM-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 conflict 面板 → 点击「触发审计冲突合并」→ 对照 tablet/mobile light/dark 八张截图。

## SDCM-10 — 场景域 conflict/merge tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{conflict,merged}.png` + `scenarioDomainConflictMergeViewportLightDarkScreenshotStates.conflictMergeStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × conflict/merged 全量 golden 存在 | SDCM-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainConflictMergeViewportLightDarkScreenshots` 通过 | SDCM-10 · PREVIEW-* |
| 3 | conflict 态 | 五域 `data-audit="scenario-domain-conflict-overlay"` `data-state="conflict"` 可见 | SDCM-10 · LOGIC-* |
| 4 | merged 态 | 五域点击 merge trigger 后 `role="status"` + `data-state="merged"` 可见 | SDCM-10 · ASYNC-* |
| 5 | 矩阵完整 | `conflictMergeStateMatrixComplete = true` | SDCM-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张 conflict/merged 截图与门禁 JSON 输出。
