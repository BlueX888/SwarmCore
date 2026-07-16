# ContextMenu 表格行操作

DataTable / TreeTable 行右键菜单规范：

```
DataTable
└── ContextMenu
    ├── ContextMenuTrigger（包裹 TableRow 或行内操作区）
    └── ContextMenuContent
        ├── ContextMenuItem「编辑」
        ├── ContextMenuItem「复制」
        └── ContextMenuItem destructive「删除」
```

## 组件

- `context-menu.tsx`（`@radix-ui/react-context-menu`）

## 与 DropdownMenu 选型

| 场景 | 组件 |
|------|------|
| 点击「更多 ▾」按钮 | `DropdownMenu` |
| 行/节点右键 | `ContextMenu` |
| 危险操作二次确认 | `Popconfirm` 或 `useConfirm` |

## a11y

- 键盘：ContextMenu 支持方向键与 Enter
- 每项需可读 `aria-label`
