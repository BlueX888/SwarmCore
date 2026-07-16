# MN-02 — SearchCommand 无 react-router 演练

## 元信息

```yaml
component: SearchCommand
change_type: behavior-change
severity: additive-deprecation
introduced_in: G48-COMPAT-003
compat_until: G50
status: active
scenario_ref: MS-02
```

## 变更摘要

`SearchCommand` 默认通过 `useNavigate` 处理 `href` 跳转，无 react-router 的项目会运行时报错。本轮 additive 增加组件级 `onItemSelect` 与 `SearchCommandStatic` wrapper，供无路由环境使用。

## 旧用法

```tsx
import { SearchCommand, useSearchCommand } from "@/components/ui/search-command";

const { open, setOpen } = useSearchCommand();

<SearchCommand open={open} onOpenChange={setOpen} groups={groups} />
// 项带 href 时依赖 react-router
```

## 新用法

```tsx
import {
  SearchCommand,
  useSearchCommand,
} from "@/components/ui/search-command";

<SearchCommand
  open={open}
  onOpenChange={setOpen}
  groups={groups}
  onItemSelect={(item) => {
    if (item.href) window.location.assign(item.href);
    else item.onSelect?.();
  }}
/>
```

无路由降级：

```tsx
import { SearchCommandStatic } from "@/components/ui/deprecated/search-command-static";

<SearchCommandStatic open={open} onOpenChange={setOpen} groups={groups} />
```

## Deprecated Wrapper

```tsx
// templates/ui/deprecated/search-command-static.tsx
/** @deprecated 无 react-router 时使用。优先传 onItemSelect。兼容至 G50，见 MN-02 */
export function SearchCommandStatic(props) {
  return (
    <SearchCommand
      {...props}
      onItemSelect={(item) => {
        if (item.href) window.location.assign(item.href);
        else item.onSelect?.();
      }}
    />
  );
}
```

## 影响范围

| 区域 | 是否受影响 | 说明 |
|---|---|---|
| `templates/ui/search-command.tsx` | yes | additive `onItemSelect` prop |
| `templates/ui/deprecated/` | yes | SearchCommandStatic wrapper |
| `preview.html` | no | preview 环境有 router mock |
| `component-index.md` | yes | 无路由迁移路径 |
| 业务 vendored copy | yes | 静态站点/嵌入页常见 |

## 兼容期与回滚

- **兼容期**：默认 `href` + navigate 行为保留；`onItemSelect` 为 optional override。
- **回滚**：移除 `onItemSelect`，恢复纯 navigate 行为。
- **检测**：`audit_migration_drills.py` 检查 wrapper 与 prop 存在。

## 验证清单

- [x] `onItemSelect` 已导出且覆盖 navigate 路径
- [x] `SearchCommandStatic` deprecated wrapper 已注册
- [x] `api-contracts.md` Command 契约已更新
- [x] `migration-scenarios.md` MS-02 已链接 MN-02
- [x] `scorecard.md` 反向审计已记录
