# 布局模式 — Three-Column Workspace

典型路由：`/projects/:id/repo`、`/workspace`、`/code/:repo/tree`

关联：`code-repository.md`、`templates/layout/three-column-workspace.tsx`

## 适用场景

- 项目 → 仓库 → 文件树 + 主编辑/预览区
- 资源树（K8s 命名空间）+ 列表 + 详情 YAML
- 文档库：分类树 + 文件列表 + 阅读器

## 结构

```tsx
<ThreeColumnWorkspace
  rail={<ProjectSwitcher />}
  tree={<ResourceTree nodes={…} selectedId={…} />}
  main={<CodeViewer path={…} />}
  aside={showPreview ? <PreviewPanel /> : null}
/>
```

## 列宽

| 列 | desktop | tablet | mobile |
|---|---|---|---|
| Rail（项目/门户） | 56–72px 图标栏 | 隐藏，Drawer 触发 | Drawer |
| Tree | 240–280px | 200px 或可折叠 | Sheet |
| Main | flex-1 min-w-0 | flex-1 | 全宽 |
| Aside（可选） | 320–400px | 折叠为 tab | bottom sheet |

## 高度链

```tsx
<div className="flex h-[calc(100vh-64px)] min-h-0">
  <nav className="shrink-0 border-r …" />
  <aside className="flex w-64 shrink-0 flex-col min-h-0">
    <div className="flex-1 overflow-y-auto custom-scrollbar">…</div>
  </aside>
  <main className="flex min-w-0 flex-1 flex-col min-h-0">
    <header className="shrink-0 border-b …" />
    <div className="flex-1 overflow-auto">…</div>
  </main>
</div>
```

## 树交互

- 选中高亮 `bg-brand-50 text-brand-500`
- 展开/折叠 `ChevronRight` 旋转
- 搜索过滤：高亮匹配，无结果 empty
- 右键菜单：Rename / Delete（危险项 confirm）

## 主工作区

- 顶栏：面包屑路径 + branch/tag + actions
- 代码：`font-mono text-theme-sm` + 行号 gutter
- Diff：split view `grid-cols-2`，同步滚动

## 空态

- 未选树节点：main 区「Select a file to view」
- 空仓库：tree empty + main 引导 clone

## 截图验收

- 三列在 1440px 均可见，主区占 ≥50% 宽度
- 树与代码区文本不重叠
- mobile 不得三列挤在一行
