# 场景 Scenario Page Visual Regression 评审清单

> DOCS-043 / G92 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级视觉回归抽检**，覆盖各场景 section 的 KPI 密度、流水线 framing、控制平面 Hub、审计表格与容量卡片布局，并与 `scenario-page-visual-regression-review-checklist.md`（SPVR-01～05）、`scene-pattern-coverage-review-checklist.md`（PAT-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域抽检 | 对应 SPVR 块 + `quality-rubric.md` |
| BI Analytics 多页面工作台 | SPVR-06 + `tailadmin-bi-analytics` |
| DevOps 发布运行详情 | SPVR-07 + `scenario-devops` |
| Gateway 控制平面 | SPVR-08 + `scenario-gateway` |
| Governance 治理审计 | SPVR-09 + `scenario-governance` |
| 场景视觉回归束缺门禁 | SPVR-10 + `verify:runtime` `scenarioPageVisualRegressionStates` |

## 通用前置

1. 先完成 `scenario-page-visual-regression-review-checklist.md` SPVR-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-page-visual-regression-gates.png`。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + DevOps 或 Gateway**。
4. 视口 **desktop 1440×1000** 与 **mobile 390×844** 各 1 次首屏宽度检查。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景页面视觉回归（G92）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景页面视觉回归抽检行。

## SPVR-06 — BI Analytics 多页面工作台

**对照 golden**：`tailadmin-bi-analytics`、`bi-chart-builder-runtime.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 多页面 tab | BI source pages tab 可切换，每页独立 KPI/画布 | SPVR-06 · PAT-06 |
| 2 | Chart Builder | Builder 内 ≥10 ApexCharts runtime + 首屏宽度 ≥80% | SPVR-06 · COV-06 |
| 3 | Data Screen | fixed-ratio 大屏画布有真实 KPI/图表层次 | SPVR-06 · VIS-06 |
| 4 | 中文文案 | 指标、筛选、导出按钮使用中文 mock | SPVR-06 · COPY-06 |
| 5 | example runtime | BI 场景 section + Chart Builder 截图全过 | SPVR-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 切换 Chart Builder tab → 检查 10 runtime 图表 framing。

## SPVR-07 — DevOps 发布运行详情

**对照 golden**：`scenario-devops`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 流水线阶段 | PipelineStageBar 6 阶段等宽，当前步高亮 | SPVR-07 · PAT-07 |
| 2 | 日志流 | LogStreamPanel 固定高度，等宽字体可读 | SPVR-07 · VIS-07 |
| 3 | 审批时间线 | ApprovalTimeline 与 ArtifactTable framing 一致 | SPVR-07 · REV-07 |
| 4 | 中文文案 | 阶段、审批、制品表使用中文 mock | SPVR-07 · COPY-07 |
| 5 | example runtime | DevOps 场景 section 首屏 KPI + 流水线可见 | SPVR-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 检查 PipelineStageBar + LogStreamPanel framing。

## SPVR-08 — Gateway 控制平面

**对照 golden**：`scenario-gateway`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 部署矩阵 | DeploymentModeMatrix 4 模式可选，选中态清晰 | SPVR-08 · PAT-08 |
| 2 | KPI 栅格 | 4 列网关 KPI 与 EndpointProbeTable 对齐 | SPVR-08 · RESP-08 |
| 3 | 密钥面板 | ApiKeyRevealPanel mask/copy/rotate 按钮完整 | SPVR-08 · LOGIC-08 |
| 4 | 中文文案 | 节点、许可、密钥文案使用中文 mock | SPVR-08 · COPY-08 |
| 5 | example runtime | Gateway 场景 section 首屏 KPI + 矩阵可见 | SPVR-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 检查 DeploymentModeMatrix + EndpointProbeTable framing。

## SPVR-09 — Governance 治理审计

**对照 golden**：`scenario-governance`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 权限矩阵 | PermissionMatrix 行列对齐，角色/资源列完整 | SPVR-09 · PAT-09 |
| 2 | 审计日志 | AuditLogTable 时间/操作/结果列密度一致 | SPVR-09 · VIS-09 |
| 3 | 合规提示 | ComplianceAlert 可关闭，不永久遮挡表格 | SPVR-09 · REV-09 |
| 4 | 中文文案 | 权限、审计、合规文案使用中文 mock | SPVR-09 · COPY-09 |
| 5 | example runtime | Governance 场景 section 表格首屏可见 | SPVR-09 · PREVIEW-* |

**交互动作**：打开治理场景 → 检查 PermissionMatrix + AuditLogTable framing。

## SPVR-10 — 场景页面视觉回归束

**对照 golden**：`scenario-page-visual-regression-gates.png`、`verifyScenarioPageVisualRegressionGates`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 统一门禁 | `scenario-page-visual-regression-gates` + runtime 验证全过 | SPVR-10 · VAL-* |
| 2 | 五项交互 | 密度/流水线/Hub/表格/容量 5 门禁可切换 | SPVR-10 · INTER-10 |
| 3 | 截图证据 | `scenario-page-visual-regression-gates.png` 含五门禁态 | SPVR-10 · REV-10 |
| 4 | audit 静态 | `audit` 含 `verifyScenarioPageVisualRegressionGates` marker | SPVR-10 · COV-10 |
| 5 | 场景域串联 | visual regression gates 与 5 场景 section 同轮可访问 | SPVR-10 · PREVIEW-* |

**交互动作**：跑 `npm run verify:runtime` → 确认 `scenarioPageVisualRegressionStates` → 对照五门禁截图。

## 交叉引用

- `scenario-page-visual-regression-review-checklist.md` — SPVR-01～05
- `scene-pattern-coverage-review-checklist.md` — PAT-06～10
- `scene-ui-drift-review-checklist.md` — REV-06～10
- `business-validation-checklist.md` — VAL-* 场景冒烟
- `decision-matrix.md` — G92 场景页面视觉回归选型表
- `upgrade-troubleshooting.md` — SPVR-01～10 症状路由
- `agent-retrieval-guide.md` — 场景页面视觉回归检索路径
- `quality-rubric.md` — 模式覆盖维度
