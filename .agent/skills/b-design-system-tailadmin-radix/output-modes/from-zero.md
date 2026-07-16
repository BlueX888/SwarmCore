# 从 0 构建模式

技术栈：**React 19 + Vite + react-router v7 + shadcn/ui + Radix + Tailwind v4**

## 读取顺序

1. `references/engineering-guards.md` — 初始化 shadcn 与目录
2. `references/token-index.md` — 复制 `@theme` 到 `index.css`
3. `references/visual-language.md` — 壳层比例
4. `references/pattern-index.md` — 选页面模式
5. `references/component-index.md` — 选组件
6. `references/state-index.md` — 状态覆盖

## 脚手架步骤

```bash
npm create vite@latest my-app -- --template react-ts
cd my-app && npm i tailwindcss @tailwindcss/postcss @tailwindcss/forms
npm i clsx tailwind-merge class-variance-authority @radix-ui/react-slot
npx shadcn@latest init
```

1. 复制 Skill `templates/components.json`、`templates/lib/utils.ts` 到项目
2. 将 TailAdmin `@theme` 色板写入 `src/index.css`（见 `references/token-index.md`）
3. 复制 `@utility menu-*` 到同文件
4. `npx shadcn@latest add button input ...` 后覆盖 `button.tsx` 为 `templates/ui/button.tsx`
5. 实现 `ThemeContext` + `SidebarContext`
6. 实现 `AppLayout` / `AppSidebar` / `AppHeader`

## 工作流

1. 明确路由与数据形态
2. 选 `layout-patterns/*.md`
3. 从 `component-index` 拉 shadcn 组件
4. 语义 Token 组装 UI
5. 实现 loading/empty/error/disabled/focus/dark/responsive
6. 对照 `visual-language.md` 做密度检查
7. 业务仓库首次接入时，按 `references/adoption-onboarding-checklist.md` ADOPT-01～06 验收；copy 模式后续改动按 `references/upstream-contribution-guide.md` 登记 `docs/design-system-upstream.md`

## 避免

- 跳过 shadcn 直接复制 TailAdmin 手写 Modal/Dropdown
- 硬编码 hex 色值
- 营销页构图用于后台任务界面
- 未索引的一次性组件
