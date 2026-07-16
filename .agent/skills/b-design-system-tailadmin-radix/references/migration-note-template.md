# Migration Note 模板

> 发生破坏性变更时，在对应 `component-styles/*.md` 或 PR 描述中复制本模板填写。同轮不得删除旧 API 而不留 deprecated wrapper。

## 元信息

```yaml
component: <组件或 theme lib 名>
change_type: rename | remove | default-change | behavior-change | dependency-change
severity: breaking | visual-breaking | additive-deprecation
introduced_in: G<round>-<ID>
compat_until: G<round+N>  # 至少保留一个演化周期
status: draft | active | completed
```

## 变更摘要

一句话说明改了什么、为什么改。

## 旧用法

```tsx
// 变更前 — 业务项目中可能存在的调用
```

## 新用法

```tsx
// 变更后 — 推荐迁移目标
```

## Deprecated Wrapper（必填，若 severity ≠ additive）

```tsx
/**
 * @deprecated 使用 <NewComponent /> 替代。兼容至 G<round+N>，见 migration-note-<id>.md
 */
export function OldComponentName(props: OldProps) {
  return <NewComponent {...mapOldToNew(props)} />;
}
```

## 影响范围

| 区域 | 是否受影响 | 说明 |
|---|---|---|
| `templates/` 可复制模板 | yes/no | 路径 |
| `preview.html` frame | yes/no | section id |
| `component-index.md` | yes/no | |
| 业务 vendored copy | yes/no | 典型路径 |
| 截图 / golden screens | yes/no | |

## 兼容期与回滚

- **兼容期**：旧 API 通过 wrapper 保留至 `<日期或轮次>`。
- **回滚**：`git revert <sha>` 或 pin Skill 快照至 `<tag/commit>`。
- **检测**：`verify_design_system.py` + 业务侧类型检查 / 截图对比。

## 验证清单

- [ ] deprecated wrapper 已导出且类型与旧 API 一致
- [ ] `api-contracts.md` 风险表已更新
- [ ] `component-index.md` 已标注 deprecated
- [ ] `scorecard.md` 反向审计已记录
- [ ] preview 文案指向新模板（若适用）

## 示例：ThemeToggle 导出名 alias（预防性，非已发生变更）

```yaml
component: ThemeToggle
change_type: rename
severity: additive-deprecation
introduced_in: 未计划
compat_until: N/A
status: draft
```

旧用法（若未来统一导出名）：

```tsx
import { ThemeToggleButton } from "@/components/layout/theme-toggle";
```

新用法 / 推荐 alias：

```tsx
export { ThemeToggleButton as ThemeToggle } from "@/components/layout/theme-toggle";
```

影响范围：仅 import 路径；props `className` / `aria-label` 不变。
