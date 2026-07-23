# SwarmCore UI 规范

本文是 SwarmCore Web 的项目级视觉与交互约束。它替代仓库内通用的
`b-design-system-tailadmin-radix` Skill；实现代码和本文件共同构成当前事实来源。

## 技术边界

- React 19、TypeScript、Vite、React Router v7。
- Tailwind CSS v4；Token 定义在 `apps/web/src/index.css`。
- 组件优先使用现有 `apps/web/src/components/ui/` 实现。
- Dialog、Tooltip 等浮层使用 Radix，图标使用 `lucide-react`。
- 类名只通过 `cn()` 合并；多变体组件使用 `cva`。

## 视觉基线

- 视觉来源为 TailAdmin React Pro v2.3.1，但不复制或 vendoring 上游代码。
- 主色为 `brand-500`（`#465fff`）；业务组件使用语义 Token，不新增硬编码颜色。
- 字体使用 Outfit，表单控件默认 `h-11 rounded-lg`。
- 页面背景使用低对比度品牌光晕；卡片使用 `shadow-theme-card`，主操作浮层使用
  `shadow-theme-float`，避免页面各自定义阴影。
- 桌面侧栏宽度为 290px，折叠宽度为 90px；主内容最大宽度使用
  `--breakpoint-2xl`。
- 浮层使用 `z-99999`；键盘焦点使用可见的 `focus-visible:ring-3`。
- dark mode 由根节点 `.dark` 类控制，新增界面必须同时覆盖明暗主题。

## 组件与交互

- 新页面先复用 Button、Card、Badge、Skeleton 和 StatusBadge。
- 主导航按总览、业务工作、执行管理、平台底座、系统治理、系统观测分组；业务能力包
  归入业务工作，能力目录及智能体、工具、模型配置归入平台底座。
  具体业务不硬编码为一级导航；从业务能力包列表进入项目配置页或已启用能力包的独立工作台。
  新建 Run、待办处理和编排画布必须保持一级可达，外部观测入口明确标识为新窗口打开。
- 新增通用组件时放入 `apps/web/src/components/ui/`，同时补充相邻测试。
- 禁止手写 Modal、Popover、Dropdown 的点击外部关闭和焦点管理。
- 异步页面必须明确处理 loading、empty、error、partial、stale 和 retry。
- Run 状态必须复用 `StatusBadge` 的状态映射，避免页面各自定义颜色。
- Run 实时更新必须覆盖 SSE reconnect、gap、backpressure 和 410 cursor expired。

## 验收

- 运行 `pnpm web:lint`、`pnpm web:test` 和 `pnpm web:build`。
- 核心交互变化运行 `pnpm web:e2e`。
- 通过浏览器检查 desktop、tablet、mobile 的 light/dark 视口。
- 不允许大面积无意义空白、内容列过窄、文字裁切、控件重叠或横向溢出。
- Dialog、Tooltip、侧栏和策略画布必须可用键盘操作，且焦点清晰可见。

若新增框架级 Token、组件契约或布局规则，同步更新本文和相关实现；不在仓库中
重新引入通用模板库、图标全集或组合式评审清单。
