# Editor 主题 — Prism 代码块

独立 Editor 主题 shard。源：`components/ai/Codeblock.tsx`、`src/index.css`（Code Editor 段）。

**库**：`prismjs` + line-numbers 插件。

可复制模板：`templates/lib/editor-theme.ts` · **`templates/ui/code-block.tsx`** · **`templates/ui/code-editor.tsx`**

## 检索别名

| 意图 | 读本节 |
|---|---|
| 代码块壳层 | `#code-block-shell` |
| Header / Toolbar | `#toolbar` |
| 语法高亮 | `#prism-tokens` |
| 行号 | `#line-numbers` |
| 支持语言 | `#languages` |
| CSS 覆盖 | `#css-overrides` |
| 加载/空态 | `#data-states` |

## Code Block Shell

用于 AI Code Generator、支持工单代码片段等场景：

```tsx
import {
  codeBlockShellClass,
  codeBlockHeaderClass,
  codeBlockBodyClass,
  codeBlockPreClass,
} from "@/lib/editor-theme";

<div className={codeBlockShellClass}>
  <div className={codeBlockHeaderClass}>
    {/* language label + toolbar */}
  </div>
  <div className={codeBlockBodyClass}>
    <pre className={codeBlockPreClass}>
      <code className="language-tsx">{code}</code>
    </pre>
  </div>
</div>
```

- 外包 `ComponentCard` 或独立 `rounded-2xl border`
- Body `max-h-[350px]` + `custom-scrollbar`

## Toolbar

```tsx
import { codeBlockToolbarButtonClass } from "@/lib/editor-theme";

<button type="button" className={codeBlockToolbarButtonClass} aria-label="Copy code">
  <CopyIcon className="size-4" />
</button>
```

- 圆形 `size-8`；`border-gray-200 dark:border-gray-800`
- Copy 成功后 1.5s 切换图标；Edit 按钮可选

## Prism Tokens

宿主 `index.css` 引入 `prismCssOverrides`：

| Token | Light | Dark |
|---|---|---|
| base text | `#344054` | `#98a2b3` |
| tag/selector | `#267f99` | `#267f99` |
| property | `#0070c1` | `#0070c1` |
| attr-value | `#a31615` | `#a31615` |
| doctype/name | `#018001` | `#018001` |
| punctuation | `#344054` | `#98a2b3` |

```tsx
import Prism from "prismjs";
import "prismjs/plugins/line-numbers/prism-line-numbers";
import { prismLanguageImports } from "@/lib/editor-theme";

useEffect(() => {
  prismLanguageImports.forEach((path) => import(path));
  if (codeRef.current) Prism.highlightElement(codeRef.current);
}, [code, language]);
```

## Line Numbers

- `showLineNumbers` → pre 加 `line-numbers` class
- `padding-left: 2.8em`；行号区 `border-right: 0`

## Languages

默认导入：`jsx`、`tsx`、`typescript`、`bash`、`json`、`css`、`scss`、`markdown`。

## CSS Overrides

```ts
import { prismCssOverrides } from "@/lib/editor-theme";
// append to host index.css
```

- `text-shadow: none` on code/pre
- `white-space: pre-wrap; word-wrap: break-word`
- dark `[data-theme="dark"] .language-html` → `#171f2e` 背景

## Data States

| 状态 | 模式 |
|---|---|
| loading | Body 内 `Skeleton` 行 + `aria-busy="true"` |
| empty | 居中文案「No code generated yet」 |
| error | `Alert variant="error"` 替换代码区 |

## 工程约束

- 按需 `import` prism 语言组件，避免打包全部语法
- `Prism.highlightElement` 在 `useEffect` 中调用（客户端）
- 与 `Textarea` 输入区分离：Editor shard 专用于**只读高亮展示**；可编辑场景用 **`CodeEditor`**（`templates/ui/code-editor.tsx`）或 `AiCodeGeneratorShell`
- 可编辑规则详见 `references/layout-patterns/code-editor-editable.md`

## 与 third-party-template 关系

`third-party-template.md#editor` 保留简要入口；本 shard 为 Prism 代码块深化参考。
