# 布局模式 — 可编辑代码编辑器

典型路由：`/code-generator`、`/devops/snippets/:id/edit`、`/support/tickets/:id/code`

关联：`editor-theme.md`、`templates/ui/code-block.tsx`、`templates/ui/code-editor.tsx`、`templates/devops/ai-code-generator-shell.tsx`

## 适用场景

- **AI 代码生成**：自然语言提示 → 生成代码 → 用户继续编辑
- **工单/支持片段**：客服或运维编辑脚本、配置片段后预览高亮
- **DevOps 模板编辑**：Pipeline YAML、Helm values、Shell 脚本在线修改
- **只读 vs 可编辑**：展示用 `CodeBlock`；需要用户改内容用 `CodeEditor`

## 组件分工

| 组件 | 用途 | 何时使用 |
|---|---|---|
| `CodeBlock` | Prism 只读高亮 | 日志、生成结果展示、复制/编辑入口 |
| `CodeEditor` | Textarea + 实时预览 | 用户需要改代码并看高亮 |
| `AiCodeGeneratorShell` | 提示词 + CodeEditor 页面组合 | `/code-generator` 类整页 |

## CodeEditor 能力

| 能力 | 说明 |
|---|---|
| 分屏模式 | `split` / `edit` / `preview` 三态切换 |
| 语言选择 | `supportedPrismLanguages` 下拉 |
| 实时预览 | 右侧 `CodeBlock` 随 `value` 更新 |
| 脏状态 | `dirty` badge「未保存」 |
| 语法错误 | `error` 展示在编辑区底部 + destructive badge |
| 保存/复制 | `onSave`、`onCopy` 回调；保存按钮在 `dirty` 时启用 |

```tsx
<CodeEditor
  value={code}
  onChange={setCode}
  language={language}
  onLanguageChange={setLanguage}
  mode="split"
  onModeChange={setMode}
  dirty={dirty}
  error={syntaxError}
  onSave={handleSave}
  showLineNumbers
/>
```

## AiCodeGeneratorShell 组合

```tsx
<AiCodeGeneratorShell
  prompt={prompt}
  onPromptChange={setPrompt}
  code={code}
  onCodeChange={setCode}
  language="tsx"
  generating={generating}
  dirty={dirty}
  onGenerate={handleGenerate}
  onSave={handleSave}
  onReset={handleReset}
/>
```

## 响应式规则

| 视口 | 布局 |
|---|---|
| desktop | `split` 默认左右分屏 |
| tablet | `split` 仍可用，窄屏降为上下堆叠 |
| mobile | 默认 `edit` 或 `preview`，避免双栏挤压 |

## 状态矩阵

| 状态 | 编辑区 | 预览区 | 工具栏 |
|---|---|---|---|
| 空内容 | placeholder | empty 态 | 复制禁用 |
| 生成中 | `readOnly` + saving | loading skeleton 可选 | 生成按钮 loading |
| 语法错误 | `variant="error"` + 底部文案 | 仍展示最近可解析内容 | error badge |
| 只读审计 | `readOnly` | 正常预览 | 隐藏保存 |

## 选型规则（写回 decision-matrix）

| 业务意图 | 优先组件 | 不要使用 |
|---|---|---|
| 只读展示代码 | `CodeBlock` | `CodeEditor` |
| 用户编辑并预览 | `CodeEditor` | 两个独立 Textarea + pre |
| AI 生成整页 | `AiCodeGeneratorShell` | 手写散落 prompt + editor |
| 大段 JSON/YAML 表单 | `Textarea` + 校验提示 | CodeEditor 分屏 |

## 反例

- ❌ 用 `CodeBlock` 的 `onEdit` 跳转到空白页，却没有 `CodeEditor` 承接
- ❌ 编辑区用普通 `Input` 单行承载多行代码
- ❌ 预览区不随编辑更新，需要手动点「刷新预览」
- ❌ mobile 仍强制左右分屏导致编辑区宽度 &lt; 240px

## Preview 验收

- `preview.html#editor-editable`：textarea 输入后预览区同步更新
- 模式切换：split → edit → preview 可见布局变化
- 语言切换：TSX ↔ JSON 标签更新
- 截图：`editor-editable-*.png`、`editor-editable-split-*.png`
