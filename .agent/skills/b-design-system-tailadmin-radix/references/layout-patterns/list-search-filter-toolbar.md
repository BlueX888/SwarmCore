# ListSearchFilterToolbar — 列表搜索 + 筛选

**模板**：`templates/ui/list-search-filter-toolbar.tsx` · `list-search-input.tsx` · `list-filter-panel.tsx`

用于 CRUD 列表、审计日志、工单列表等 **Table List** 页统一工具栏。

## 交互

1. **搜索**：输入 300ms debounce 触发 `onSearch`；Enter 立即触发；清空输入时页面应重置 query（由页面 `onChange` 处理）。
2. **筛选**：点击搜索框右侧漏斗图标；Popover（默认）或 Drawer（复杂）；draft 编辑后点「应用」才写回 `filter.onApply`。
3. **角标**：`countActiveFilters` 统计非默认 select / 已勾选 checkbox / 非空 text。
4. **禁用**：列表 loading / refetch 时传 `disabled` 到 toolbar。

## 字段类型

| kind | 用途 |
|------|------|
| `select` | 状态、格式、环境；`allValue` 默认 `all` |
| `text` | 操作者 ID、编号 |
| `checkbox` | 布尔开关（如「仅保护分支」「待我审批」） |

业务专用字段（如项目成员 `AssigneeSelect`）在应用层扩展 `ListFilterPanel`，不要放入 Skill 通用模板。

## Drawer 筛选（Sheet 约束）

```tsx
<Sheet modal={false} open={open} onOpenChange={setOpen}>
  <SheetContent side="right" size="filter" showOverlay={false} className="flex flex-col">
    ...
  </SheetContent>
</Sheet>
```

- **`showOverlay={false}`**：不 blur 背后列表
- **`modal={false}`**：列表仍可滚动/点击
- **`SheetContent` 禁止**在 `cn()` 中于 `sheetVariants()`（含 `fixed`）之后追加 `relative` — 见 `upgrade-troubleshooting.md#sheet-content-fixed`

## 与 DataTableCard 关系

- 简单页：Card 内工具栏行 + `ListSearchFilterToolbar` + 右侧 actions
- 重页：继续用 `DataTableCard` 的 title/bulk/footer，toolbar 行替换为同一组件

## 顶栏搜索（HeaderSearch）区别

`HeaderSearch`（`templates/layout/app-header.tsx`）是 **全局命令/导航搜索**，单元素 `dark:bg-gray-900`。

**禁止**用「外壳 div + 内层 Input 双层背景」模拟顶栏搜索 — 暗色模式会出现双色条。列表页搜索用 `ListSearchInput`，顶栏用 `HeaderSearch` 或等效单元素样式。

## Dialog 内 Select

Dialog 内 `SelectContent` portal 到 `document.body` 时，可能与 Dialog 焦点陷阱冲突（Console `aria-hidden` 警告）。

- 空选项时不渲染 Select，改静态文案
- 或 `SelectContent` portal 挂到 `DialogContent` 节点（项目层扩展）
- 优先 `position="popper"`

## 禁止

- inline 多个 `Label + Select` 作为列表主筛选
- 筛选变更即时打 API（无「应用」确认），除非仅 search debounce
- 在 `onOpenChange(false)` 里手动删除 Radix portal DOM（见 `engineering-guards.md`）
