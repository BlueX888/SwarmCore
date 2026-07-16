# b-design-system-tailadmin-radix

从 **TailAdmin React Pro v2.3.1** 抽取的 Code Agent 设计系统 Skill，目标技术栈为 **React + shadcn/ui + Radix Primitives + Tailwind CSS v4**。

## 用途

- 按 TailAdmin 视觉语言搭建管理后台
- 将 TailAdmin 自定义组件迁移到 shadcn/Radix
- 补充缺失组件并保持一致 Token
- UI 一致性评审

## 快速开始

```text
Read b-design-system-tailadmin-radix/SKILL.md
```

按任务分流：

| 任务 | 文件 |
|---|---|
| 新建项目 | `output-modes/from-zero.md` |
| 迁移 UI | `output-modes/migration.md` |
| 缺组件 | `output-modes/missing-component.md` |
| 查 Token | `references/token-index.md` |
| 查组件 | `references/component-index.md` |

## 验收与预览

后续验收和查看统一以真实 example app 为准：

```bash
npm run dev -w examples/b-design-system-tailadmin-radix
npm run audit -w examples/b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
```

`preview.html` 已退役；不要再把静态 HTML mock 作为完成证据。

## 代码模板

复制到宿主项目：

| 文件 | 用途 |
|---|---|
| `templates/components.json` | shadcn 初始化 |
| `templates/lib/utils.ts` | `cn()` |
| `templates/ui/button.tsx` | TailAdmin Button variants |

## Spec 与演化

```text
Read docs/spec/b-design-system-tailadmin-radix/sop.md
Run the self-evolution workflow for this design system.
```

## 来源

- 页面溯源：`examples/b-design-system-tailadmin-radix/src/data/tailadminPageCatalog.ts`（92 页冻结快照，TailAdmin React Pro v2.3.1）
- 生成工具：`create-design-system` skill

## 关键 Token

- 主色：`brand-500` (#465fff)
- 字体：Outfit (`font-outfit`)
- 控件高度：`h-11`
- 侧栏：290px / 90px 折叠
