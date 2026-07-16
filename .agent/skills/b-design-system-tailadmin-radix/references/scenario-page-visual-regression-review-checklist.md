# Scenario Page Visual Regression 评审清单

> DOCS-043 / G92 产物。对 Agent 生成或人工改写的 **5 大业务场景页面**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现视觉回归抽检**，覆盖 KPI 密度、流水线 framing、控制平面 Hub 对齐、审计表格密度与容量卡片布局，并与 `pattern-coverage-review-checklist.md`（PAT-01～05）、`scene-pattern-coverage-review-checklist.md`（PAT-06～10）、`scene-ui-drift-review-checklist.md`（REV-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景页面视觉抽检 | 对应 SPVR 块 + `quality-rubric.md` 模式覆盖 |
| BI 仪表盘 KPI/图表密度抽检 | SPVR-01 + `bi-chart-builder-runtime.png` |
| DevOps 流水线/日志 framing 抽检 | SPVR-02 + `devops-template.md` |
| Gateway 控制平面 Hub 对齐抽检 | SPVR-03 + `gateway-template.md` |
| Governance 权限/审计表格密度抽检 | SPVR-04 + `governance-template.md` |
| PaaS 容量卡片/资源表布局抽检 | SPVR-05 + `paas-template.md` |

## 通用前置

1. 先完成 `pattern-coverage-review-checklist.md` PAT-01～02（场景 layout pattern 选型）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-page-visual-regression-gates.png`。
3. 抽检视口 **desktop 1440×1000** 与 **mobile 390×844** 各至少 1 次。
4. 场景级 5 大业务域抽检见 `scene-scenario-page-visual-regression-review-checklist.md` SPVR-06～10。
5. 组件/页面选型争议必须先读 `decision-matrix.md`，再填本清单。
6. 检索路径见 `agent-retrieval-guide.md` 场景页面视觉回归抽检行。

## SPVR-01 — BI KPI 密度与信息层次

**对照 reference**：`scenario-page-visual-regression-gates.png`、`domain-scenarios.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | KPI 栅格 | 4 列 KPI 在 desktop 展开，指标/趋势/图标完整 | SPVR-01 · PAT-01 |
| 2 | 图表区宽度 | 图表/筛选区占主内容 ≥70%，无大面积空白 | SPVR-01 · RESP-01 |
| 3 | 中文文案 | 指标、筛选 chips、按钮使用中文 mock | SPVR-01 · COPY-01 |
| 4 | data-state | `data-audit="spvr-density"` `data-state=balanced` | SPVR-01 · COV-05 |
| 5 | example runtime | `verifyScenarioPageVisualRegressionGates` density gate 全过 | SPVR-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 切换 density 门禁「模拟稀疏」→ 确认 `data-state=sparse` → 点击「恢复均衡」。

## SPVR-02 — DevOps 流水线 Framing

**对照 golden**：`devops-template.md`、`spvr-pipeline` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段条对齐 | PipelineStageBar 阶段等宽，当前步高亮清晰 | SPVR-02 · PAT-02 |
| 2 | 日志区高度 | LogStreamPanel 固定高度，loading 不贴边 | SPVR-02 · VIS-02 |
| 3 | 审批时间线 | ApprovalTimeline 与阶段条垂直对齐 | SPVR-02 · REV-02 |
| 4 | data-state | `data-audit="spvr-pipeline"` `data-state=aligned` | SPVR-02 · COV-05 |
| 5 | example runtime | pipeline gate 切换 misaligned 可复现并恢复 | SPVR-02 · PREVIEW-* |

**交互动作**：点击 pipeline 门禁「模拟错位」→ `data-state=misaligned` → 点击「恢复对齐」。

## SPVR-03 — Gateway 控制平面 Hub 对齐

**对照 golden**：`gateway-template.md`、`spvr-hub` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 子面板栅格 | DeploymentModeMatrix + ApiKeyPanel 2 列对齐 | SPVR-03 · PAT-03 |
| 2 | KPI 密度 | 4 列网关 KPI 与表格区 framing 一致 | SPVR-03 · VIS-03 |
| 3 | 探测 Dialog | EndpointProbe Dialog 不遮挡 Hub Tabs | SPVR-03 · INTER-03 |
| 4 | data-state | `data-audit="spvr-hub"` `data-state=aligned` | SPVR-03 · COV-05 |
| 5 | example runtime | hub gate 切换 crowded 可复现并恢复 | SPVR-03 · PREVIEW-* |

**交互动作**：点击 hub 门禁「模拟拥挤」→ `data-state=crowded` → 点击「恢复对齐」。

## SPVR-04 — Governance 审计表格密度

**对照 golden**：`governance-template.md`、`spvr-table` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 表格行高 | PermissionMatrix/AuditLogTable 行高一致，列对齐 | SPVR-04 · PAT-04 |
| 2 | 合规横幅 | ComplianceAlert 不永久遮挡表格首屏 | SPVR-04 · REV-04 |
| 3 | 危险操作 | SecretPanel 轮换按钮与表格 framing 不重叠 | SPVR-04 · LOGIC-04 |
| 4 | data-state | `data-audit="spvr-table"` `data-state=compact` | SPVR-04 · COV-05 |
| 5 | example runtime | table gate 切换 overflow 可复现并恢复 | SPVR-04 · PREVIEW-* |

**交互动作**：点击 table 门禁「模拟溢出」→ `data-state=overflow` → 点击「恢复紧凑」。

## SPVR-05 — PaaS 容量卡片布局

**对照 golden**：`paas-template.md`、`spvr-capacity` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 容量卡片 | CapacityCard CPU/Memory/Disk 三列对齐 | SPVR-05 · PAT-05 |
| 2 | 资源表宽度 | ResourceTable 列宽利用 ≥85%，长 ID ellipsis | SPVR-05 · RESP-05 |
| 3 | 危险 Dialog | 恢复/伸缩 Dialog 不遮挡关键列 | SPVR-05 · INTER-05 |
| 4 | data-state | `data-audit="spvr-capacity"` `data-state=balanced` | SPVR-05 · COV-05 |
| 5 | example runtime | capacity gate 切换 cramped 可复现并恢复 | SPVR-05 · PREVIEW-* |

**交互动作**：点击 capacity 门禁「模拟挤压」→ `data-state=cramped` → 点击「恢复均衡」。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | SPVR-01～05 |
| 场景/页面级 | `scene-scenario-page-visual-regression-review-checklist.md` | SPVR-06～10 |

## 交叉引用

- `pattern-coverage-review-checklist.md` — PAT-01～05
- `scene-pattern-coverage-review-checklist.md` — PAT-06～10
- `scene-ui-drift-review-checklist.md` — REV-06～10
- `decision-matrix.md` — G92 场景页面视觉回归选型表
- `upgrade-troubleshooting.md` — SPVR-01～10 症状路由
- `agent-retrieval-guide.md` — 场景页面视觉回归检索路径
- `quality-rubric.md` — 模式覆盖维度
