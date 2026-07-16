# 场景 Scenario Domain Viewport Light/Dark Screenshot 评审清单

> DOCS-046 / G95 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题独立截图抽检**，确保各域 section 在平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-viewport-light-dark-screenshot-review-checklist.md`（SDTM-01～05）、`scene-scenario-domain-light-dark-screenshot-review-checklist.md`（SDLD-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDTM 块 + `quality-rubric.md` |
| BI Analytics 多页面工作台 tablet/mobile light/dark 独立截图 | SDTM-06 + `tailadmin-bi-analytics` |
| DevOps 发布运行详情 tablet/mobile light/dark 独立截图 | SDTM-07 + `scenario-devops` |
| Gateway 控制平面 tablet/mobile light/dark 独立截图 | SDTM-08 + `scenario-gateway` |
| Governance 治理审计 tablet/mobile light/dark 独立截图 | SDTM-09 + `scenario-governance` |
| 场景域 tablet/mobile light/dark 独立截图束缺门禁 | SDTM-10 + `verify:runtime` `scenarioDomainViewportLightDarkScreenshotStates` |

## 通用前置

1. 先完成 `scenario-domain-viewport-light-dark-screenshot-review-checklist.md` SDTM-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}.png` 共 20 张独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + DevOps 或 Gateway** tablet/mobile light/dark 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 tablet/mobile light/dark 独立截图（G95）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 tablet/mobile light/dark 独立截图抽检行。

## SDTM-06 — BI Analytics tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet.png`、`scenario-bi-domain-mobile-dark.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark | `scenario-bi-domain-tablet.png` + `scenario-bi-domain-tablet-dark.png` framing 正常 | SDTM-06 · RESP-06 |
| 2 | mobile light/dark | `scenario-bi-domain-mobile.png` + `scenario-bi-domain-mobile-dark.png` framing 正常 | SDTM-06 · RESP-07 |
| 3 | Data Screen | Data Screen tab 画布 tablet/mobile light/dark 首屏可见 | SDTM-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 KPI/图表 grid/legend 边框背景文字层级可辨认 | SDTM-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 四视口双主题截图全过 | SDTM-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 切换 Data Screen tab → 对照 tablet/mobile light/dark 四张截图。

## SDTM-07 — DevOps tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet.png`、`scenario-devops-domain-mobile-dark.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark | `scenario-devops-domain-tablet.png` + `scenario-devops-domain-tablet-dark.png` framing 正常 | SDTM-07 · RESP-06 |
| 2 | mobile light/dark | `scenario-devops-domain-mobile.png` + `scenario-devops-domain-mobile-dark.png` framing 正常 | SDTM-07 · RESP-07 |
| 3 | 流水线阶段 | PipelineStageBar 6 阶段 tablet/mobile light/dark 首屏可见 | SDTM-07 · PAT-07 |
| 4 | 日志流 | LogStreamPanel mobile dark 下等宽字体可读 | SDTM-07 · VIS-07 |
| 5 | example runtime | DevOps 场景 section + 四视口双主题截图全过 | SDTM-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 tablet/mobile light/dark 四张截图 → 检查 PipelineStageBar + LogStreamPanel framing。

## SDTM-08 — Gateway tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet.png`、`scenario-gateway-domain-mobile-dark.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark | `scenario-gateway-domain-tablet.png` + `scenario-gateway-domain-tablet-dark.png` framing 正常 | SDTM-08 · RESP-06 |
| 2 | mobile light/dark | `scenario-gateway-domain-mobile.png` + `scenario-gateway-domain-mobile-dark.png` framing 正常 | SDTM-08 · RESP-07 |
| 3 | 部署矩阵 | DeploymentModeMatrix 4 模式 tablet/mobile light/dark 首屏可见 | SDTM-08 · PAT-08 |
| 4 | KPI 栅格 | mobile dark 下 4 列网关 KPI 对齐不丢失 | SDTM-08 · RESP-08 |
| 5 | example runtime | Gateway 场景 section + 四视口双主题截图全过 | SDTM-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 tablet/mobile light/dark 四张截图 → 检查 DeploymentModeMatrix framing。

## SDTM-09 — Governance tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet.png`、`scenario-governance-domain-mobile-dark.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark | `scenario-governance-domain-tablet.png` + `scenario-governance-domain-tablet-dark.png` framing 正常 | SDTM-09 · RESP-06 |
| 2 | mobile light/dark | `scenario-governance-domain-mobile.png` + `scenario-governance-domain-mobile-dark.png` framing 正常 | SDTM-09 · RESP-07 |
| 3 | 权限矩阵 | PermissionMatrix 行列对齐 tablet/mobile light/dark 首屏可见 | SDTM-09 · PAT-09 |
| 4 | 审计日志 | AuditLogTable mobile dark 下时间/操作/结果列密度一致 | SDTM-09 · VIS-09 |
| 5 | example runtime | Governance 场景 section + 四视口双主题截图全过 | SDTM-09 · PREVIEW-* |

**交互动作**：打开治理场景 → 对照 tablet/mobile light/dark 四张截图 → 检查 PermissionMatrix framing。

## SDTM-10 — 场景域 tablet/mobile light/dark 独立截图束

**对照 golden**：`scenario-*-domain-{tablet,mobile}{,-dark}.png`（20 张）、`verifyScenarioDomainViewportLightDarkScreenshots`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 五域 tablet light 截图 | 5 张 `scenario-*-domain-tablet.png` 均存在且 framing 正常 | SDTM-10 · RESP-06 |
| 2 | 五域 tablet dark 截图 | 5 张 `scenario-*-domain-tablet-dark.png` 均存在且 framing 正常 | SDTM-10 · VIS-05 |
| 3 | 五域 mobile light 截图 | 5 张 `scenario-*-domain-mobile.png` 均存在且首屏主任务可见 | SDTM-10 · RESP-07 |
| 4 | 五域 mobile dark 截图 | 5 张 `scenario-*-domain-mobile-dark.png` 均存在且对比度可辨认 | SDTM-10 · VIS-06 |
| 5 | runtime 门禁 | `scenarioDomainViewportLightDarkScreenshotStates.viewportMatrixComplete = true` | SDTM-10 · VAL-* |

**交互动作**：跑 `npm run verify:runtime` → 确认 `viewportMatrixComplete = true` → 对照 20 张独立截图。

## 交叉引用

- `scenario-domain-viewport-light-dark-screenshot-review-checklist.md` — SDTM-01～05
- `scenario-domain-light-dark-screenshot-review-checklist.md` — SDLD-01～05
- `scene-scenario-domain-light-dark-screenshot-review-checklist.md` — SDLD-06～10
- `scene-responsive-review-checklist.md` — RESP-06～10
- `business-validation-checklist.md` — VAL-* 场景冒烟
- `decision-matrix.md` — G95 场景域 tablet/mobile light/dark 独立截图选型表
- `upgrade-troubleshooting.md` — SDTM-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域 tablet/mobile light/dark 独立截图检索路径
- `quality-rubric.md` — 综合美学维度
