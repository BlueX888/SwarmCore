# 可访问性评审清单

> DOCS-010 / G59 产物。对 Agent 生成或人工改写的业务页面执行**可复现可访问性抽检**，覆盖键盘、焦点、表单标签、浮层、图标命名、对比度与动态状态，并与 `engineering-guards.md`、`state-index.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前 a11y 抽检 | 对应 A11Y 块 + `quality-rubric.md` 约束遵守 |
| 大规模 Agent 生成后抽检 | A11Y-01～05 各抽 1 页 |
| 键盘无法完成主任务 | 先跑 A11Y-01，再查 `state-index.md` |
| 屏幕阅读器报「按钮无名称」 | A11Y-04 + `icon-system.md` |
| 表单错误无法被读屏识别 | A11Y-02 + `layout-patterns/form-composition.md` |

## 通用前置

1. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
2. 抽检视口 **desktop 1440×1000**，**light + dark** 各 1 次键盘遍历；Dialog/Drawer 补打开态焦点截图。
3. 用户可见标签、按钮、错误文案默认中文（技术缩写除外，见 `quality-rubric.md`）。
4. 浮层与复杂控件必须先确认使用 Radix/shadcn，非手写 div modal（见 `engineering-guards.md`）。

## A11Y-01 — 键盘导航与焦点顺序

**对照 reference**：`engineering-guards.md#可访问性`、`state-index.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Tab 顺序 | 主任务控件可按逻辑 Tab 到达；无意外跳焦 | A11Y-01 |
| 2 | focus-visible | 键盘焦点环可见（`focus-visible:ring-*`），鼠标点击不强制显示粗环 | `state-index.md` |
| 3 | 侧栏/顶栏 | 折叠侧栏后 Tab 不进入不可见菜单项 | `interaction-motion.md` |
| 4 | 数据表格 | 行操作、排序、分页可用键盘触发 | A11Y-03 |
| 5 | 无键盘陷阱 | 非 Modal 区域 Tab 不会永久困在子树内 | A11Y-03 |

**交互动作**：仅用键盘 Tab 完成「打开侧栏项 → 进入主内容第一个控件 → 触发一次主操作」→ 记录是否可达。

## A11Y-02 — 表单标签、错误与必填

**对照 reference**：`layout-patterns/form-composition.md`、`state-index.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Label 关联 | 每个输入有可见 `Label` + `htmlFor`/`id` 或等效 `aria-labelledby` | A11Y-02 |
| 2 | 错误态 | 校验失败字段 `aria-invalid="true"` + 可读错误文案（FormMessage） | `state-index.md` |
| 3 | 必填提示 | required 字段有「必填」或 `*` 且读屏可理解 | DRIFT-04 |
| 4 | 高级输入 | 金额/密钥/OTP 等专用控件保留语义标签，非裸 Input | `decision-matrix.md#表单` |
| 5 | 禁用/只读 | disabled/readonly 状态可辨且不可误提交 | `state-index.md` |

**交互动作**：提交空表单触发错误 → 确认焦点落到首个错误字段 → 错误文案为中文。

## A11Y-03 — 浮层、对话框与焦点管理

**对照 reference**：`engineering-guards.md#Radix 组合规则`、`interaction-motion.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Dialog 标题 | 居中/确认 Dialog 有 `DialogTitle` 或 `aria-labelledby` | A11Y-03 |
| 2 | 焦点陷阱 | Modal 打开后 Tab 在浮层内循环；关闭后焦点回到触发器 | SSR-04 |
| 3 | Esc 关闭 | Dialog/Drawer/Popover 支持 Esc 或明确关闭按钮 | `state-index.md` |
| 4 | 层级 | 打开 Dialog 时背景 Dropdown 不穿透可点 | DRIFT-05 |
| 5 | 滚动锁定 | Drawer/Dialog 打开时背景滚动锁定不导致焦点丢失 | `interaction-motion.md` |

**交互动作**：键盘打开 Dialog → Tab 循环 3 次 → Esc 关闭 → 焦点回到触发按钮。

## A11Y-04 — 图标按钮与装饰图标

**对照 reference**：`icon-system.md`、`engineering-guards.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 图标按钮 | 仅图标 Button 有 `aria-label` 或可见 tooltip 且可键盘聚焦 | A11Y-04 |
| 2 | 装饰图标 | 纯装饰 SVG 使用 `aria-hidden="true"` | `icon-system.md` |
| 3 | 语义图标 | 状态/告警图标有文本并列或 `aria-label` | DRIFT-03 |
| 4 | ThemeToggle | 主题切换按钮标签为中文（如「切换主题」） | ADOPT-03 |
| 5 | 表格行操作 | 行内 icon-only 操作有「编辑」「删除」等可读名称 | A11Y-04 |

**交互动作**：用读屏或 DevTools Accessibility 树检查顶栏 ThemeToggle、表格行操作、关闭按钮均有名称。

## A11Y-05 — 对比度、状态控件与动态内容

**对照 reference**：`token-index.md`、`visual-language.md`、`quality-rubric.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 正文对比度 | light：正文 `gray-800` on 白底；dark：`white/90` on `gray-900` 可读 | VIS-02 |
| 2 | 状态控件 | Switch/Checkbox/Radio 选中/未选中/禁用态可辨，轨道与圆点不错位 | DRIFT-05 |
| 3 | Loading | 异步加载有 Spinner/`aria-busy` 或区域 `aria-live="polite"` | `state-index.md` |
| 4 | 空态/错误 | empty/error 区块有标题+说明，非仅图标 | `prd/F02-data-state.md` |
| 5 | MS 抽检 | MS-09～13 至少 1 页完成 A11Y-01～04 键盘+标签抽检 | `business-validation-checklist.md` |

**交互动作**：切换 light/dark → 检查 Switch 与 Checkbox 边界 → 触发 loading 态确认有可读反馈。

## 五类可访问性速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 键盘/焦点 | Tab 跳焦、无 focus 环、困在子树 | `state-index.md` · preview | A11Y-01 · A11Y-03 |
| 表单/标签 | 无 Label、错误不可读、必填不明 | `form-composition.md` | A11Y-02 · DRIFT-04 |
| 浮层/Modal | 无标题、Esc 无效、焦点不回 | `engineering-guards.md` | A11Y-03 · SSR-04 |
| 图标/名称 | 图标按钮无名称、装饰图标误读 | `icon-system.md` | A11Y-04 |
| 对比/动态 | dark 对比不足、loading 无反馈 | `token-index.md` · `quality-rubric.md` | A11Y-05 · VIS-02 |

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库
pnpm exec tsc --noEmit
# 可选：eslint jsx-a11y
pnpm exec eslint src/components --max-warnings=0
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的无标签图标按钮、无标题 Dialog 或键盘不可达主路径。
- MS 场景组合存在可访问性反模式（如 RBAC 仅用 Switch 无矩阵语义）。
- 检索路径超过 3 跳才找到本清单或对应 A11Y 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 A11Y-01（键盘焦点）～ A11Y-05（对比度与动态）；场景级 A11Y-06～10 见 `scene-accessibility-review-checklist.md`。

控件/页面级 A11Y-01～05 完成后，对 BI/Data Screen、DevOps、Gateway、PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-accessibility-review-checklist.md`（DOCS-026 / G75）。

新增 A11Y-* 症状行写入 `upgrade-troubleshooting.md`；可复用检查项可沉淀到本文件对应 A11Y 块。

## 检索入口

| 意图 | 读 |
|---|---|
| 工程守卫与 Radix 规则 | `engineering-guards.md` |
| 交互状态与焦点 | `state-index.md` |
| 组件/页面正选 | `decision-matrix.md` |
| UI 漂移评审 | `ui-drift-review-checklist.md` |
| 响应式抽检 | `responsive-review-checklist.md` |
| 异步状态抽检 | `async-state-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| SSR / 微前端 Portal | `ssr-microfrontend-adoption-checklist.md#ssr-04` |
| 症状与回滚 | `upgrade-troubleshooting.md` A11Y-* / VIS-* / DRIFT-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
