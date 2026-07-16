# 约束遵守评审清单

> DOCS-021 / G70 产物。对 Agent 生成或人工改写的业务页面执行**可复现约束遵守抽检**，覆盖语义 Token、框架 API、导入规则、Skill 红线与 MS 场景工程边界，并与 `engineering-guards.md`、`token-index.md`、`quality-rubric.md`、`decision-matrix.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前约束抽检 | 对应 CON 块 + `quality-rubric.md` 约束遵守 |
| 从 0 搭建新应用或新页面 | CON-01 + CON-02 + `engineering-guards.md` |
| 迁移/重构已有 UI | CON-02 + CON-03 + `output-modes/migration.md` |
| 新增复杂组件或第三方库 | CON-02 + CON-03 + `extension-audit.md` |
| 英文 mock / 品牌硬编码 / 装饰性漂移 | CON-04 + `chinese-copy-review-checklist.md` |
| MS-09～13 场景工程边界 | CON-05 + `business-validation-checklist.md` |

## 通用前置

1. 抽检至少 **1 个通用后台页（dashboard/table-list/form-flow）+ 1 个 MS-09～13 场景组合页**。
2. 约束违规必须区分**可修复实现错误**与**需写回 Skill 规则缺口**；稳定复现的缺口写回 `decision-matrix.md` 与 PRD/plan/state。
3. 页面内 `#hex`、`rgb()`、`style={{ color }}` 默认视为 CON-01 失败；浮层非 Radix 实现视为 CON-02 失败。
4. 用户可读 mock/placeholder/helper 默认中文；无 `locale`/i18n 入口的英文默认文案视为 CON-04 失败。

## CON-01 — 语义 Token 与视觉约束

**对照 reference**：`token-index.md`、`visual-language.md`、`visual-token-review-checklist.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 语义色 | 主操作/状态/边框使用 `brand-*` / `success-*` / `error-*` 等语义 Token | VIS-01 · `token-index.md` |
| 2 | 禁止内联色 | 页面/组件无默认 `#hex`、`rgb()`、`style={{}}` 颜色 | VIS-01 · `engineering-guards.md` |
| 3 | Dark 约束 | `html.dark` + `@custom-variant dark`；dark 边框/背景层级可读 | VIS-02 |
| 4 | 密度与圆角 | 面板 `rounded-xl`、表格 `py-4`、浮层 `z-99999` 等约定一致 | VIS-03 · VIS-04 |
| 5 | 图标尺寸 | 图标 `size-4`/`size-5`/`size-6` 与相邻文本比例协调 | `icon-system.md` |

**交互动作**：抽 1 个 dashboard KPI 区 + 1 个表格页 → 检查 className 无裸色值 → light/dark 切换对比度。

## CON-02 — 框架 API 与 Radix/shadcn 约束

**对照 reference**：`engineering-guards.md`、`state-index.md`、`interaction-motion-review-checklist.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 浮层基座 | Dialog/Dropdown/Popover/Tooltip/Tabs 使用 Radix/shadcn，禁止手写 portal | CON-02 · `engineering-guards.md` |
| 2 | 类名合并 | 使用 `cn()` = clsx + tailwind-merge，禁止 `` `${a} ${b}` `` | CON-02 |
| 3 | 变体 API | Button/Badge/Alert 等使用 `cva` variants，非内联条件 class 堆叠 | CON-02 |
| 4 | 受控模式 | 表单/浮层优先受控 `open`/`value`/`onChange`；`useModal` 场景用 Dialog 受控 | TYPE-03 · `state-index.md` |
| 5 | 动效克制 | hover/focus/open 过渡 150–200ms；禁止夸张装饰动效破坏密度 | INTER-01 · INTER-02 |

**交互动作**：打开 Dialog/Drawer/Dropdown → Esc 关闭 + 焦点回焦 → 检查实现来自 `@/components/ui/*` Radix 包装。

## CON-03 — 导入规则与工程边界

**对照 reference**：`engineering-guards.md`、`extension-audit.md`、`ssr-microfrontend-adoption-checklist.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 路径别名 | 组件从 `@/components/ui/*`、`@/lib/utils` 导入，无深层相对路径穿透 | CON-03 · `engineering-guards.md` |
| 2 | Client 边界 | Chart/Maps/Kanban/FullCalendar 等重组件 `dynamic import` 或 client-only 声明 | SSR-02 · ASYNC-05 |
| 3 | 主题 helper | Chart/Calendar/Carousel/Maps override 走 `getBase*` / `merge*Options` deep merge | MER-02 · `merge-options-guide.md` |
| 4 |  Barrel / 导出 | 模板公开导出名与 `api-contracts.md` 一致；禁止 silent rename | TYPE-01 · TYPE-04 |
| 5 | 目录约定 | `components/ui`、`layout`、`context`、`lib` 分层符合 Skill 目录约定 | ADOPT-03 |

**交互动作**：抽查 3 个新增/改动模板文件 import 行 → 跑 `audit_compat_contracts.py` + `tsc --noEmit`（若项目已配置）。

## CON-04 — Skill 红线与内容/设计限制

**对照 reference**：`quality-rubric.md`、`chinese-copy-review-checklist.md`、`icon-system.md`、`decision-matrix.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 中文默认文案 | mock/placeholder/helper/空态/错误/按钮默认中文；技术缩写可保留 | COPY-01 · COPY-02 |
| 2 | 禁止品牌硬编码 | 不把 DeepTalk/Nex/项目路由/品牌写入 TailAdmin 默认规则 | `domain-scenarios.md` · SOP 红线 |
| 3 | 图标约束 | 语义图标先查 `icon-system.md`；源 SVG 覆盖的不无理由换 lucide | ICON-001 · CON-04 |
| 4 | 业务密度 | 禁止为「高端感」削弱表格密度、KPI 信息层次或业务操作可达性 | DRIFT-01 · VIS-03 |
| 5 | 演化写回 | 稳定复现的错选/约束缺口写回 decision-matrix when-not，非只修单页 | `sop.md` · GEN-01 |

**交互动作**：抽 1 个表单页 + 1 个领域场景页 → 检查 placeholder/列头/空态中文 → 确认无项目专有品牌字符串。

## CON-05 — MS 场景约束束合规

**对照 reference**：`scenario-override-recipes.md`、`business-validation-checklist.md`、`decision-matrix.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关页：`ControlPlaneHub` 受控 props；Token/浮层/中文 mock 合规；preview gateway-patterns | SOR-05 · VAL-01 |
| 2 | MS-10 | CI/CD 页：Pipeline/LogStream client 边界 + 中文阶段文案；非 Kanban 冒充 | SOR-02 · VAL-02 |
| 3 | MS-11 | BI 页：Chart dynamic + `chartPaletteCssVars`；筛选 chips 中文；非单图硬编码色 | SOR-01 · VAL-03 |
| 4 | MS-12 | PaaS 页：Maps client-only + ResourceTable 密度；恢复/伸缩确认 Dialog 中文 | SOR-03 · VAL-04 |
| 5 | MS-13 | 治理页：PermissionMatrix 非 Switch 列表；Wizard 分步 + 审计表异步态合规 | SOR-04 · VAL-05 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **约束遵守（G70）** 列 → 确认 CON-01～04 在场景内同时满足。

## 五类约束遵守速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| Token 违规 | 页面内 `#hex`、裸 `blue-500`、dark 边框丢失 | `token-index.md` | CON-01 · VIS-* |
| 框架违规 | 手写 div 弹层、模板字符串拼 class | `engineering-guards.md` | CON-02 · RUN-03 |
| 导入/边界 | 深层相对 import、SSR 直渲 Chart | `extension-audit.md` | CON-03 · SSR-* |
| 红线/文案 | 英文 placeholder、品牌路由硬编码 | `quality-rubric.md` | CON-04 · COPY-* |
| MS 场景 | 领域页违反 Token+API+文案组合约束 | `decision-matrix.md` MS 表 | CON-05 · VAL-* |

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/run_token_hit_tests.py b-design-system-tailadmin-radix
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的 Token 违规、非 Radix 浮层、导入穿透或英文默认文案。
- MS 场景在工程边界（client-only、受控 props、中文 mock）上反复失败。
- `engineering-guards.md` 未覆盖的新框架约束模式。

症状 ID 对照：`upgrade-troubleshooting.md` 中 CON-01（Token）～ CON-05（MS 场景）；场景级 CON-06～10 见 `scene-constraint-compliance-review-checklist.md`（DOCS-028 / G77）。与 VIS-*、COPY-*、SSR-*、VAL-* 交叉引用。

## 交叉引用

| 主题 | 文件 |
|---|---|
| 工程守卫 | `engineering-guards.md` |
| Token 索引 | `token-index.md` |
| 质量规程 | `quality-rubric.md` |
| 决策矩阵 | `decision-matrix.md` |
| 场景约束遵守 | `scene-constraint-compliance-review-checklist.md` |
| 中文文案 | `chinese-copy-review-checklist.md` |
| 视觉 Token | `visual-token-review-checklist.md` |
| 可访问性 | `accessibility-review-checklist.md` |
| 业务验证 | `business-validation-checklist.md` |
| 模式覆盖 | `pattern-coverage-review-checklist.md` |
| 故障排查 | `upgrade-troubleshooting.md` |
