# 场景中文示例文案评审清单

> DOCS-029 / G78 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级中文示例文案抽检**，覆盖 BI 大屏筛选与图表 mock、DevOps 流水线阶段与日志、Gateway 端点探测与配额、PaaS 危险操作与 ConfigDiff 及 MS 场景中文文案束，并与 `chinese-copy-review-checklist.md`（COPY-01～05）、`quality-rubric.md`、`state-index.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景中文文案抽检 | 对应 COPY 块 + `quality-rubric.md` 中文示例文案规则 |
| 大规模 Agent 生成后 MS 场景抽检 | COPY-01～05（控件/页面级）+ COPY-06～10（场景级）各抽 1 页 |
| BI 筛选 chips/KPI/图表标题仍为英文 | 先跑 COPY-06，再查 `layout-patterns/bi-filter-linkage.md` |
| CI/CD 阶段名、日志、制品仍为英文 | COPY-07 + `templates/devops/pipeline-stage-bar.tsx` |
| Gateway License/端点/配额 mock 英文混杂 | COPY-08 + MS-09 `ControlPlaneHub` |
| PaaS 资源列头、备份/伸缩 Dialog 英文 | COPY-09 + `templates/paas/resource-table.tsx` |
| MS 场景组合 mock 文案与业务域不一致 | COPY-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `chinese-copy-review-checklist.md` COPY-01～05（表单、数据状态、壳层、领域 mock 控件级、浮层/a11y）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
3. 抽检视口 **desktop 1440×1000**，**light + dark** 各至少 1 次；重点检查用户可见字符串，非代码标识符。
4. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
5. 默认文案语言为**简体中文**；允许保留 API、CI/CD、K8s、SLA、P95、QPS、OAuth、LDAP 等固定技术术语。

## COPY-06 — BI / Data Screen 筛选与图表中文 mock

**对照 reference**：`layout-patterns/bi-filter-linkage.md`、`templates/bi/cross-filter-dashboard.tsx`、`templates/bi/filter-bar.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | FilterBar chips | 筛选维度、选中态、清除按钮为中文业务名，非 `Region` / `Status` | COPY-06 · MS-11 |
| 2 | KPI 指标名 | 指标标题、周期、趋势说明中文可读；P95/QPS 等可保留 | COPY-03 · VIS-06 |
| 3 | 图表标题/图例 | 图表标题、系列名、轴标签默认中文 | COPY-06 · CON-06 |
| 4 | 空态/错误态 | BI 筛选无结果、图表加载失败有中文标题+说明+重试 | COPY-02 · ASYNC-06 |
| 5 | 大屏画布 | Data Screen 区块标题、告警摘要、图例说明中文；非 `Chart Title` 占位 | COPY-06 · RESP-06 |

**交互动作**：打开 BI 筛选页 → 检查 chips/KPI/图表标题为中文 → 触发空态/错误态 → 切换 light/dark → 对照 `bi-chart-state-gates.png`。

## COPY-07 — DevOps 流水线阶段与日志中文 mock

**对照 golden**：`cicd-run-detail`、`pipeline-stage-bar`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段名 | 构建/测试/部署/审批等阶段名中文；CI/CD 缩写可保留 | COPY-07 · CON-07 |
| 2 | 日志/制品 | LogStream 摘要、制品名、审批动作中文可读 | COPY-04 · MS-10 |
| 3 | 状态 badge | 成功/失败/进行中/等待审批等状态中文映射 | COPY-02 · ASYNC-07 |
| 4 | Rollback Dialog | 回滚确认标题、影响说明、确认/取消按钮中文 | COPY-05 · LOGIC-02 |
| 5 | Danger Zone | 危险操作说明、按钮文案中文；技术术语有上下文 | COPY-07 · INTER-09 |

**交互动作**：打开 CicdRunDetail → 抽查阶段条/日志/制品 3 处 mock → 打开 Rollback Dialog → 对照 `workflow-ticket-reply.png`。

## COPY-08 — Gateway 端点探测与配额中文 mock

**对照 golden**：`gateway-patterns`、`control-plane-hub`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | License/同步 | License 状态、同步健康、端点探测结果说明中文 | COPY-08 · MS-09 |
| 2 | 探测表列头 | 端点、延迟、状态、最近探测时间等列头中文 | COPY-04 · CON-08 |
| 3 | 配额/余额 | BalanceQuota 超限/正常说明、剩余额度文案中文 | COPY-08 · ASYNC-08 |
| 4 | API Key 面板 | 生成/复制/吊销说明与按钮中文；`API Key` 术语可保留 | COPY-05 · MS-09 |
| 5 | 部署模式矩阵 | 部署模式、节点角色、许可限制说明中文可读 | COPY-08 · SOR-05 |

**交互动作**：抽查 Gateway 页 3 处 mock 字段 → 模拟配额超限 → 打开探测 Dialog → 对照 `gateway-patterns` golden。

## COPY-09 — PaaS 资源与危险操作中文 mock

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | ResourceTable | 集群/实例/备份列头、状态枚举、空态中文 | COPY-09 · CON-09 |
| 2 | CapacityCard | CPU/内存/磁盘/QPS 等指标标签中文；单位可保留 | COPY-04 · MS-12 |
| 3 | ConfigDiff | 参数名、变更说明、风险提示中文 | COPY-09 · VIS-09 |
| 4 | 危险 Dialog | 恢复/伸缩/重启确认标题、影响范围、确认按钮中文 | COPY-05 · INTER-09 |
| 5 | 备份/运维 | 备份策略、恢复点、故障转移说明中文可读 | COPY-09 · LOGIC-09 |

**交互动作**：抽查 PaaS 资源表列头 → 打开恢复/伸缩 Dialog → 展开 ConfigDiff 检查中文 mock → 对照 `paas-restore-dialog-open` golden。

## COPY-10 — MS 场景中文文案束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：License/端点/配额/探测 Dialog mock 中文 + 危险操作说明可读 | SOR-05 · COPY-08 |
| 2 | MS-10 | CI/CD：阶段/日志/制品/回滚 Dialog 中文；CI/CD 缩写可保留 | SOR-02 · COPY-07 |
| 3 | MS-11 | BI：筛选 chips/KPI/图表标题/空态错误态中文 | SOR-01 · COPY-06 |
| 4 | MS-12 | PaaS：ResourceTable 列头/危险 Dialog/ConfigDiff 中文 | SOR-03 · COPY-09 |
| 5 | MS-13 | 治理：PermissionMatrix/Auth Wizard/审计表 mock 中文 + aria-label 可读 | SOR-04 · COPY-05 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景中文文案（G78）** 选型表 → 确认 COPY-01～10 在场景内组合满足。

## 五类场景中文文案速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | 筛选/KPI/图表标题英文、空态 `No data` | `bi-filter-linkage.md` | COPY-06 · VAL-03 |
| DevOps | 阶段/日志/制品英文、Rollback `Confirm` | `devops-template.md` | COPY-07 · VAL-02 |
| Gateway | License/端点/配额 mock 英文 | `gateway-template.md` | COPY-08 · VAL-01 |
| PaaS | 资源列头/危险 Dialog/ConfigDiff 英文 | `paas-template.md` | COPY-09 · MS-12 |
| MS 束 | 领域页 mock 文案与业务域不一致 | `business-validation-checklist.md` | COPY-10 · DRIFT-04 |

## 完整中文文案评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `chinese-copy-review-checklist.md` | COPY-01～05 |
| 场景级 | 本文件 | COPY-06～10 |

完整中文文案评审 = **COPY-01～10**；PR 前至少抽检 COPY-01 + COPY-06 + 1 个 MS COPY-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
# 业务仓库：grep 用户可见英文 mock 或 Playwright 文案抽检
rg -n "placeholder=\"[A-Za-z]|No data|Loading\.\.\.|Something went wrong" src/
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的场景级英文 mock、英文空态或英文 Dialog 按钮无 props/`locale` 覆盖。
- MS 场景组合 mock 文案与目标业务域不一致（如网关页用英文 SaaS 电商文案）。
- 检索路径超过 3 跳才找到本清单或对应 COPY 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 COPY-06（BI 场景）～ COPY-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 中文规则与封顶 | `quality-rubric.md` |
| 状态文案矩阵 | `state-index.md` |
| 控件/页面级文案 | `chinese-copy-review-checklist.md` |
| 组件/页面正选 | `decision-matrix.md` |
| UI 漂移评审 | `ui-drift-review-checklist.md` |
| 可访问性可读标签 | `accessibility-review-checklist.md` |
| 场景约束遵守 | `scene-constraint-compliance-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` COPY-* / DRIFT-04 |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
