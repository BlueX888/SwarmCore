# TreeTable 页壳

层级资源 / 权限继承列表的标准组合：

```
QueryShell
├── 工具栏（搜索 + SplitButton 导出）
├── TreeTable（checkable + loadData 可选）
└── PaginationBar（showSizeChanger + showQuickJumper）
```

## 选型

| 场景 | 用 |
|---|---|
| 扁平行 CRUD | `DataTableCard` |
| 纯树导航 | `Tree` |
| 树 + 多列数据 | **TreeTable** |

## MS 映射

- **MS-12**：PaaS 命名空间 → 集群 → 节点
- **MS-13**：组织树 + 列权限（可替代部分扁平 `PermissionMatrix`）

## 四态

`QueryShell` 包裹：`loading` / `empty` / `error` / `success`；树表 `loading` 与壳层 loading 二选一，避免双 Spinner。
