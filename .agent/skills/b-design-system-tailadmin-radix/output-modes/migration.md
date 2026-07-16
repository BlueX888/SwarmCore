# 迁移模式

将已有 UI 或 TailAdmin 源组件迁移到 **shadcn/Radix** 实现，或在业务项目中升级已 vendored 的 TailAdmin-Radix Skill 快照。

## 读取顺序

### 首次从 TailAdmin 源项目迁移

1. `references/engineering-guards.md`
2. `references/component-index.md` — TailAdmin → shadcn 映射
3. 相关 `component-styles/*-template.md`
4. `references/token-index.md`
5. `references/decision-matrix.md` — 避免组件/页面错选

### 业务项目升级 Skill 快照

1. `references/version-pinning-guide.md` — 确认 pin 方式与升级检查清单
2. `references/migration-playbook.md` — MS-01～13 场景路由表
3. `references/upgrade-troubleshooting.md` — 升级后症状排查与回滚
4. `references/backward-compatibility.md` — 兼容原则与 deprecated 模式
5. `references/migration-scenarios.md` — 场景详情与降级路径
6. `references/migration-notes/` — MN-01～03 已填写演练
7. `references/api-override-recipes.md` / `references/scenario-override-recipes.md`
8. `references/merge-options-guide.md` — 嵌套 options 浅/深 merge

## 迁移优先级

| 优先级 | 替换目标 | 原因 |
|---|---|---|
| P0 | Modal → Dialog | a11y、focus trap |
| P0 | Dropdown → DropdownMenu | 键盘导航 |
| P1 | 模板字符串 className → `cn()` + `cva` | 可维护性 |
| P1 | 原生 select → shadcn Select | 样式一致 |
| P2 | flatpickr → Calendar+Popover | 可选 |
| P3 | ApexCharts 主题 | 保留库，仅改色 |

## 单组件迁移步骤

1. 读页面溯源：`examples/b-design-system-tailadmin-radix/src/data/tailadminPageCatalog.ts` + `component-index.md`；组件实现见 `templates/`
2. 提取 variant/size 与 Token 类名
3. 在 `components/ui/` 用 shadcn CLI add 或覆盖 variants
4. 替换页面 import：`../ui/button/Button` → `@/components/ui/button`
5. 验证 dark/focus/disabled 态
6. 更新 `component-index.md` 若 API 变化

## Skill 快照升级步骤

1. 记录当前 pin commit 与关键页面截图基线
2. 查 `migration-playbook.md` 找到业务使用的 MS ID
3. MN 场景（MS-01～03）：按 MN 验证清单在业务仓库演练
4. MS-04～08：确认无硬编码 palette / 手动 spread 默认 theme
5. MS-09～13：确认页面组合使用受控 props，非 Skill 内部 mock
6. 运行 `audit_migration_drills.py` + `audit_compat_contracts.py` + `verify_design_system.py`
7. 业务侧 `tsc --noEmit` + 截图对比
8. 若回归：查 `upgrade-troubleshooting.md` 症状路由表并执行回滚或降级

## Token 迁移

将散落 `gray-700` 等对照 `token-index.md` 检索别名；`index.css` 统一 `@theme`。

## 禁止

- 同时保留手写 Modal 与 Dialog 两套 API
- 迁移时改变视觉（除非修复 a11y 缺陷如 focus ring）
- 未读 `decision-matrix.md` 即选用跨组件场景模板（易触发 SEL-* 错选）
- 升级失败时静默 pin 新 sha 而不记录回滚原因
