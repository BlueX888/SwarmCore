# 中文示例文案评审清单

> DOCS-014 / G63 产物。对 Agent 生成或人工改写的业务页面执行**可复现中文示例文案抽检**，覆盖表单、数据状态、导航壳层、领域 mock 与浮层/无障碍可读文案，并与 `quality-rubric.md`、`state-index.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前文案抽检 | 对应 COPY 块 + `quality-rubric.md` 中文示例文案规则 |
| 大规模 Agent 生成后抽检 | COPY-01～05 各抽 1 页 |
| placeholder/helper 仍为英文 | 先跑 COPY-01，再查 `decision-matrix.md#表单` |
| 空态/错误/加载文案不可读 | COPY-02 + `state-index.md#数据状态` |
| 侧栏/顶栏/大屏标题英文混杂 | COPY-03 / COPY-04 + `ui-drift-review-checklist.md#rev-01` |

## 通用前置

1. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
2. 抽检视口 **desktop 1440×1000**，**light + dark** 各至少 1 次；重点检查用户可见字符串，非代码标识符。
3. 默认文案语言为**简体中文**；允许保留 API、CI/CD、K8s、SLA、P95、QPS、OAuth、LDAP 等固定技术术语。
4. 若业务需英文界面，必须通过 props、`locale` 或 i18n 入口显式覆盖，不得把英文 mock 当作 Skill 默认。

## COPY-01 — 表单控件与校验文案

**对照 reference**：`layout-patterns/form-composition.md`、`quality-rubric.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Label / 字段名 | 表单字段有中文标签；必填/选填标识可读 | COPY-01 |
| 2 | placeholder | 输入框 placeholder 为中文业务语义，非 `Enter text` / `Search...` | COPY-01 |
| 3 | helper / hint | 辅助说明中文完整；技术缩写有上下文 | `form-composition.md` |
| 4 | 校验错误 | error/success/warning 为中文可读句，非裸 `Invalid` / `Required` | A11Y-02 |
| 5 | 按钮文案 | 提交/取消/保存/删除等为中文动词短语 | `decision-matrix.md#表单` |

**交互动作**：打开 Form Controls 矩阵或 Dialog 短表单 → 触发必填校验 → 检查 placeholder/helper/error 均为中文。

## COPY-02 — 数据状态与异步反馈文案

**对照 reference**：`state-index.md`、`prd/F02-data-state.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | loading | 按钮/区块 loading 文案为「加载中…」「提交中…」等，非 `Loading` | ASYNC-03 |
| 2 | empty | 空态有中文标题+说明+可选 CTA，非仅 `No data` | COPY-02 |
| 3 | error / retry | 失败原因+「重试」中文可读，非 `Something went wrong` | ASYNC-01 |
| 4 | success / toast | 成功提示为中文短句，非 `Saved successfully` | COPY-02 |
| 5 | partial | 局部失败 inline 提示中文，不拖垮其余区块 | ASYNC-04 |

**交互动作**：模拟慢请求 → 触发 empty/error → 点击重试 → 确认 success toast 为中文。

## COPY-03 — 导航、壳层与页面标题

**对照 golden**：`overview-period`、`layout-patterns-tablet`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 页面标题 | h1/h2 与面包屑为中文业务名，非 `Dashboard` / `Settings` 直译堆砌 | COPY-03 |
| 2 | 侧栏/顶栏 | 菜单项、用户菜单、通知摘要中文可读 | `route-index.md` |
| 3 | Tab / Hub | Hub Tabs 标签为中文领域名（设置/配额/用量等） | `layout-patterns/hub-tabs.md` |
| 4 | 表格列头 | 数据表列名为中文字段名；状态枚举有中文映射 | COPY-04 |
| 5 | 分页/工具栏 | 「共 N 条」「每页」「导出」「筛选」等为中文 | `decision-matrix.md#表格` |

**交互动作**：切换 Overview / 设置 Hub / DataTable 面板 → 检查标题、列头、分页文案为中文。

## COPY-04 — 领域 mock 与场景页文案

**对照 golden**：`gateway-patterns`、`cicd-run-detail`、`bi-filter-linkage`、`security-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Gateway / 控制平面 | License、端点、同步、配额等 mock 字段与操作为中文 | MS-09 |
| 2 | DevOps / CI/CD | 阶段名、日志、制品、审批动作中文；可保留 CI/CD 缩写 | MS-10 |
| 3 | PaaS / 资源 | 集群、实例、备份、伸缩等中文；K8s/MySQL 等术语可保留 | MS-12 |
| 4 | BI / 大屏 | 指标名、筛选维度、图表标题中文；P95/QPS 等可保留 | MS-11 |
| 5 | 治理 / 安全 | 权限、审计、合规、密钥轮换等中文可读 | MS-13 |

**交互动作**：各打开 1 个 MS-09～13 对应 preview frame → 抽查 3 处 mock 字段与按钮文案。

## COPY-05 — 浮层、危险操作与无障碍可读文案

**对照 reference**：`decision-matrix.md#浮层`、`accessibility-review-checklist.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Dialog / Alert | 标题、描述、确认/取消按钮中文；危险操作说明可行动 | COPY-05 |
| 2 | Toast / Alert 条 | 操作结果与错误摘要中文，非 `Copied` / `Failed` | COPY-02 |
| 3 | Tooltip / Popover | 解释性文案中文；技术术语有上下文 | A11Y-04 |
| 4 | aria-label | 图标按钮 `aria-label` 中文，如「复制」「删除」「更多操作」 | A11Y-04 |
| 5 | MS 抽检 | MS-09～13 至少 1 页完成 COPY-01 + COPY-05 组合抽检 | `business-validation-checklist.md` |

**交互动作**：打开危险操作 Dialog → 检查标题/描述/按钮 → 悬停图标按钮确认 aria-label 或 Tooltip 为中文。

## 五类中文文案速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 表单 | 英文 placeholder、裸 `Required` | `form-composition.md` | COPY-01 · DRIFT-04 |
| 数据状态 | `No data`、英文 error | `state-index.md` | COPY-02 · ASYNC-01 |
| 壳层导航 | `Dashboard` 直译菜单 | `route-index.md` | COPY-03 · DRIFT-01 |
| 领域 mock | 网关/DevOps/BI 英文标题 | `decision-matrix.md` MS 表 | COPY-04 · SEL-* |
| 浮层/a11y | `OK`/`Cancel`、无中文 aria-label | `accessibility-review-checklist.md` | COPY-05 · A11Y-04 |
| 场景 mock | BI/DevOps/Gateway/PaaS 英文标题 | `scene-chinese-copy-review-checklist.md` | COPY-06～10 · SEL-* |

## 完整中文文案评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | 本文件 | COPY-01～05 |
| 场景级 | `scene-chinese-copy-review-checklist.md` | COPY-06～10 |

完整中文文案评审 = **COPY-01～10**；PR 前至少抽检 COPY-01 + COPY-06 + 1 个 MS COPY-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库：grep 用户可见英文 mock 或 Playwright 文案抽检
rg -n "placeholder=\"[A-Za-z]|No data|Loading\.\.\.|Something went wrong" src/
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的英文 placeholder、英文空态或英文 Dialog 按钮无 props 覆盖。
- MS 场景组合 mock 文案与目标业务域不一致（如网关页用英文 SaaS 电商文案）。
- 检索路径超过 3 跳才找到本清单或对应 COPY 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 COPY-01（表单）～ COPY-05（浮层/a11y）；历史 DRIFT-04 并入本清单路由。

新增 COPY-* 症状行写入 `upgrade-troubleshooting.md`；可复用检查项可沉淀到本文件对应 COPY 块。

## 检索入口

| 意图 | 读 |
|---|---|
| 中文规则与封顶 | `quality-rubric.md` |
| 状态文案矩阵 | `state-index.md` |
| 组件/页面正选 | `decision-matrix.md` |
| UI 漂移评审 | `ui-drift-review-checklist.md` |
| 可访问性可读标签 | `accessibility-review-checklist.md` |
| 异步状态文案 | `async-state-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` COPY-* / DRIFT-04 |
| 场景中文文案 | `scene-chinese-copy-review-checklist.md` |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
