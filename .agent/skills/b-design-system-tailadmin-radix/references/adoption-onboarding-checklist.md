# Skill 首次接入与 vendoring 清单

> DOCS-008 / G57 产物。业务仓库**首次**从 0 接入或 vendored 复制 TailAdmin-Radix Skill 时，按本清单执行可复现冒烟，确认脚手架、Token、壳层、快照 pin 与首个业务页在真实项目中成立，而非仅依赖 Skill 内部 preview mock。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| 新建 Vite/React 后台并接入 Skill | ADOPT-01～03 |
| 从 TailAdmin 源项目迁移到 shadcn/Radix | ADOPT-01 + `output-modes/migration.md` |
| Vendored copy / submodule 固定快照 | ADOPT-04 |
| 首个业务页（仪表盘/列表/表单）上线前 | ADOPT-05 |
| 不确定从哪开始 | `agent-retrieval-guide.md` 首次接入路由 |

## 通用前置

1. 确认 Skill 路径或 vendored 目录可读：`b-design-system-tailadmin-radix/`。
2. 业务仓库 `package.json` 含 React 19 + Vite + Tailwind v4 + shadcn 依赖（见 `engineering-guards.md`）。
3. 在业务仓库创建或更新 `docs/design-system-pin.md`，记录 `pinned_commit`、`local_skill`、`runtime_roots`（ADOPT-04）。
4. 复制 `upstream-changelog-template.md` 为 `docs/design-system-upstream.md`（ADOPT-06）。
4. 用户可见文案默认中文（技术缩写除外，见 `quality-rubric.md`）。

## ADOPT-01 — 脚手架与 shadcn 初始化

**对照 reference**：`output-modes/from-zero.md`、`engineering-guards.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Vite + TS | `npm create vite@latest` 或等价；`tsc --noEmit` 无 error | ADOPT-01 |
| 2 | Tailwind v4 | `index.css` 含 `@import "tailwindcss"` 与 `@theme` | `token-index.md` |
| 3 | shadcn init | `components.json` 来自 Skill `templates/components.json` | `engineering-guards.md` |
| 4 | 核心 UI 覆盖 | Button/Input/Dialog/Dropdown 等已从 shadcn add 并覆盖 Skill 模板 | ADOPT-01 |
| 5 | 路径别名 | `@/components/ui`、`@/lib/utils` 解析正确 | ADOPT-03 |

**交互动作**：`pnpm dev` 启动 → 访问根路由无白屏 → 控制台无 Radix Portal/ThemeProvider 报错。

## ADOPT-02 — Token 与主题复制

**对照 reference**：`token-index.md`、`visual-language.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | @theme 色板 | `brand-*`、`gray-*`、`success-*` 等语义 Token 在 `index.css` | DRIFT-01 |
| 2 | menu utility | `@utility menu-*` 已复制，侧栏菜单样式正常 | `engineering-guards.md` |
| 3 | dark variant | `@custom-variant dark (&:is(.dark *))` + `html.dark` 切换 | VIS-02 |
| 4 | 无硬编码 hex | 业务 `src/components` 无 `#hex`/`rgb()` 颜色（`index.css` 除外） | DRIFT-01 |
| 5 | cn/cva | 变体组件使用 `cn()` + `cva`，无模板字符串 className | DRIFT-02 |

**交互动作**：切换 light/dark → 检查正文对比度与边框层级 → 运行 `rg` 硬编码颜色抽检（见 `engineering-guards.md`）。

## ADOPT-03 — 壳层与布局首屏

**对照 golden**：`overview`、`devops-patterns` shell framing

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | AppLayout | `AppSidebar` + `AppHeader` + 内容区 `Outlet` 渲染 | ADOPT-03 |
| 2 | 侧栏尺寸 | 展开 290px / 折叠 90px；内容区不被侧栏遮挡 | DRIFT-05 |
| 3 | ThemeContext | `ThemeToggle` 可切换；`TooltipProvider` 包裹根 | VIS-02 |
| 4 | 内容宽度 | 主内容 `max-w-(--breakpoint-2xl)` 展开，无首屏大面积空白 | REV-01 |
| 5 | 响应式 | tablet 1024px 侧栏与内容 framing 正常 | `golden-screens.md` |

**交互动作**：折叠侧栏 → 切换主题 → desktop 1440×1000 截图归档。

## ADOPT-04 — Skill 快照 pin 与审计

**对照 reference**：`version-pinning-guide.md`、`backward-compatibility.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | pin 记录 | `docs/design-system-pin.md` 含 `pinned_commit`、`pinned_date`、`local_skill`、`runtime_roots` | ADOPT-04 |
| 2 | 契约引用 | pin 文件链接 `api-contracts.md@<sha>` 或 vendored 路径 | COMPAT-002 |
| 3 | verify 通过 | `verify_design_system.py` exit 0（vendored 时） | RUN-01 |
| 4 | compat 审计 | `audit_compat_contracts.py` exit 0 | RUN-01 |
| 5 | token 命中 | `run_token_hit_tests.py` exit 0（可选 CI） | RUN-04 |

**交互动作**：记录 pin → 运行 verify + audit_compat → 更新 pin 文件中的 `last_verified_at`。

## ADOPT-05 — 首个业务页 smoke

**对照 reference**：`decision-matrix.md`、`ui-drift-review-checklist.md` 对应 REV 块

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 页面选型 | 首个页面意图与 decision-matrix 正选一致（非临时拼 Card） | DRIFT-03 |
| 2 | 组件选型 | 表单/表格/浮层用 shadcn/Radix，非手写 Modal | DRIFT-02 |
| 3 | 状态覆盖 | loading/empty/error/disabled/focus 至少各 1 处可辨 | `state-index.md` |
| 4 | 中文文案 | mock/placeholder/按钮为中文 | DRIFT-04 |
| 5 | 截图归档 | light + dark 各 1 张；交互组件补打开态 | REV-01～05 对应块 |

**交互动作**：完成首个 CRUD/仪表盘/表单主路径 → 跑 REV 对应块 3 项检查 → 截图存入业务 `docs/ui-screenshots/`。

## ADOPT-06 — upstream 登记（copy 模式）

**对照 reference**：`upstream-contribution-guide.md`、`upstream-changelog-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | upstream 文件 | `docs/design-system-upstream.md` 存在 | ADOPT-06 · UP-02 |
| 2 | 同步顺序 | runtime → `local_skill` 后再登记 | UP-01 |
| 3 | 可泛化改动 | `status: pending` + `upstream_paths` 完整 | UP-02 |
| 4 | 业务专属 | 领域组件为 `local-only` | UP-03 |

**交互动作**：改模板后 → 同步 local_skill → 追加 upstream 条目 → 若准备本尊合并则开 PR 或通知维护者。

## 六类接入风险速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 脚手架缺失 | 白屏、shadcn 组件找不到、alias 报错 | `from-zero.md` · `engineering-guards.md` | ADOPT-01 |
| Token 未复制 | 默认 Tailwind 色板、dark 失效 | `token-index.md` | ADOPT-02 · VIS-02 |
| 壳层未接 | 无侧栏/顶栏、内容全宽错位 | `templates/layout/` | ADOPT-03 · DRIFT-05 |
| pin 未记录 | 升级后不知基线、契约漂移 | `version-pinning-guide.md` | ADOPT-04 |
| 首页错选 | 普通 Input/Table 冒充专用组件 | `decision-matrix.md` | ADOPT-05 · SEL-* |
| 改模板未登记 | 本尊不知业务领先改动 | `upstream-contribution-guide.md` | ADOPT-06 · UP-* |

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/run_token_hit_tests.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库
pnpm exec tsc --noEmit
pnpm exec eslint . --max-warnings 0
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 接入步骤在真实业务中**稳定复现失败**且根因为 Skill 文档缺口。
- 发现 ADOPT-01～06 未覆盖的新接入路径（monorepo、SSR、微前端等）→ 见 `ssr-microfrontend-adoption-checklist.md`。
- 检索路径超过 3 跳才找到本清单或对应 ADOPT 块。
- 业务侧可泛化 bugfix/组件/文档改动 → 按 `upstream-contribution-guide.md` 写 `design-system-upstream.md`。

症状 ID 对照：`upgrade-troubleshooting.md` 中 ADOPT-01（脚手架）～ ADOPT-06（upstream 登记）。

新增 ADOPT-* 症状行写入 `upgrade-troubleshooting.md`；可复用检查项可沉淀到本文件对应 ADOPT 块。

## 检索入口

| 意图 | 读 |
|---|---|
| 从 0 脚手架步骤 | `output-modes/from-zero.md` |
| 迁移已有 TailAdmin | `output-modes/migration.md` |
| pin 与升级 | `version-pinning-guide.md` |
| 回流本尊 / upstream 登记 | `upstream-contribution-guide.md` |
| 部署后 MS 冒烟 | `business-validation-checklist.md` |
| UI 漂移评审 | `ui-drift-review-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` ADOPT-* / RUN-* |
| SSR / 微前端接入 | `ssr-microfrontend-adoption-checklist.md` |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
