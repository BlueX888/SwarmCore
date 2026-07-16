# 业务部署验证清单

> DOCS-006 / G55 产物。业务仓库接入或升级 Skill 快照后，对 MS-09～13 预防性场景组合执行**可复现冒烟验证**，确认受控 props、选型与降级路径在真实页面中成立，而非仅依赖 Skill 内部 mock。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| 首次接入 `ControlPlaneHub` / `CicdRunDetail` / `CrossFilterDashboard` / PaaS 地图组合 / 治理控制台 | 对应 MS 验证块 |
| Skill 快照 pin 升级后 | MS-09～13 全量 + `migration-playbook.md` 升级检查清单 |
| 选型争议或 preview 与业务页不一致 | 先查 `decision-matrix.md`，再跑本清单 |
| 故障排查 SEL-* 已修复 | 对应 MS 块勾选后截图归档 |

## 通用前置

1. 业务侧 `tsc --noEmit` 通过。
2. `python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix` 通过（若 vendored Skill）。
3. 关键页面 **light + dark** 各 1 张截图，视口 desktop 1440×1000。
4. 所有用户可见文案为中文（技术缩写除外，见 `quality-rubric.md`）。

## MS-09 — 企业网关控制平面

**正选**：`ControlPlaneHub` + 子面板受控 props（SOR-05）

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 部署模式矩阵 | `deploymentMode` / `onDeploymentModeChange` 受控；切换后 KPI 与矩阵状态一致 | `decision-matrix.md` MS-09；SEL-05 |
| 2 | License / 同步健康 | `showSync`、同步状态 props 来自业务 API，非写死「正常」 | SOR-05 食谱 |
| 3 | 端点探测 | `onProbe` 触发后表格 loading → 成功/失败态可辨 | `upgrade-troubleshooting.md` VAL-01 |
| 4 | API Key 揭示 | 揭示/复制/轮换走受控回调，mask 默认关闭 | `api-contracts.md` Gateway |
| 5 | 降级路径 | 可拆为 `DeploymentModeMatrix` + `EndpointProbeTable` 独立使用 | `migration-scenarios.md#ms-09` |

**交互动作**：切换部署模式 → 触发一次端点探测 → 打开 API Key 揭示面板。

## MS-10 — DevOps CI/CD 运行详情

**正选**：`CicdRunDetail` 或 `PipelineStageBar` + `ArtifactTable`（SOR-02）

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 流水线阶段 | `stages` 受控传入；当前阶段高亮与日志区联动 | SEL-02 |
| 2 | 日志流 | `logs` 追加/滚动不撑破布局；长行可横向滚动 | `decision-matrix.md` MS-10 |
| 3 | 产物表 | `artifacts` 下载/预览回调可触发 | SOR-02 |
| 4 | 危险操作 | `onDangerAction` / `onRetry` 有确认 Dialog，非直接执行 | `api-contracts.md` DevOps |
| 5 | 误选检测 | 页面**未**使用纯 `KanbanBoard` 冒充发布看板 | SEL-02 |

**交互动作**：点击阶段切换 → 展开日志 → 打开危险操作确认 Dialog（取消即可）。

## MS-11 — BI 联动仪表盘

**正选**：`CrossFilterDashboard` + `FilterBar` chips（SOR-01）

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 筛选 chips | `filters` / `onFilterChange` 受控；清除 chip 恢复图表 | SEL-01 |
| 2 | 图表联动 | 筛选后至少 2 个图表系列颜色/数值同步变化 | SOR-01 |
| 3 | 色板一致 | 各图表使用 `getBaseChartOptions` + 共享 `chartPaletteCssVars` | MER-02 |
| 4 | 下钻入口 | `onDrillDown` 可打开明细或 `DrillDownDashboard` | `decision-matrix.md` MS-11 |
| 5 | 误选检测 | 单图页面**未**误接 `CrossFilterDashboard` | SEL-01 |

**交互动作**：添加筛选 chip → 观察两图联动 → 清除 chip。

## MS-12 — PaaS 资源监控地图热力

**正选**：`ResourceTable` + Maps/Vector 同一地理语义（SOR-03）

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 地区列与地图 | 表格地区筛选与 `mapCenter` / `mapZoom` 同一数据中心语义 | SEL-03 |
| 2 | 地图点击回写 | `onMapRegionSelect` 同步表格 `regionFilter` | SOR-03 |
| 3 | Vector 热力 | 热力层与表格行数量级一致（非假柱状占位） | `quality-rubric.md` 截图红线 |
| 4 | 降级路径 | 可去掉地图 Card，仅保留 `ResourceTable` 地区列 | `migration-scenarios.md#ms-12` |
| 5 | 误选检测 | **未**在扁平表上硬塞无地理语义的地图 Card | SEL-03 |

**交互动作**：表格按地区筛选 → 地图视口跟随 → 点击地图区域回写表格。

## MS-13 — 治理安全控制台

**正选**：`PermissionMatrix` + `AuditLogTable` + Auth Wizard（SOR-04）

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 权限矩阵 | `selectedRole` / `onRoleChange` 受控；批量勾选有 indeterminate | SEL-04 |
| 2 | 审计联动 | 切换角色后 `AuditLogTable` 查询条件同步 | SOR-04 |
| 3 | 认证向导 | `AuthProviderWizard` 四步可前进/后退；探测成功/失败态可辨 | `migration-scenarios.md#ms-13` |
| 4 | 密钥面板 | `SecretKeyPanel` mask/copy/rotate 走受控回调 | `api-contracts.md` Gov |
| 5 | 误选检测 | **未**用 Switch 列表冒充 RBAC 矩阵 | SEL-04 |

**交互动作**：切换角色 → 查看审计表刷新 → 打开认证向导第一步。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
# 业务仓库
pnpm exec tsc --noEmit
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 清单某项在真实业务中**无法通过**且根因为选型或 props 契约缺失。
- 发现 MS-09～13 未覆盖的新业务意图组合。
- 验证通过但检索路径超过 3 跳才找到本清单。

症状 ID 对照：`upgrade-troubleshooting.md` 中 VAL-01（MS-09 探测态）～ VAL-05（MS-13 审计联动）。

新增 VAL-* 症状行写入 `upgrade-troubleshooting.md`；可复用检查项可沉淀到本文件对应 MS 块。

## 检索入口

| 意图 | 读 |
|---|---|
| 场景 ID → 模板路径 | `migration-playbook.md` 场景路由表 |
| 场景代码与降级 | `migration-scenarios.md` |
| 选型正/反例 | `decision-matrix.md` MS-09～13 |
| 症状与回滚 | `upgrade-troubleshooting.md` VAL-* / SEL-* |
| 首次接入清单 | `adoption-onboarding-checklist.md` |
| ≤3 跳任务路由 | `agent-retrieval-guide.md` |
