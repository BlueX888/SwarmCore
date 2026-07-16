# 缺组件模式

当 `component-index.md` 无覆盖组件时，按本协议扩展。

## 步骤

1. **分类**：primitive / overlay / navigation / data-display / feedback / composite
2. **选型**：优先 shadcn registry；无则选 Radix primitive + TailAdmin Token
3. **实现**：
   - `cva` 定义 variants
   - `cn()` 合并 className
   - 覆盖 hover/focus/disabled/dark（见 `state-index.md`）
4. **文档**：
   - 更新 `references/component-index.md` 一行
   - 在对应 `component-styles/*-template.md` 追加 section
5. **示例**：在 `examples/b-design-system-tailadmin-radix` 增加真实可运行示例和打开态验收

## Radix 选型表

| 交互 | Radix 包 |
|---|---|
| 对话框 | `@radix-ui/react-dialog` |
| 下拉 | `@radix-ui/react-dropdown-menu` |
| 弹出 | `@radix-ui/react-popover` |
| 提示 | `@radix-ui/react-tooltip` |
| 标签页 | `@radix-ui/react-tabs` |
| 开关 | `@radix-ui/react-switch` |
| 单选 | `@radix-ui/react-radio-group` |
| 勾选 | `@radix-ui/react-checkbox` |
| 选择 | `@radix-ui/react-select` |
| 手风琴 | `@radix-ui/react-collapsible` |
| 悬停卡片 | `@radix-ui/react-hover-card` |
| 右键菜单 | `@radix-ui/react-context-menu` |

## 可选 peer 依赖

| 组件 | npm 包 | 版本 |
|---|---|---|
| Splitter | `react-resizable-panels` | ^2.x |
| Tour | `driver.js` | ^1.x |
| ColorPicker | `react-colorful` | ^5.x |
| DataTable virtual | `@tanstack/react-virtual` | ^3.x |
| Autocomplete virtual | `@tanstack/react-virtual` | ^3.x |
| QRCode | `qrcode` | ^1.x |
| RichTextEditor (Tiptap 可选) | `@tiptap/react` + `@tiptap/starter-kit` | ^2.x |
| RichTextEditor full toolbar | `@tiptap/extension-link` + `@tiptap/extension-table` + `@tiptap/extension-table-row` + `@tiptap/extension-table-cell` | ^2.x |
| OrderList / Transfer sort / Tree draggable | `@dnd-kit/core` + `@dnd-kit/sortable` + `@dnd-kit/utilities` | ^6.x / ^10.x / ^3.x |
| ContextMenu | `@radix-ui/react-context-menu` | ^2.x |

## API 约定

- 受控优先：`open` + `onOpenChange`
- 扩展：`className` + `...props` 透传
- 导出：named export + `VariantProps`

## 视觉对齐检查

- [ ] 使用 `token-index.md` 色板
- [ ] 圆角/阴影与同类组件一致
- [ ] `text-theme-sm` / `text-theme-xs` 字号
- [ ] `h-11` 表单对齐
