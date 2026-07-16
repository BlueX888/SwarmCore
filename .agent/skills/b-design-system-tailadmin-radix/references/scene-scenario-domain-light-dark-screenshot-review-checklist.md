# 场景 Scenario Domain Light/Dark Screenshot 评审清单

> DOCS-045 / G94 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 light/dark 双主题独立截图抽检**，确保各域 section 有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-light-dark-screenshot-review-checklist.md`（SDLD-01～05）、`scene-scenario-domain-independent-screenshot-review-checklist.md`（SDIS-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 light/dark 独立截图矩阵抽检 | 对应 SDLD 块 + `quality-rubric.md` |
| BI Analytics 多页面工作台 light/dark 独立截图 | SDLD-06 + `tailadmin-bi-analytics` |
| DevOps 发布运行详情 light/dark 独立截图 | SDLD-07 + `scenario-devops` |
| Gateway 控制平面 light/dark 独立截图 | SDLD-08 + `scenario-gateway` |
| Governance 治理审计 light/dark 独立截图 | SDLD-09 + `scenario-governance` |
| 场景域 light/dark 独立截图束缺门禁 | SDLD-10 + `verify:runtime` `scenarioDomainLightDarkScreenshotStates` |

## 通用前置

1. 先完成 `scenario-domain-light-dark-screenshot-review-checklist.md` SDLD-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain.png` 与 `scenario-*-domain-dark.png` 共 10 张独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + DevOps 或 Gateway** light/dark 独立截图。
4. 视口 **desktop 1440×1000**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 light/dark 独立截图（G94）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 light/dark 独立截图抽检行。

## SDLD-06 — BI Analytics light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain.png`、`scenario-bi-domain-dark.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | light 独立截图 | `scenario-bi-domain.png` framing 正常，非合并门禁裁剪 | SDLD-06 · REV-06 |
| 2 | dark 独立截图 | `scenario-bi-domain-dark.png` framing 正常 | SDLD-06 · VIS-05 |
| 3 | Data Screen | Data Screen tab 画布 + KPI light/dark 首屏可见 | SDLD-06 · PAT-06 |
| 4 | 主题对比 | dark 下 KPI/图表 grid/legend 边框背景文字层级可辨认 | SDLD-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 双主题截图全过 | SDLD-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 切换 Data Screen tab → 对照 light 截图 → 切换主题 → 对照 dark 截图。

## SDLD-07 — DevOps light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain.png`、`scenario-devops-domain-dark.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | light 独立截图 | `scenario-devops-domain.png` framing 正常 | SDLD-07 · REV-07 |
| 2 | dark 独立截图 | `scenario-devops-domain-dark.png` framing 正常 | SDLD-07 · VIS-05 |
| 3 | 流水线阶段 | PipelineStageBar 6 阶段 light/dark 等宽首屏可见 | SDLD-07 · PAT-07 |
| 4 | 日志流 | LogStreamPanel dark 下等宽字体可读 | SDLD-07 · VIS-07 |
| 5 | example runtime | DevOps 场景 section + 双主题截图全过 | SDLD-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 light/dark 双截图 → 检查 PipelineStageBar + LogStreamPanel framing。

## SDLD-08 — Gateway light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain.png`、`scenario-gateway-domain-dark.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | light 独立截图 | `scenario-gateway-domain.png` framing 正常 | SDLD-08 · REV-08 |
| 2 | dark 独立截图 | `scenario-gateway-domain-dark.png` framing 正常 | SDLD-08 · VIS-05 |
| 3 | 部署矩阵 | DeploymentModeMatrix 4 模式 light/dark 首屏可见 | SDLD-08 · PAT-08 |
| 4 | KPI 栅格 | 4 列网关 KPI dark 下对齐不丢失 | SDLD-08 · RESP-08 |
| 5 | example runtime | Gateway 场景 section + 双主题截图全过 | SDLD-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 light/dark 双截图 → 检查 DeploymentModeMatrix framing。

## SDLD-09 — Governance light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain.png`、`scenario-governance-domain-dark.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | light 独立截图 | `scenario-governance-domain.png` framing 正常 | SDLD-09 · REV-09 |
| 2 | dark 独立截图 | `scenario-governance-domain-dark.png` framing 正常 | SDLD-09 · VIS-05 |
| 3 | 权限矩阵 | PermissionMatrix 行列对齐 light/dark 首屏可见 | SDLD-09 · PAT-09 |
| 4 | 审计日志 | AuditLogTable dark 下时间/操作/结果列密度一致 | SDLD-09 · VIS-09 |
| 5 | example runtime | Governance 场景 section + 双主题截图全过 | SDLD-09 · PREVIEW-* |

**交互动作**：打开治理场景 → 对照 light/dark 双截图 → 检查 PermissionMatrix framing。

## SDLD-10 — 场景域 light/dark 独立截图束

**对照 golden**：`scenario-*-domain.png` + `scenario-*-domain-dark.png`（10 张）、`verifyScenarioDomainLightDarkScreenshots`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 五域 light 截图 | 5 张 `scenario-*-domain.png` 均存在且 framing 正常 | SDLD-10 · VAL-* |
| 2 | 五域 dark 截图 | 5 张 `scenario-*-domain-dark.png` 均存在且 framing 正常 | SDLD-10 · VIS-05 |
| 3 | 主题切换 | runtime 通过「切换主题」进入 `.app.dark` 再截图 | SDLD-10 · INTER-10 |
| 4 | audit 静态 | `audit` 含 `verifyScenarioDomainLightDarkScreenshots` marker | SDLD-10 · COV-10 |
| 5 | 与 SDIS 串联 | light 截图与 SDIS 五域独立截图同轮可访问 | SDLD-10 · PREVIEW-* |

**交互动作**：跑 `npm run verify:runtime` → 确认 `scenarioDomainLightDarkScreenshotStates.themeMatrixComplete = true` → 对照 10 张独立截图。

## 交叉引用

- `scenario-domain-light-dark-screenshot-review-checklist.md` — SDLD-01～05
- `scenario-domain-independent-screenshot-review-checklist.md` — SDIS-01～05
- `scene-scenario-domain-independent-screenshot-review-checklist.md` — SDIS-06～10
- `scene-ui-drift-review-checklist.md` — REV-06～10
- `business-validation-checklist.md` — VAL-* 场景冒烟
- `decision-matrix.md` — G94 场景域 light/dark 独立截图选型表
- `upgrade-troubleshooting.md` — SDLD-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域 light/dark 独立截图检索路径
- `quality-rubric.md` — 综合美学维度
