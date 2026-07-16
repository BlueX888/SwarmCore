# Scenario Domain Conflict Merge Viewport Light/Dark Screenshot 评审清单

> DOCS-058 / G107 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 conflict/merged 独立截图视觉回归抽检**，确保每个场景 section 在版本冲突检测态、合并完成态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md`（SDMR-01～05）、`scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md`（SDCM-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 conflict/merge tablet/mobile light/dark 独立截图抽检 | 对应 SDCM 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标 conflict/merge tablet/mobile light/dark golden 对照 | SDCM-01 + `scenario-bi-domain-tablet-conflict.png` + `scenario-bi-domain-mobile-dark-merged.png` |
| DevOps 场景阶段 conflict/merge tablet/mobile light/dark golden 对照 | SDCM-02 + `scenario-devops-domain-tablet-conflict.png` + `scenario-devops-domain-mobile-dark-merged.png` |
| Gateway 场景端点 conflict/merge tablet/mobile light/dark golden 对照 | SDCM-03 + `scenario-gateway-domain-tablet-conflict.png` + `scenario-gateway-domain-mobile-dark-merged.png` |
| Governance 场景审计行 conflict/merge tablet/mobile light/dark golden 对照 | SDCM-04 + `scenario-governance-domain-tablet-conflict.png` + `scenario-governance-domain-mobile-dark-merged.png` |
| PaaS 场景容量 conflict/merge tablet/mobile light/dark golden 对照 | SDCM-05 + `scenario-paas-domain-tablet-conflict.png` + `scenario-paas-domain-mobile-dark-merged.png` |

## 通用前置

1. 先完成 `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md` SDMR-01～05（mutation pending/rollback 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{conflict,merged}.png` 四视口双主题 conflict/merged 独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 conflict 与一张 merged 独立截图；conflict 必须出现冲突 banner 与冲突字段摘要，merged 必须出现合并完成 banner 与查看详情 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. conflict/merged 截图出现文案裁切、冲突 banner 对比度不足、merged banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 conflict/merge tablet/mobile light/dark 独立截图（G107）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 conflict/merge tablet/mobile light/dark 独立截图抽检行。

## SDCM-01 — BI 场景指标 conflict/merge tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-conflict.png`、`scenario-bi-domain-tablet-dark-conflict.png`、`scenario-bi-domain-mobile-conflict.png`、`scenario-bi-domain-mobile-dark-conflict.png`、`scenario-bi-domain-tablet-merged.png`、`scenario-bi-domain-tablet-dark-merged.png`、`scenario-bi-domain-mobile-merged.png`、`scenario-bi-domain-mobile-dark-merged.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light conflict 截图 | `scenario-bi-domain-tablet-conflict.png` 存在且 conflict framing 正常 | SDCM-01 · RESP-06 |
| 2 | tablet dark conflict 截图 | `scenario-bi-domain-tablet-dark-conflict.png` 存在且冲突 banner 可读 | SDCM-01 · VIS-05 |
| 3 | mobile light merged 截图 | `scenario-bi-domain-mobile-merged.png` merged banner 首屏可见 | SDCM-01 · RESP-07 |
| 4 | mobile dark merged 截图 | `scenario-bi-domain-mobile-dark-merged.png` merged 对比度可辨认 | SDCM-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainConflictMergeViewportLightDarkScreenshots` biDomain 全过 | SDCM-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 conflict 面板 → 点击「触发指标冲突合并」→ 对照 tablet/mobile light/dark 八张 conflict/merged 截图。

## SDCM-02 — DevOps 场景阶段 conflict/merge tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-conflict.png`、`scenario-devops-domain-tablet-dark-conflict.png`、`scenario-devops-domain-mobile-conflict.png`、`scenario-devops-domain-mobile-dark-conflict.png`、`scenario-devops-domain-tablet-merged.png`、`scenario-devops-domain-tablet-dark-merged.png`、`scenario-devops-domain-mobile-merged.png`、`scenario-devops-domain-mobile-dark-merged.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light conflict 截图 | `scenario-devops-domain-tablet-conflict.png` 存在且 conflict framing 正常 | SDCM-02 · RESP-06 |
| 2 | tablet dark conflict 截图 | `scenario-devops-domain-tablet-dark-conflict.png` 存在且阶段冲突可读 | SDCM-02 · VIS-05 |
| 3 | mobile light merged 截图 | `scenario-devops-domain-mobile-merged.png` 流水线 merged 首屏可见 | SDCM-02 · RESP-07 |
| 4 | mobile dark merged 截图 | `scenario-devops-domain-mobile-dark-merged.png` merged 对比度可辨认 | SDCM-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + conflict/merge tablet/mobile light/dark 可见 | SDCM-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 conflict 面板 → 点击「触发阶段冲突合并」→ 对照 tablet/mobile light/dark 八张截图。

## SDCM-03 — Gateway 场景端点 conflict/merge tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-conflict.png`、`scenario-gateway-domain-tablet-dark-conflict.png`、`scenario-gateway-domain-mobile-conflict.png`、`scenario-gateway-domain-mobile-dark-conflict.png`、`scenario-gateway-domain-tablet-merged.png`、`scenario-gateway-domain-tablet-dark-merged.png`、`scenario-gateway-domain-mobile-merged.png`、`scenario-gateway-domain-mobile-dark-merged.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light conflict 截图 | `scenario-gateway-domain-tablet-conflict.png` 存在且 conflict framing 正常 | SDCM-03 · RESP-06 |
| 2 | tablet dark conflict 截图 | `scenario-gateway-domain-tablet-dark-conflict.png` 存在且端点冲突可读 | SDCM-03 · VIS-05 |
| 3 | mobile light merged 截图 | `scenario-gateway-domain-mobile-merged.png` 端点 merged 首屏可见 | SDCM-03 · RESP-07 |
| 4 | mobile dark merged 截图 | `scenario-gateway-domain-mobile-dark-merged.png` merged 层级不丢失 | SDCM-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + conflict/merge tablet/mobile light/dark 可见 | SDCM-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 conflict 面板 → 点击「触发端点冲突合并」→ 对照 tablet/mobile light/dark 八张截图。

## SDCM-04 — Governance 场景审计行 conflict/merge tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-conflict.png`、`scenario-governance-domain-tablet-dark-conflict.png`、`scenario-governance-domain-mobile-conflict.png`、`scenario-governance-domain-mobile-dark-conflict.png`、`scenario-governance-domain-tablet-merged.png`、`scenario-governance-domain-tablet-dark-merged.png`、`scenario-governance-domain-mobile-merged.png`、`scenario-governance-domain-mobile-dark-merged.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light conflict 截图 | `scenario-governance-domain-tablet-conflict.png` 存在且 conflict framing 正常 | SDCM-04 · RESP-06 |
| 2 | tablet dark conflict 截图 | `scenario-governance-domain-tablet-dark-conflict.png` 存在且审计冲突可读 | SDCM-04 · VIS-05 |
| 3 | mobile light merged 截图 | `scenario-governance-domain-mobile-merged.png` 审计 merged 首屏可见 | SDCM-04 · RESP-07 |
| 4 | mobile dark merged 截图 | `scenario-governance-domain-mobile-dark-merged.png` merged 密度一致 | SDCM-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + conflict/merge tablet/mobile light/dark 可见 | SDCM-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 conflict 面板 → 点击「触发审计冲突合并」→ 对照 tablet/mobile light/dark 八张截图。

## SDCM-05 — PaaS 场景容量 conflict/merge tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-conflict.png`、`scenario-paas-domain-tablet-dark-conflict.png`、`scenario-paas-domain-mobile-conflict.png`、`scenario-paas-domain-mobile-dark-conflict.png`、`scenario-paas-domain-tablet-merged.png`、`scenario-paas-domain-tablet-dark-merged.png`、`scenario-paas-domain-mobile-merged.png`、`scenario-paas-domain-mobile-dark-merged.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light conflict 截图 | `scenario-paas-domain-tablet-conflict.png` 存在且 conflict framing 正常 | SDCM-05 · RESP-06 |
| 2 | tablet dark conflict 截图 | `scenario-paas-domain-tablet-dark-conflict.png` 存在且容量冲突可读 | SDCM-05 · VIS-05 |
| 3 | mobile light merged 截图 | `scenario-paas-domain-mobile-merged.png` 容量 merged 首屏可见 | SDCM-05 · RESP-07 |
| 4 | mobile dark merged 截图 | `scenario-paas-domain-mobile-dark-merged.png` merged 列表项可辨认 | SDCM-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + conflict/merge tablet/mobile light/dark 可见 | SDCM-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 conflict 面板 → 点击「触发容量冲突合并」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md` SDCM-06～10
- mutation pending/rollback 前置：`scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md` SDMR-01～05
- 选型表：`decision-matrix.md` G107 场景域 conflict/merge tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDCM-01～10
- Runtime 门禁：`verifyScenarioDomainConflictMergeViewportLightDarkScreenshots`
