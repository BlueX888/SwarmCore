# MN-01 — ThemeToggle 导出名 alias 演练

## 元信息

```yaml
component: ThemeToggle
change_type: rename
severity: additive-deprecation
introduced_in: G48-COMPAT-003
compat_until: G50
status: active
scenario_ref: MS-01
```

## 变更摘要

索引与文档使用概念名 `ThemeToggle`，可复制模板导出 `ThemeToggleButton`。本轮 additive 提供 `ThemeToggle` alias 与 deprecated wrapper，避免业务项目因统一导出名而 breaking。

## 旧用法

```tsx
import { ThemeToggleButton } from "@/components/layout/theme-toggle";

<ThemeToggleButton aria-label="切换深浅色主题" />
```

## 新用法

```tsx
import { ThemeToggle } from "@/components/layout/theme-toggle";
// 或
import { ThemeToggle } from "@/components/ui/deprecated/theme-toggle-alias";

<ThemeToggle aria-label="切换深浅色主题" />
```

## Deprecated Wrapper

```tsx
// templates/ui/deprecated/theme-toggle-alias.tsx
/** @deprecated 使用 ThemeToggleButton 或 layout/theme-toggle 的 ThemeToggle alias。兼容至 G50，见 MN-01 */
export { ThemeToggleButton as ThemeToggle } from "@/components/layout/theme-toggle";
```

## 影响范围

| 区域 | 是否受影响 | 说明 |
|---|---|---|
| `templates/layout/theme-toggle.tsx` | yes | additive `ThemeToggle` re-export |
| `templates/ui/deprecated/` | yes | 独立 wrapper 入口 |
| `preview.html` | no | 仍使用 ThemeToggleButton |
| `component-index.md` | yes | 标注双导出名 |
| 业务 vendored copy | yes | import 路径可选迁移 |

## 兼容期与回滚

- **兼容期**：`ThemeToggleButton` 与 `ThemeToggle` 并存至 G50。
- **回滚**：移除 alias import，继续使用 `ThemeToggleButton`。
- **检测**：`audit_migration_drills.py` + `verify_design_system.py`。

## 验证清单

- [x] `ThemeToggle` alias 已导出且类型与 `ThemeToggleButton` 一致
- [x] deprecated wrapper 已注册于 `templates/ui/deprecated/`
- [x] `api-contracts.md` 风险表已引用 MN-01
- [x] `component-index.md` 已标注双导出名
- [x] `scorecard.md` 反向审计已记录
