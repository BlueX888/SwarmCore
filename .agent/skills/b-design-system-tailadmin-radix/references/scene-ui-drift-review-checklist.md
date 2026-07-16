# 场景 UI 漂移评审清单

> DOCS-034 / G83 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级 UI 漂移抽检**，覆盖 BI 大屏筛选与图表视觉一致性、DevOps 流水线阶段与日志区 framing、Gateway 控制平面 Hub 子面板密度、PaaS 资源与危险操作 Dialog 层级及 MS 场景漂移束，并与 `ui-drift-review-checklist.md`（REV-01～05）、`agent-failure-patterns.md`（FAIL-01～10）、`quality-rubric.md` 截图红线、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景 UI 漂移抽检 | 对应 REV 块 + `quality-rubric.md` 截图红线 |
| 大规模 Agent 生成后 MS 场景抽检 | REV-01～05（控件/页面级）+ REV-06～10（场景级）各抽 1 页 |
| BI 场景 KPI/Chart 与 golden 密度不一致 | 先跑 REV-06，再查 `visual-token-review-checklist.md#vis-05` |
| CI/CD 页阶段条/日志区 framing 错位或裁切 | REV-07 + `interaction-motion-review-checklist.md#inter-05` |
| Gateway Hub 子面板 hex 硬编码或侧栏遮挡 | REV-08 + `decision-matrix.md#场景-ui-漂移选型g83` |
| PaaS 恢复/伸缩 Dialog 遮挡表格或 Maps 层级错乱 | REV-09 + `quality-rubric.md` 浮层红线 |
| MS 场景组合与 example runtime golden 明显不一致 | REV-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `ui-drift-review-checklist.md` REV-01～05（仪表盘/表单/列表/壳层/BI 页面级漂移）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
3. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**；视口 **desktop 1440×1000**，**light + dark** 各 1 张。
4. 用户可见文案默认中文（技术缩写除外，见 `quality-rubric.md`）。
5. 组件/页面选型争议必须先读 `decision-matrix.md`，再填本清单；Agent 常见失败对照 `agent-failure-patterns.md` FAIL-01～10。

## REV-06 — BI / Data Screen 场景 UI 漂移覆盖

**对照 golden**：`bi-filter-linkage`、`bi-chart-state-gates.png`、`data-screen-canvas`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | KPI/Chart 密度 | BI 场景 KPI 带与 Chart 区密度与 golden 一致；无首屏大面积空白 | REV-06 · DRIFT-01 |
| 2 | 色板一致 | 各图表使用 `getBaseChartOptions` + `chartPaletteCssVars`；dark 对比度可读 | REV-06 · DRIFT-01 · MER-02 |
| 3 | 筛选 chips 视觉 | FilterBar chips 增删不撑破布局；清除 chip 后图表区 framing 稳定 | REV-06 · DRIFT-02 |
| 4 | 大屏信息层次 | Data Screen 有 KPI 带、主图区、明细区；非空容器假柱状条 | REV-06 · DRIFT-05 |
| 5 | example runtime | BI 场景有打开态截图；`bi-chart-state-gates.png` 可复现 legend/tooltip 层级 | REV-06 · PREVIEW-* |

**交互动作**：打开 BI 筛选页 → 切换 light/dark → 添加/清除筛选 chip → 对照 `bi-chart-state-gates.png` → 检查 Chart tooltip 不遮挡后续 KPI。

## REV-07 — DevOps 流水线阶段与日志场景 UI 漂移覆盖

**对照 golden**：`cicd-run-detail`、`workflow-ticket-reply.png`、`pipeline-stage-bar`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段条 framing | PipelineStageBar 圆点/轨道对齐；active 阶段高亮不裁切标签 | REV-07 · DRIFT-05 |
| 2 | 日志区密度 | LogStream 固定高度 + 长行横向滚动；loading 动画不贴边溢出 | REV-07 · DRIFT-02 |
| 3 | 制品/审批区块 | ArtifactTable 数字列 tabular-nums；行操作 Dropdown 不遮挡阶段条 | REV-07 · DRIFT-01 |
| 4 | 危险 Dialog 层级 | Rollback/Approve 确认 Dialog 居中且可关闭；destructive 按钮语义色正确 | REV-07 · DRIFT-03 |
| 5 | example runtime | DevOps 场景 `workflow-ticket-reply.png` 可复现；阶段切换后 framing 稳定 | REV-07 · PREVIEW-* |

**交互动作**：打开 CicdRunDetail → 切换阶段 → 展开 LogStream loading → 打开危险操作 Dialog（取消）→ 对照 `workflow-ticket-reply.png`。

## REV-08 — Gateway 控制平面 Hub 场景 UI 漂移覆盖

**对照 golden**：`gateway-patterns`、`control-plane-hub`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Hub 子面板密度 | ControlPlaneHub 子面板 KPI/表格密度与 golden 一致；无 hex 硬编码 | REV-08 · DRIFT-01 |
| 2 | 探测 Dialog 层级 | EndpointProbe Dialog 打开态不遮挡 Hub Tabs；关闭路径可辨 | REV-08 · DRIFT-02 |
| 3 | 部署/License 视觉 | DeploymentModeMatrix 选中态与 KPI 同步；License 面板 mask 默认关闭 | REV-08 · DRIFT-03 |
| 4 | 图标语义 | 网关 KPI/操作图标来自 `icon-system.md`；非随机 lucide 替换 TailAdmin 语义图标 | REV-08 · DRIFT-03 |
| 5 | example runtime | Gateway 场景 golden `gateway-patterns` 可复现；light/dark 对比度可读 | REV-08 · PREVIEW-* |

**交互动作**：抽查 Gateway 页 3 个子面板 → 触发端点探测 → 打开 API Key 揭示面板 → 切换 light/dark → 对照 `gateway-patterns` golden。

## REV-09 — PaaS 资源与危险操作场景 UI 漂移覆盖

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 表格/地图 framing | ResourceTable 与 Maps Card 同一页面 framing 稳定；mobile 地图可降级 | REV-09 · DRIFT-05 |
| 2 | ConfigDiff 视觉 | ConfigDiff before/after 字段对齐；风险提示 destructive 色语义正确 | REV-09 · DRIFT-01 |
| 3 | 恢复/伸缩 Dialog | 打开态不遮挡表格关键列；确认/取消按钮不被裁切 | REV-09 · DRIFT-02 |
| 4 | 容量 KPI 对齐 | CapacityCard 数字/KPI 右对齐或 tabular-nums；无文本溢出 | REV-09 · DRIFT-01 |
| 5 | example runtime | `paas-restore-dialog-open` / `paas-scale-dialog-open` 可复现 | REV-09 · PREVIEW-* |

**交互动作**：ResourceTable 筛选 → 打开恢复 Dialog → 展开 ConfigDiff → 对照 `paas-restore-dialog-open` golden → 检查 Dialog 不遮挡行操作区。

## REV-10 — MS 场景 UI 漂移束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`agent-failure-patterns.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：ControlPlaneHub 子面板视觉与 `gateway-patterns` golden 一致；探测 Dialog 层级正常 | SOR-05 · REV-08 |
| 2 | MS-10 | CI/CD：阶段条/日志/制品区 framing 与 `workflow-ticket-reply.png` 一致 | SOR-02 · REV-07 |
| 3 | MS-11 | BI 联动：FilterBar + Chart 联动视觉与 `bi-chart-state-gates.png` 一致 | SOR-01 · REV-06 |
| 4 | MS-12 | PaaS 资源：ResourceTable + Maps + 危险 Dialog 与 paas golden 一致 | SOR-03 · REV-09 |
| 5 | MS-13 | 治理安全：PermissionMatrix + AuditLogTable + Auth Wizard 中文 mock 与 security-governance golden 一致 | SOR-04 · REV-03 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景 UI 漂移（G83）** 选型表 → 确认 REV-01～10 在场景内 UI 漂移满足 → `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` exit 0。

## 五类场景 UI 漂移速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | KPI 密度突变、Chart 色板不一致、大屏占位画布 | `bi-filter-linkage` golden | REV-06 · DRIFT-01 |
| DevOps | 阶段条错位、日志 loading 贴边、危险 Dialog 层级错乱 | `cicd-run-detail` golden | REV-07 · DRIFT-05 |
| Gateway | Hub 子面板 hex 硬编码、探测 Dialog 遮挡 Tabs | `gateway-template.md` | REV-08 · DRIFT-03 |
| PaaS | 恢复 Dialog 遮挡表格、Maps/表格 framing 不一致 | `paas-patterns` golden | REV-09 · DRIFT-02 |
| MS 束 | 领域页与 example runtime golden 明显不一致 | `business-validation-checklist.md` | REV-10 · VAL-* |

## 完整 UI 漂移评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `ui-drift-review-checklist.md` | REV-01～05 |
| 场景级 | 本文件 | REV-06～10 |

完整 UI 漂移评审 = **REV-01～10**；PR 前至少抽检 REV-01 + REV-06 + 1 个 MS REV-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
pnpm exec tsc --noEmit
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的场景级视觉/交互/语义/工程漂移（非一次性笔误）。
- MS 场景组合与 example runtime golden 差异根因为 Skill 规则缺口。
- 检索路径超过 3 跳才找到本清单或对应 REV 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 REV-06（BI 场景）～ REV-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 评审规程与封顶规则 | `quality-rubric.md` |
| 控件/页面级漂移 | `ui-drift-review-checklist.md` |
| Agent 常见失败 | `agent-failure-patterns.md` |
| 组件/页面正选 | `decision-matrix.md` |
| Golden 对照 | `docs/spec/.../shards/golden-screens.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 视觉 Token | `visual-token-review-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` REV-* / DRIFT-* / VAL-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
