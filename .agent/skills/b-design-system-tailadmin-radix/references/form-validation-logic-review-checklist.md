# 表单校验与逻辑完备评审清单

> DOCS-016 / G65 产物。对 Agent 生成或人工改写的业务页面执行**可复现表单校验与产品逻辑抽检**，覆盖校验触发、破坏性动作、权限门禁、向导分步与 CRUD 闭环，并与 `layout-patterns/crud-flow.md`、`layout-patterns/form-composition.md`、`state-index.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前逻辑抽检 | 对应 LOGIC 块 + `quality-rubric.md` 逻辑完备 |
| 大规模 Agent 生成后抽检 | LOGIC-01～05 各抽 1 页 |
| 表单提交无反馈或双提交 | 先跑 LOGIC-01，再查 `async-state-review-checklist.md#async-03` |
| 危险操作无确认或权限绕过 | LOGIC-02 + LOGIC-03 |
| 向导/接入页步骤混乱 | LOGIC-04 + `layout-patterns/form-composition.md` |
| 列表页缺编辑/删除/关闭确认 | LOGIC-05 + `layout-patterns/crud-flow.md` |

## 通用前置

1. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
2. 抽检至少 **1 个表单页 + 1 个 MS-09～13 场景组合页**。
3. 校验错误优先 **字段内联**（`FormMessage` / helper），禁止仅用 toast 替代必填提示。
4. 破坏性操作必须有 **可关闭确认路径**（Dialog/AlertDialog），禁止 silent delete。
5. 权限不足时按钮 **disabled + tooltip/说明**，禁止点击后才报错。

## LOGIC-01 — 表单校验触发与反馈

**对照 reference**：`layout-patterns/crud-flow.md`、`templates/ui/async-field.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 触发时机 | 必填/格式校验在 blur + submit 触发；非仅 submit 一次 | LOGIC-01 |
| 2 | 内联错误 | 错误字段 `aria-invalid` + 中文 `FormMessage`；非 toast-only | A11Y-02 · COPY-01 |
| 3 | 异步校验 | 唯一性/连通性走 `AsyncField` validating→success/error | ASYNC-03 |
| 4 | 提交防重 | 提交中按钮 disabled + Spinner；不可双提交 | ASYNC-03 |
| 5 | 成功反馈 | 保存成功有 toast 或页面跳转；失败保留表单数据 | `state-index.md` |

**交互动作**：打开 Dialog 短表单或 Form Controls 矩阵 → 清空必填项提交 → blur 触发错误 → 填写后提交观察 disabled/Spinner。

## LOGIC-02 — 破坏性动作与危险区

**对照 reference**：`decision-matrix.md#浮层`、`templates/devops/danger-zone.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 确认 Dialog | 删除/吊销/回滚/伸缩/重启前有 AlertDialog 或确认 Dialog | LOGIC-02 |
| 2 | 可行动文案 | 确认描述说明后果（中文）；destructive 按钮用 `variant="destructive"` | COPY-05 |
| 3 | 二次确认 | 高危操作（生产删除、密钥吊销）需 typed confirm 或勾选「我已知晓」 | LOGIC-02 |
| 4 | 取消路径 | Esc、取消按钮、点击 overlay（若允许）均可关闭且不回滚已填表单 | INTER-02 |
| 5 | Danger Zone | 批量破坏性操作集中在 DangerZone 区块，与主表单视觉隔离 | `devops-template.md` |

**交互动作**：打开 PaaS 恢复/伸缩 Dialog 或 DevOps Rollback → 检查标题/描述/取消/确认 → Esc 关闭。

## LOGIC-03 — 权限、只读与禁用态

**对照 reference**：`templates/governance/permission-matrix.tsx`、`decision-matrix.md#治理安全`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 按钮门禁 | 无权限时主操作 disabled + 中文 tooltip/说明 | LOGIC-03 |
| 2 | 矩阵语义 | RBAC 用 `PermissionMatrix` 行列语义；非 Switch 列表冒充 | SEL-04 · MS-13 |
| 3 | 只读查看 | 查看态用 `DescriptionList`；非 disabled 表单堆字段 | `form-composition.md` |
| 4 | 部分权限 | 行级/列级禁用可辨；不全页静默失败 | MS-13 |
| 5 | 审计联动 | 权限变更后审计表/日志可刷新或提示重新查询 | VAL-05 |

**交互动作**：MS-13 PermissionMatrix 切换角色 → 检查无权限操作 disabled → 保存后审计表刷新或提示。

## LOGIC-04 — 向导 / 分步接入逻辑

**对照 reference**：`templates/governance/auth-provider-wizard.tsx`、`layout-patterns/form-composition.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 步骤校验 | 每步局部校验通过才可下一步；非一次性提交全部 | LOGIC-04 |
| 2 | 导航规则 | 上一步保留已填数据；未完成步骤有 visual 指示 | INTER-03 |
| 3 | 测试/探测 | 接入/部署向导含连通性测试或 probe 步骤与结果态 | MS-09 · MS-13 |
| 4 | 提交 loading | 最后一步提交有 loading；失败停留当前步并展示错误 | ASYNC-03 |
| 5 | 移动适配 | mobile 长向导用 bottom Sheet 或单列；步骤指示不溢出 | RESP-03 |

**交互动作**：Auth Provider Wizard → 逐步填写 → 中间步故意留空点下一步 → 确认被拦截 → 完成 probe 步骤。

## LOGIC-05 — CRUD 闭环与脏数据关闭

**对照 reference**：`layout-patterns/crud-flow.md`、`templates/ui/form-dialog.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 创建/编辑路径 | 列表有明确「新建」「编辑」入口；编辑保留上下文（Drawer/Dialog/详情 Tab） | LOGIC-05 |
| 2 | 删除闭环 | 行删除 → 确认 → 列表刷新或 optimistic 回滚 | LOGIC-02 |
| 3 | 脏关闭确认 | Dialog/Drawer 表单 dirty 时关闭需二次确认 | `form-dialog.tsx` |
| 4 | 筛选/分页 | 表格筛选、排序、分页状态切换不丢编辑上下文（Master-Detail） | ASYNC-02 |
| 5 | MS 抽检 | MS-09～13 至少 1 页完成 LOGIC-01 + LOGIC-02 组合抽检 | `business-validation-checklist.md` |

**交互动作**：FormDialog 修改字段不保存直接关闭 → 确认 dirty 提示 → 取消关闭保留数据。

## 五类逻辑完备速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 校验反馈 | toast-only 错误、无双提交防护 | `crud-flow.md` | LOGIC-01 · ASYNC-03 |
| 危险操作 | 无确认直接删除/吊销 | `danger-zone.tsx` | LOGIC-02 · SEL-* |
| 权限门禁 | Switch 冒充 RBAC、按钮可点但 API 403 | `decision-matrix.md` | LOGIC-03 · SEL-04 |
| 向导分步 | 一步提交全部、probe 无结果态 | `form-composition.md` | LOGIC-04 · MS-09 |
| CRUD 闭环 | 无编辑入口、dirty 关闭丢数据 | `form-dialog.tsx` | LOGIC-05 · VAL-* |

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库：破坏性操作与校验模式抽检
rg -n "confirm\(|AlertDialog|danger-zone|FormMessage|aria-invalid" src/
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的无确认删除、toast-only 校验或 RBAC Switch 列表冒充。
- MS 场景组合缺少 probe/rollback/权限门禁等可观察逻辑路径。
- 检索路径超过 3 跳才找到本清单或对应 LOGIC 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 LOGIC-01（校验）～ LOGIC-05（CRUD）；产品逻辑 LOGIC-06～10 见 `logic-completeness-review-checklist.md`；与 ASYNC-03、SEL-04、VAL-* 交叉引用。

新增 LOGIC-* 症状行写入 `upgrade-troubleshooting.md`；可复用检查项可沉淀到本文件对应 LOGIC 块。

## 检索入口

| 意图 | 读 |
|---|---|
| 逻辑完备规则 | `quality-rubric.md` |
| CRUD 与校验模式 | `layout-patterns/crud-flow.md` |
| 表单形态选型 | `layout-patterns/form-composition.md` |
| 状态文案矩阵 | `state-index.md` |
| 异步提交/校验 | `async-state-review-checklist.md` |
| 组件/页面正选 | `decision-matrix.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` LOGIC-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| 产品逻辑完备（LOGIC-06～10） | `logic-completeness-review-checklist.md` |
