# 数据状态与异步韧性评审清单

> DOCS-012 / G61 产物。对 Agent 生成或人工改写的业务页面执行**可复现数据状态与异步韧性抽检**，覆盖 loading、empty、error、partial、retry、refetch、异步校验与第三方组件降级，并与 `state-index.md`、`prd/F02-data-state.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前数据状态抽检 | 对应 ASYNC 块 + `quality-rubric.md` 逻辑完备 |
| 大规模 Agent 生成后抽检 | ASYNC-01～05 各抽 1 页 |
| 页面长时间空白无反馈 | 先跑 ASYNC-01，再查 `state-index.md` |
| 表格刷新后数据错乱或静默失败 | ASYNC-02 + `prd/F02-data-state.md` |
| 提交后无 loading 或错误不可重试 | ASYNC-03 + `layout-patterns/form-composition.md` |

## 通用前置

1. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
2. 抽检视口 **desktop 1440×1000**，**light + dark** 各至少 1 次状态切换；异步操作补动作后截图。
3. 用户可见 loading/empty/error/retry 文案默认中文（技术缩写除外，见 `quality-rubric.md`）。
4. 复杂第三方组件必须先确认有 loading 占位与降级路径（见 `extension-audit.md`）。

## ASYNC-01 — 页面级 Query Shell / 内容区状态

**对照 reference**：`state-index.md`、`prd/F02-data-state.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 首屏 loading | 数据未就绪时显示 Skeleton/Spinner，非空白页 | ASYNC-01 |
| 2 | empty | 无数据时有标题+说明+可选 CTA，非仅「暂无数据」单行 | `state-index.md` |
| 3 | error | 失败态有原因+重试/深链，非 `console.error` 静默 | ASYNC-01 |
| 4 | partial | 局部失败时其余区块仍可读，失败区有 inline 提示 | ASYNC-04 |
| 5 | refetch | 手动刷新有 loading 反馈，完成后状态恢复 | `prd/F02-data-state.md` |

**交互动作**：模拟慢请求 → 确认 loading 可见 → 触发 error → 点击重试 → 确认恢复 success 态。

## ASYNC-02 — 表格 / 列表 / DataTableCard

**对照 golden**：`data-table-dense`、`paas-resource-table`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 表格 loading | 首载与翻页有行级或表级 Skeleton，表头结构保留 | ASYNC-02 |
| 2 | 空列表 | 空态居中+说明+创建/导入 CTA（适用时） | `decision-matrix.md#表格` |
| 3 | 筛选无结果 | 与真 empty 区分：提示「无匹配结果」+ 清除筛选 | ASYNC-02 |
| 4 | 服务端分页 | 翻页/排序时 loading 不丢选中态或页码 | `prd/F02-data-state.md` |
| 5 | 批量操作 | 批量提交有进度或禁用重复点击 | ASYNC-03 |

**交互动作**：打开 ResourceTable 或 DataTable → 触发筛选无结果 → 翻页观察 loading → 模拟 error 后点重试。

## ASYNC-03 — 表单提交 / 异步校验

**对照 reference**：`layout-patterns/form-composition.md`、`state-index.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 提交 loading | 主按钮 `disabled` + Spinner，防重复提交 | ASYNC-03 |
| 2 | 异步校验 | validating 态有 Spinner/文案；成功/失败可辨 | `templates/ui/async-field.tsx` |
| 3 | 提交错误 | 服务端错误映射到字段或顶部 Alert，中文可读 | A11Y-02 |
| 4 | 脏数据关闭 | Dialog/Drawer 关闭未保存时有确认 | `form-composition.md` |
| 5 | 危险操作 | 删除/吊销/回滚有二次确认 + 提交 loading | `decision-matrix.md#反例` |

**交互动作**：提交表单触发 validating → 模拟网络错误 → 重试成功 → 关闭未保存 Dialog 确认脏关闭。

## ASYNC-04 — 局部失败 / 重试 / 陈旧数据

**对照 reference**：`extension-audit.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 多区块页面 | KPI/图表/表格独立 loading/error，一区块失败不拖垮全页 | ASYNC-04 |
| 2 | retry | 失败区块有「重试」按钮且可恢复 | `state-index.md` |
| 3 | stale 提示 | 后台刷新后可选「数据已更新」或自动合并 | ASYNC-04 |
| 4 | 权限禁用 | 无权限操作 disabled + tooltip，非提交后 403 空白 | `decision-matrix.md` |
| 5 | MS 抽检 | MS-09～13 至少 1 页有 observable loading→success 路径 | `business-validation-checklist.md` |

**交互动作**：在 ControlPlaneHub 或 CicdRunDetail 模拟单面板失败 → 重试该面板 → 确认其余面板仍可用。

## ASYNC-05 — 第三方重组件 / 降级与懒加载

**对照 reference**：`extension-audit.md`、`ssr-microfrontend-adoption-checklist.md#ssr-02`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Chart/Maps | dynamic import + loading 占位；失败有降级文案或静态图 | ASYNC-05 |
| 2 | Kanban/Calendar | DnD/日历加载中有占位；error 不白屏 | `kanban-theme.md` |
| 3 | LogStream | 流式加载有尾部 loading 或「加载更多」 | MS-10 |
| 4 | 大屏画布 | Data Screen 区块独立 loading，非全局阻塞 | RESP-05 |
| 5 | SSR 边界 | 客户端组件有 `ssr: false` 或 dynamic 包装说明 | SSR-02 |

**交互动作**：打开含 Chart 的 BI 页 → 观察 lazy 加载占位 → 模拟地图/图表失败 → 确认降级可读。

## 五类异步状态速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 页面/Shell | 长时间空白、error 无重试 | `state-index.md` · preview | ASYNC-01 |
| 表格/列表 | 翻页丢态、筛选与空态混淆 | `prd/F02-data-state.md` | ASYNC-02 |
| 表单/提交 | 双提交、校验无反馈 | `form-composition.md` | ASYNC-03 |
| 局部/多区块 | 一错全页白、无 retry | `extension-audit.md` | ASYNC-04 |
| 重组件/降级 | Chart 白屏、地图无 title | `ssr-microfrontend-adoption-checklist.md` | ASYNC-05 · SSR-02 |

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库：模拟慢网/失败 API
pnpm exec playwright test --grep async-state
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的静默失败、无 loading 双提交或表格翻页丢态。
- MS 场景组合缺少 observable 异步路径（如端点探测无 loading、流水线无阶段状态）。
- 检索路径超过 3 跳才找到本清单或对应 ASYNC 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 ASYNC-01（页面级）～ ASYNC-05（重组件降级）；场景级 ASYNC-06～10 见 `scene-async-state-review-checklist.md`。

控件/页面级 ASYNC-01～05 完成后，对 BI/Data Screen、DevOps、Gateway、PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-async-state-review-checklist.md`（DOCS-025 / G74）。

新增 ASYNC-* 症状行写入 `upgrade-troubleshooting.md`；可复用检查项可沉淀到本文件对应 ASYNC 块。

## 检索入口

| 意图 | 读 |
|---|---|
| 状态矩阵与 Token | `state-index.md` |
| DataTable 契约 | `prd/F02-data-state.md` |
| 组件/页面正选 | `decision-matrix.md` |
| UI 漂移评审 | `ui-drift-review-checklist.md` |
| 可访问性 loading 反馈 | `accessibility-review-checklist.md#a11y-05` |
| 响应式与大屏 | `responsive-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| SSR / 微前端懒加载 | `ssr-microfrontend-adoption-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` ASYNC-* / VAL-* / RUN-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
