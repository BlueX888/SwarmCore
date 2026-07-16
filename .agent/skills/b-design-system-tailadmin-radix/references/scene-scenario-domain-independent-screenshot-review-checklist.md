# 场景 Scenario Domain Independent Screenshot 评审清单

> DOCS-044 / G93 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级独立截图抽检**，确保各域 section 有独立 golden 截图矩阵，并与 `scenario-domain-independent-screenshot-review-checklist.md`（SDIS-01～05）、`scene-scenario-page-visual-regression-review-checklist.md`（SPVR-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域独立截图矩阵抽检 | 对应 SDIS 块 + `quality-rubric.md` |
| BI Analytics 多页面工作台独立截图 | SDIS-06 + `tailadmin-bi-analytics` |
| DevOps 发布运行详情独立截图 | SDIS-07 + `scenario-devops` |
| Gateway 控制平面独立截图 | SDIS-08 + `scenario-gateway` |
| Governance 治理审计独立截图 | SDIS-09 + `scenario-governance` |
| 场景域独立截图束缺门禁 | SDIS-10 + `verify:runtime` `scenarioDomainScreenshotStates` |

## 通用前置

1. 先完成 `scenario-domain-independent-screenshot-review-checklist.md` SDIS-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain.png` 五张独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + DevOps 或 Gateway** 独立截图。
4. 视口 **desktop 1440×1000** 与 **mobile 390×844** 各 1 次首屏宽度检查。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域独立截图（G93）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域独立截图抽检行。

## SDIS-06 — BI Analytics 独立截图矩阵

**对照 golden**：`scenario-bi-domain.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 独立截图 | `scenario-bi-domain.png` framing 正常，非合并门禁裁剪 | SDIS-06 · REV-06 |
| 2 | Data Screen | Data Screen tab 画布 + KPI 首屏可见 | SDIS-06 · PAT-06 |
| 3 | 宽度利用 | 主内容区 ≥80%，无大面积空白 | SDIS-06 · RESP-06 |
| 4 | 中文文案 | 指标、筛选、导出按钮使用中文 mock | SDIS-06 · COPY-06 |
| 5 | example runtime | BI 场景 section + `scenario-bi-domain.png` 全过 | SDIS-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 切换 Data Screen tab → 对照 `scenario-bi-domain.png`。

## SDIS-07 — DevOps 独立截图矩阵

**对照 golden**：`scenario-devops-domain.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 独立截图 | `scenario-devops-domain.png` framing 正常 | SDIS-07 · REV-07 |
| 2 | 流水线阶段 | PipelineStageBar 6 阶段等宽首屏可见 | SDIS-07 · PAT-07 |
| 3 | 日志流 | LogStreamPanel 固定高度，等宽字体可读 | SDIS-07 · VIS-07 |
| 4 | 中文文案 | 阶段、审批、制品表使用中文 mock | SDIS-07 · COPY-07 |
| 5 | example runtime | DevOps 场景 section + `scenario-devops-domain.png` 全过 | SDIS-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 检查 PipelineStageBar + LogStreamPanel framing → 对照 `scenario-devops-domain.png`。

## SDIS-08 — Gateway 独立截图矩阵

**对照 golden**：`scenario-gateway-domain.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 独立截图 | `scenario-gateway-domain.png` framing 正常 | SDIS-08 · REV-08 |
| 2 | 部署矩阵 | DeploymentModeMatrix 4 模式首屏可见 | SDIS-08 · PAT-08 |
| 3 | KPI 栅格 | 4 列网关 KPI 与 EndpointProbeTable 对齐 | SDIS-08 · RESP-08 |
| 4 | 中文文案 | 节点、许可、密钥文案使用中文 mock | SDIS-08 · COPY-08 |
| 5 | example runtime | Gateway 场景 section + `scenario-gateway-domain.png` 全过 | SDIS-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 检查 DeploymentModeMatrix framing → 对照 `scenario-gateway-domain.png`。

## SDIS-09 — Governance 独立截图矩阵

**对照 golden**：`scenario-governance-domain.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 独立截图 | `scenario-governance-domain.png` framing 正常 | SDIS-09 · REV-09 |
| 2 | 权限矩阵 | PermissionMatrix 行列对齐首屏可见 | SDIS-09 · PAT-09 |
| 3 | 审计日志 | AuditLogTable 时间/操作/结果列密度一致 | SDIS-09 · VIS-09 |
| 4 | 中文文案 | 权限、审计、合规文案使用中文 mock | SDIS-09 · COPY-09 |
| 5 | example runtime | Governance 场景 section + `scenario-governance-domain.png` 全过 | SDIS-09 · PREVIEW-* |

**交互动作**：打开治理场景 → 检查 PermissionMatrix framing → 对照 `scenario-governance-domain.png`。

## SDIS-10 — 场景域独立截图束

**对照 golden**：`scenario-*-domain.png`（5 张）、`verifyScenarioDomainScreenshots`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 五域截图 | 5 张 `scenario-*-domain.png` 均存在且 framing 正常 | SDIS-10 · VAL-* |
| 2 | data-audit | 各域 section 有 `data-audit="scenario-*"` 或 `tailadmin-bi-analytics` | SDIS-10 · COV-10 |
| 3 | 画布可见 | 各域 `.scenario-domain-layout` 或 `.bi-analytics-layout` 画布可见 | SDIS-10 · INTER-10 |
| 4 | audit 静态 | `audit` 含 `verifyScenarioDomainScreenshots` marker | SDIS-10 · COV-10 |
| 5 | 与 SPVR 串联 | 独立截图与 SPVR 五门禁同轮可访问 | SDIS-10 · PREVIEW-* |

**交互动作**：跑 `npm run verify:runtime` → 确认 `scenarioDomainScreenshotStates.domainCount = 5` → 对照五张独立截图。

## 交叉引用

- `scenario-domain-independent-screenshot-review-checklist.md` — SDIS-01～05
- `scene-scenario-page-visual-regression-review-checklist.md` — SPVR-06～10
- `scene-ui-drift-review-checklist.md` — REV-06～10
- `business-validation-checklist.md` — VAL-* 场景冒烟
- `decision-matrix.md` — G93 场景域独立截图选型表
- `upgrade-troubleshooting.md` — SDIS-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域独立截图检索路径
- `quality-rubric.md` — 综合美学维度
