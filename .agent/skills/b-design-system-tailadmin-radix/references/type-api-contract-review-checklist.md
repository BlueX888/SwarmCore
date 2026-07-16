# 类型完整与 API 契约评审清单

> DOCS-017 / G66 产物。对 Agent 生成或人工改写的业务页面执行**可复现 TypeScript 类型与公开 API 契约抽检**，覆盖 props 导出、theme helper 签名、受控组件契约、additive 变更与 MS 场景组合类型边界，并与 `api-contracts.md`、`extension-audit.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前类型抽检 | 对应 TYPE 块 + `quality-rubric.md` 类型完整 |
| 升级 Skill 快照后 `tsc` 报错 | 先跑 TYPE-04，再查 `upgrade-troubleshooting.md` TS-* |
| 复杂组件 props 对不上 | TYPE-03 + `api-contracts.md` 对应组件表 |
| theme lib override 类型丢失 | TYPE-02 + `merge-options-guide.md` |
| MS-09～13 组合页类型漂移 | TYPE-05 + `business-validation-checklist.md` |

## 通用前置

1. 对照 `references/api-contracts.md` 确认所用组件/ helper 的稳定性等级（stable / additive / evolving）。
2. 抽检至少 **1 个复杂组件页（Chart/Kanban/DataTable）+ 1 个 MS-09～13 场景组合页**。
3. 业务代码必须能通过 `tsc --noEmit`；禁止 `any` 绕过公开 props。
4. 破坏性变更必须有 `migration-notes/` 记录或 deprecated wrapper；禁止 silent rename。
5. theme helper 的 `overrides` 参数必须保持 **additive deep merge** 语义（G49）。

## TYPE-01 — Props 导出与接口完整

**对照 reference**：`api-contracts.md`、`component-index.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 导出名 | 从模板复制的组件使用文档列出的导出名；无本地 rename 再 export | TYPE-01 · TS-* |
| 2 | Props 类型 | 关键 props 有显式 interface/type；`variant`/`size` 走 `cva` 联合类型 | TYPE-01 |
| 3 | 受控/非受控 | `value`/`onChange` 或 `open`/`onOpenChange` 成对出现；非混用 | TYPE-03 |
| 4 | 回调签名 | 事件回调参数类型与数据模型一致（如 `KanbanTask`、`PermissionRow`） | TYPE-03 |
| 5 | 编译检查 | `tsc --noEmit` 无 props 缺失/多余；无 `@ts-ignore` 掩盖契约 | RUN-03 |

**交互动作**：打开 MS-12 ResourceTable 或 Form Controls 矩阵 → `tsc --noEmit` → 对照 `api-contracts.md` Gateway/Form 契约表。

## TYPE-02 — Theme lib 与 override 签名

**对照 reference**：`api-override-recipes.md`、`merge-options-guide.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Chart | `getBaseChartOptions(overrides?)` 返回 `ApexOptions`；series 深嵌套不丢失 | MER-02 · TS-04 |
| 2 | FullCalendar | `getDefaultFullCalendarOptions(overrides?)` deep merge；无参调用仍合法 | TS-05 |
| 3 | Maps/Carousel | `mergeMapLibreOptions` / `mergeSwiperOptionsDeep` 签名与文档一致 | MER-01 |
| 4 | CSS 常量 | `chartPaletteCssVars`、`kanbanBoardGridClass` 等 theme-only 导出未删改 | api-contracts |
| 5 | 类型导入 | 第三方类型（`ApexOptions`、`SwiperOptions`）从正确包导入；无手写 `any` options | TYPE-02 |

**交互动作**：MS-11 CrossFilterDashboard → 传入 `getBaseChartOptions({ series: [...] })` → 确认 TS 推断与运行时色板一致。

## TYPE-03 — 复杂组件受控契约

**对照 reference**：`extension-audit.md`、`api-contracts.md` Kanban/DataTable/Permission 表

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | KanbanBoard | `columns: KanbanColumnData[]` + `onTaskMove`/`onColumnAction` 可选但类型完整 | TS-03 · MN-03 |
| 2 | DataTableCard | `loading`/`error`/`empty`/`onRetry` 与 `prd/F02-data-state.md` 一致 | ASYNC-02 |
| 3 | PermissionMatrix | 行列 id 为 `string`；`onChange` 返回完整矩阵快照 | LOGIC-03 |
| 4 | ControlPlaneHub | 子面板 props 受控；禁止子组件内部写死 mock 且对外无类型 | SEL-05 · MS-09 |
| 5 | 降级路径 | partial 失败时 props 仍满足最小可渲染子集（见 extension-audit 降级列） | ASYNC-05 |

**交互动作**：MS-10 CicdRunDetail → 切换 `stages` 受控 prop → MS-13 PermissionMatrix `onChange` 类型与保存回调对齐。

## TYPE-04 — Additive 变更与迁移兼容

**对照 reference**：`backward-compatibility.md`、`migration-notes/`、`version-pinning-guide.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 稳定性等级 | stable 组件无删 props；evolving 仅 additive 扩展 | api-contracts |
| 2 | Deprecated | 使用 `@deprecated` wrapper 或 MN 文档指引；旧 API 仍可编译 | TS-01～03 |
| 3 | 别名导出 | `ThemeToggle` alias 等与 MN-01 一致；barrel 不破坏旧 import | MN-01 |
| 4 | Pin 记录 | `docs/design-system-pin.md` 或等效记录 commit；升级前后跑 `audit_compat_contracts.py` | ADOPT-04 · RUN-01 |
| 5 | 审计通过 | `audit_migration_drills.py` + `audit_override_recipes.py` exit 0 | RUN-02 |

**交互动作**：模拟升级 pin → 跑 `audit_compat_contracts.py` → 若有 TS-02 症状改用 `SearchCommandStatic`。

## TYPE-05 — MS 场景组合类型抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | `ControlPlaneHub` 子面板 props 类型与 `gateway-template.md` 一致 | VAL-01 · TYPE-03 |
| 2 | MS-10 | `PipelineStageBar` stage id + `LogStreamPanel` 流式 props 类型闭合 | VAL-02 |
| 3 | MS-11 | `FilterBar` chips + `CrossFilterDashboard` chart filter 类型联动 | VAL-03 |
| 4 | MS-12 | `ResourceTable` row type + Maps `center/zoom` override 类型 | VAL-04 |
| 5 | MS-13 | `AuthProviderWizard` 分步 data + `AuditLogTable` query props | VAL-05 · LOGIC-04 |

**交互动作**：按 MS 表各抽 1 个组合页 → 对照 decision-matrix **类型完整（G66）** 列 → 完成受控 props 切换无 TS 错误。

## 五类类型契约速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| Props 缺失/重命名 | `tsc` 报 property does not exist | `api-contracts.md` | TYPE-01 · TS-* |
| Override 类型丢失 | series/nested options 编译报错 | `merge-options-guide.md` | TYPE-02 · MER-* |
| 受控契约断裂 | runtime 有值但 TS 推断 `never` | `extension-audit.md` | TYPE-03 · VAL-* |
| 升级破坏性 | pin 后大面积 TS 错误 | `migration-notes/` | TYPE-04 · RUN-01 |
| MS 组合漂移 | 场景页 props 与模板默认不一致 | `business-validation-checklist.md` | TYPE-05 · SEL-* |

## 完整类型契约评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | 本文件 | TYPE-01～05 |
| 场景级 | `scene-type-api-contract-review-checklist.md` | TYPE-06～10 |

完整类型契约评审 = **TYPE-01～10**；PR 前至少抽检 TYPE-01 + TYPE-06 + 1 个 MS TYPE-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库
pnpm exec tsc --noEmit
rg -n "@ts-ignore|as any" src/
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的 props 重命名、受控契约断裂或 theme helper 签名漂移。
- MS 场景组合缺少类型化受控 props，导致业务只能硬编码 mock。
- 检索路径超过 3 跳才找到本清单或 `api-contracts.md` 对应块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 TYPE-01（props）～ TYPE-05（MS 组合）、TYPE-06～10（场景级）；与 TS-*、MER-*、RUN-01 交叉引用。

## 交叉引用

| 主题 | 文件 |
|---|---|
| 公开 API 注册表 | `api-contracts.md` |
| 扩展性降级 | `extension-audit.md` |
| 类型完整规则 | `quality-rubric.md` |
| 业务冒烟 | `business-validation-checklist.md` |
| 检索路由 | `agent-retrieval-guide.md` |
| 升级症状 | `upgrade-troubleshooting.md` |
| 选型矩阵 | `decision-matrix.md` |
