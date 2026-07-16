# 组件覆盖率评审清单

> DOCS-019 / G68 产物。对 Agent 生成或人工改写的业务页面执行**可复现组件覆盖率抽检**，覆盖主路径模板存在性、extension-audit 复杂组件、preview/golden 对齐、高频变体矩阵与 MS 场景组合模板，并与 `component-index.md`、`extension-audit.md`、`decision-matrix.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前组件覆盖抽检 | 对应 COV 块 + `quality-rubric.md` 组件覆盖率 |
| 新增组件后验收 | COV-01 + COV-03 + `component-index.md` 登记 |
| 复杂组件仅 CSS mock 无模板 | COV-02 + `extension-audit.md` |
| preview 缺 section 或截图不可复现 | COV-03 + `golden-screens.md` |
| Form/Buttons/Overlays 变体不足 | COV-04 + `preview-qa.md` |
| 大规模 Agent 生成后 MS 场景抽检 | COV-01～05（控件/页面级）+ COV-06～10（场景级）各抽 1 页 |

## 通用前置

1. 对照 `references/component-index.md` 确认所用组件已登记主路径模板或缺组件协议。
2. 抽检至少 **1 个原子组件 preview 页 + 1 个 MS-09～13 场景组合页**。
3. 14 项复杂组件必须对照 `extension-audit.md`；`partial` 状态不得计为完整覆盖。
4. 新增组件必须补「什么时候用 / 不什么时候用」；否则 COV-01 不通过。
5. preview 文案必须指向可复制 `templates/...` 路径；无 preview 的主路径模板组件覆盖率最高 92。

## COV-01 — 主路径组件与索引登记

**对照 reference**：`component-index.md`、`component-styles/_index.md`、`output-modes/missing-component.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 索引登记 | 所用组件在 `component-index.md` 有类别、模板路径、when/when-not | component-index |
| 2 | 可复制模板 | 主路径组件有 `templates/**/*.tsx` 或 layout pattern；非仅 preview CSS mock | extension-audit |
| 3 | 缺组件协议 | 确实缺失时有 `missing-component.md` 路径与补组件 checklist | output-modes |
| 4 | 领域模板 | DevOps/网关/PaaS/BI/治理使用 `templates/*/` 领域目录，非散落 ui 拼凑 | decision-matrix |
| 5 | 图标体系 | 语义图标先查 `icon-system.md`；preview Icons ≥60 且分类齐全 | ICON-001 |

**交互动作**：打开 `component-index.md` → 抽 3 个主路径组件 → 确认 `templates/` 路径存在且 preview 文案指向该路径。

## COV-02 — extension-audit 复杂组件可复制性

**对照 reference**：`extension-audit.md`、`api-contracts.md`、`third-party-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 14 项审计 | Chart/FullCalendar/Kanban/Maps/Vector/Editor/Carousel/DatePicker/MultiSelect/FileUpload/ThemeToggle/Command/Header Dropdown 均有模板或 theme lib | extension-audit |
| 2 | 无 partial | 审计表无 `partial` 残留；evolving 项有明确降级路径 | AUDIT-001 |
| 3 | theme helper | 复杂组件有 `templates/lib/*-theme.ts` 或 override 食谱 | api-override-recipes |
| 4 | 受控契约 | DataTable/Kanban/Chart 等关键 props 在 `api-contracts.md` 注册 | TYPE-03 |
| 5 | 降级路径 | SSR/慢网有 dynamic import + loading 占位（见 extension-audit 降级列） | ASYNC-05 |

**交互动作**：跑 `audit_override_recipes.py` → 对照 extension-audit 14/14 → 确认每项有可复制入口。

## COV-03 — preview / golden screens 与模板对齐

**对照 reference**：`docs/spec/.../shards/golden-screens.md`、`preview-qa.md`、`component-index.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 分组导航 | preview 左侧分组导航；非所有内容堆在 Dashboard 或单页 | PREVIEW-002 |
| 2 | 模板引用 | 每个主路径 preview panel 文案指向 `templates/...` 可复制路径 | component-index |
| 3 | golden 注册 | 新增/改动 frame 已登记 `golden-screens.md`；截图路径真实存在 | preview-qa |
| 4 | 打开态截图 | dropdown/dialog/drawer/popover/date-picker/multi-select 有打开态截图 | PREVIEW-001 |
| 5 | 视口覆盖 | desktop/tablet/mobile + light/dark 关键 frame 有截图记录 | RESP-01 |

**交互动作**：打开 preview → 切换 3 个主路径 panel → 对照 golden-screens 路径与模板文案一致性。

## COV-04 — 高频变体矩阵丰富度

**对照 reference**：`state-index.md`、`icon-system.md`、`prd/F08-preview-qa.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Form Controls | text～slider、required/error/loading/disabled 等 SOP 最低线变体齐全 | G42 form-controls-matrix |
| 2 | Buttons | primary/secondary/outline/destructive/loading/icon-only/size 等变体可预览 | component-styles |
| 3 | Overlays | Dialog/Drawer/Sheet/Popover/Dropdown/Command/Context Menu 有打开态与关闭路径 | INTER-02 |
| 4 | DataTable | 基础/密集/筛选/分页/空态/错误/加载等变体可交互 | DATA-001 |
| 5 | Icons / Data Screen | Icons ≥60 类别；Data Screen 至少 3 种行业大屏布局模式，非占位画布 | ICON-001 · BI-005 |

**交互动作**：Form Controls 矩阵 + Overlays 打开态 + Icons 面板 → 确认变体可交互且中文 mock。

## COV-05 — MS 场景组合模板覆盖

**对照 reference**：`scenario-override-recipes.md`、`business-validation-checklist.md`、`decision-matrix.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | `ControlPlaneHub` + `templates/gateway/*` 子面板齐全；preview gateway-patterns | SOR-05 · VAL-01 |
| 2 | MS-10 | `CicdRunDetail` 或 PipelineStageBar + LogStream + ArtifactTable `templates/devops/*` | SOR-02 · VAL-02 |
| 3 | MS-11 | `CrossFilterDashboard` + FilterBar `templates/bi/*`；preview bi-filter-linkage | SOR-01 · VAL-03 |
| 4 | MS-12 | `ResourceTable` + Maps theme `templates/paas/*`；preview paas-patterns | SOR-03 · VAL-04 |
| 5 | MS-13 | `PermissionMatrix` + `AuditLogTable` + Auth Wizard `templates/governance/*` | SOR-04 · VAL-05 |

**交互动作**：按 MS 表各抽 1 个组合页 → 对照 decision-matrix **组件覆盖率（G68）** 列 → 确认模板路径与 preview frame 一致。

## 五类组件覆盖速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 缺主路径模板 | 组件在页面使用但 component-index 无模板 | `component-index.md` | COV-01 |
| 仅 CSS mock | extension-audit 项无 `templates/` 可复制入口 | `extension-audit.md` | COV-02 |
| preview 缺口 | 主路径模板无 preview section 或截图缺失 | `golden-screens.md` | COV-03 |
| 变体不足 | Form/Buttons/Overlays 只有单一状态 | `state-index.md` | COV-04 |
| 场景模板缺 | MS 页散落 Card 无领域 `templates/*/` 组合 | `scenario-override-recipes.md` | COV-05 |
| 场景组件覆盖漂移 | BI/DevOps/Gateway/PaaS 领域页缺 `templates/*/` 或 extension-audit partial | `scene-component-coverage-review-checklist.md` | COV-06～10 · SEL-* |

## 完整组件覆盖率评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | 本文件 | COV-01～05 |
| 场景级 | `scene-component-coverage-review-checklist.md` | COV-06～10 |

完整组件覆盖率评审 = **COV-01～10**；PR 前至少抽检 COV-01 + COV-06 + 1 个 MS COV-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_decision_matrix_from_preview.py b-design-system-tailadmin-radix
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的主路径组件缺模板、preview 缺口或 extension-audit partial 未清零。
- MS 场景组合缺少领域 `templates/*/` 目录模板，导致 Agent 每次用散落 Card 拼凑。
- 高频变体矩阵（Form/Buttons/Overlays/DataTable）明显不足且影响生成质量。

症状 ID 对照：`upgrade-troubleshooting.md` 中 COV-01（索引）～ COV-05（MS 组合）、COV-06～10（场景级）；与 SEL-*、PREVIEW-*、AUDIT-001 交叉引用。

## 交叉引用

| 主题 | 文件 |
|---|---|
| 组件索引 | `component-index.md` |
| 扩展性审计 | `extension-audit.md` |
| 选型矩阵 | `decision-matrix.md` |
| 场景食谱 | `scenario-override-recipes.md` |
| 业务冒烟 | `business-validation-checklist.md` |
| 生成一致性 | `generation-consistency-review-checklist.md` |
| 场景组件覆盖 | `scene-component-coverage-review-checklist.md` |
| 升级症状 | `upgrade-troubleshooting.md` |
| Golden 对照 | `docs/spec/.../shards/golden-screens.md` |
