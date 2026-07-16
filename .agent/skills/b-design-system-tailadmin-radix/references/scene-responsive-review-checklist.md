# 场景响应式评审清单

> DOCS-027 / G76 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级响应式抽检**，覆盖 BI 大屏筛选与图表窄屏布局、DevOps 流水线阶段与日志密度、Gateway 探测表格与配额卡片、PaaS 危险操作与 ConfigDiff 及 MS 场景响应式束，并与 `responsive-review-checklist.md`（RESP-01～05）、`state-index.md`、`golden-screens.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景响应式抽检 | 对应 RESP 块 + `quality-rubric.md` 截图红线 |
| 大规模 Agent 生成后 MS 场景抽检 | RESP-01～05（控件/页面级）+ RESP-06～10（场景级）各抽 1 页 |
| BI 筛选 chip 在窄屏挤压图表或 KPI 仍 4 列 | 先跑 RESP-06，再查 `layout-patterns/bi-filter-linkage.md` |
| CI/CD 阶段条在 mobile 溢出或日志不可读 | RESP-07 + `templates/devops/pipeline-stage-bar.tsx` |
| Gateway 探测表格撑破壳层或配额卡片贴边 | RESP-08 + MS-09 `EndpointProbeTable` |
| PaaS ResourceTable 行操作重叠或地图块压扁 | RESP-09 + `templates/paas/resource-table.tsx` |
| MS 场景组合在 tablet/mobile framing 错位 | RESP-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `responsive-review-checklist.md` RESP-01～05（壳层、KPI 栅格、表单浮层、表格、BI 画布页面级抽检）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
3. 抽检视口 **desktop 1440×1000**、**tablet 1024×768**、**mobile 390×844**；**light + dark** 各至少 1 次壳层检查。
4. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
5. 固定格式 UI（KPI 栅格、阶段条、筛选 chips、表格工具栏、大屏画布）必须按容器宽度响应式展开，禁止 desktop 布局直搬 mobile。

## RESP-06 — BI / Data Screen 筛选与图表响应式

**对照 reference**：`layout-patterns/bi-filter-linkage.md`、`templates/bi/cross-filter-dashboard.tsx`、`templates/bi/filter-bar.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | FilterBar 窄屏 | chips 在 tablet/mobile 可换行或横向滚动，不挤压 ChartPanel | RESP-06 · MS-11 |
| 2 | KPI 栅格 | desktop 4 列；tablet **2×2**；mobile 1 列；数字不裁切 | RESP-02 · VIS-06 |
| 3 | 图表高度 | ChartPanel 在 tablet/mobile 有最小高度，不压成细条 | RESP-05 · extension-audit.md |
| 4 | cross-filter 并排 | `< lg` 筛选与图表纵向堆叠，主次顺序可读 | RESP-06 · INTER-06 |
| 5 | 大屏画布 | Data Screen 按 16:9 或设计比例缩放，非空容器占位 | RESP-05 · VIS-06 |

**交互动作**：在 **1024px** 检查 FilterBar 换行与 KPI 2×2 → 在 **390px** 检查图表最小高度与首屏信息层次 → 切换 light/dark → 对照 `bi-chart-state-gates.png`、`layout-variants-mobile-layer.png`。

## RESP-07 — DevOps 流水线阶段与日志响应式

**对照 golden**：`cicd-run-detail`、`pipeline-stage-bar`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段条窄屏 | PipelineStageBar 在 mobile 可横向滚动或折行，active 态可读 | RESP-07 · MS-10 |
| 2 | LogStream 密度 | 日志区在窄屏保持等宽密度；长行可横向滚动不撑破壳层 | RESP-07 · VIS-07 |
| 3 | 制品/审批并排 | `< lg` 制品表与审批时间线纵向堆叠，不挤压到不可读 | RESP-04 · MS-10 |
| 4 | Rollback Dialog | mobile 居中 Dialog 留边距；危险操作按钮 touch target ≥ 40px | RESP-03 · LOGIC-02 |
| 5 | Danger Zone | 危险区块在窄屏与主内容区分隔清晰，按钮不重叠 | RESP-07 · VIS-07 |

**交互动作**：在 **1024px** 检查阶段条与日志并排 → 在 **390px** 打开 Rollback Dialog → 检查 LogStream 横向滚动与 Danger Zone 间距。

## RESP-08 — Gateway 端点探测与配额响应式

**对照 golden**：`gateway-patterns`、`control-plane-hub`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Probe 表格 | EndpointProbeTable 列多在容器内 `overflow-x-auto`，关键列 sticky | RESP-08 · MS-09 |
| 2 | 配额卡片 | BalanceQuota 在 tablet 2 列 / mobile 1 列；进度条不贴边 | RESP-02 · VIS-08 |
| 3 | 探测 Dialog | mobile Dialog 不贴屏；分步结果 badge 可换行 | RESP-03 · A11Y-08 |
| 4 | 顶栏操作 | tablet/mobile 顶栏双行或压缩操作区，主探测按钮仍可达 | RESP-01 · MS-09 |
| 5 | License 状态 | 状态 badge 在窄屏不裁切；表格行操作 touch target 足够 | RESP-04 · INTER-08 |

**交互动作**：在 **390px** 横向滚动 EndpointProbeTable → 打开探测 Dialog → 检查 BalanceQuota 栅格 → 对照 `gateway-patterns` golden。

## RESP-09 — PaaS 危险操作与 ConfigDiff 响应式

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | ResourceTable | 列多时在容器内横向滚动；名称/状态列 sticky 或优先可见 | RESP-09 · MS-12 |
| 2 | Capacity 栅格 | CapacityCard 在 tablet 2×2 / mobile 1 列；数字 tabular-nums 不裁切 | RESP-02 · VIS-09 |
| 3 | ConfigDiff | diff 区块在窄屏可纵向滚动；变更行高亮不溢出 | RESP-09 · INTER-09 |
| 4 | 地图块 | 地图/拓扑在 mobile 仍可读高度，或提供列表降级 | RESP-05 · MS-12 |
| 5 | 危险 Dialog | 恢复/伸缩 Dialog mobile 留边距；确认按钮不贴底 | RESP-03 · ASYNC-09 |

**交互动作**：在 **390px** 滚动 ResourceTable → 打开恢复 Dialog → 展开 ConfigDiff → 检查 Capacity 栅格 → 对照 `complex-form-drawer-guard.png` 同类 framing。

## RESP-10 — MS 场景响应式束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：探测表横向滚动 + 配额卡片栅格 + mobile Dialog 边距 | SOR-05 · RESP-08 |
| 2 | MS-10 | CI/CD：阶段条窄屏可达 + LogStream 密度 + 制品表不撑破壳层 | SOR-02 · RESP-07 |
| 3 | MS-11 | BI：FilterBar 换行 + KPI 2×2 + ChartPanel 最小高度 | SOR-01 · RESP-06 |
| 4 | MS-12 | PaaS：ResourceTable sticky + Capacity 栅格 + 地图可读高度 | SOR-03 · RESP-09 |
| 5 | MS-13 | 治理：PermissionMatrix 窄屏可滚动 + Wizard 步骤指示不溢出 | SOR-04 · RESP-03 |

**交互动作**：按 MS 表各抽 1 个场景页 → 在 **1024px** 与 **390px** 双视口抽检 → 对照 decision-matrix **场景响应式（G76）** 选型表 → 确认 RESP-01～10 在场景内组合满足。

## 五类场景响应式速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | 筛选挤压图表、KPI 仍 4 列、大屏假占位 | `bi-filter-linkage.md` | RESP-06 · DRIFT-01 |
| DevOps | 阶段条溢出、日志撑破、制品与审批同屏挤压 | `devops-template.md` | RESP-07 · VAL-02 |
| Gateway | 探测表撑破、配额卡片贴边 | `gateway-template.md` | RESP-08 · VAL-01 |
| PaaS | 表格行操作重叠、地图压扁、ConfigDiff 溢出 | `paas-template.md` | RESP-09 · MS-12 |
| MS 束 | 领域页 tablet/mobile framing 反模式 | `business-validation-checklist.md` | RESP-10 · MFE-04 |

## 完整响应式评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `responsive-review-checklist.md` | RESP-01～05 |
| 场景级 | 本文件 | RESP-06～10 |

完整响应式评审 = **RESP-01～10**；PR 前至少抽检 RESP-01 + RESP-06 + 1 个 MS RESP-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
# 业务仓库：Playwright / 真机截图
pnpm exec playwright test --grep scene-responsive
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的 tablet KPI 仍 4 列、mobile Dialog 贴边或表格撑破壳层。
- MS 场景组合在窄屏出现 framing 反模式（如双 AppLayout、Master-Detail 同屏挤压）。
- 检索路径超过 3 跳才找到本清单或对应 RESP 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 RESP-06（BI 场景）～ RESP-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 断点与侧栏行为 | `state-index.md` |
| 壳层与门户模板 | `layout-patterns/app-shell.md` |
| 组件/页面正选 | `decision-matrix.md` |
| 场景可访问性 | `scene-accessibility-review-checklist.md` |
| 场景视觉 Token | `scene-visual-token-review-checklist.md` |
| 场景交互与动效 | `scene-interaction-review-checklist.md` |
| UI 漂移评审 | `ui-drift-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| SSR / 微前端嵌入 | `ssr-microfrontend-adoption-checklist.md#mfe-04` |
| 症状与回滚 | `upgrade-troubleshooting.md` RESP-* / DRIFT-* / VIS-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
