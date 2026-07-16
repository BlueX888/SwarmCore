# 视觉语言 — TailAdmin

从 **TailAdmin React Pro v2.3.1** 抽取并内化的稳定视觉规则。实现时使用 shadcn/Radix + Tailwind v4 语义 Token。

## 设计气质

- **产品类型**：B2B SaaS 管理后台、电商运营、CRM、物流、AI 工作台
- **视觉关键词**：干净、专业、数据密集、蓝紫品牌色、柔和阴影、圆角友好
- **信息密度**：中高 — 表格/指标卡/图表并存，单屏信息量大但留白克制
- **品牌表达**：`brand-500` (#465fff) 主色；Outfit 字体；浅色底 `gray-50`，暗色底 `gray-900`/`gray-dark`
- **禁止方向**：霓虹渐变、玻璃拟态过重、营销页大留白、非品牌色系主操作

## 比例

| 对象 | 规则 | 证据 |
|---|---|---|
| 页面壳 | `min-h-screen`；主列 `flex-1`；侧栏 fixed | `layout/AppLayout.tsx` |
| 顶栏 | sticky `top-0`；高度随内容；`z-99999` | `layout/AppHeader.tsx` |
| 侧栏 | 展开 `w-[290px]`；折叠 `w-[90px]`；hover 临时展开 | `layout/AppSidebar.tsx` |
| 内容区 | `max-w-(--breakpoint-2xl)`；`p-4 md:p-6`；`pb-20 md:pb-24` | `AppLayout.tsx` |
| 卡片/面板 | `rounded-xl` 外框 + `border-gray-200`；暗色 `dark:border-white/[0.05]` | `common/ComponentCard.tsx` |
| 控件 | 输入 `h-11`；按钮 `py-3.5`/`py-3`；Badge `py-0.5` | `form/input/InputField.tsx` |
| 图标 | 导航 `size-6`；按钮内 `size-5`；顶栏 `size-5`/`size-6` | `index.css` menu-item-icon |

## 密度

- **表格行高**：cell `py-4`；header `py-3`；`text-theme-sm` / `text-theme-xs`
- **表单控件高度**：`h-11`（44px）
- **toolbar 高度**：与按钮 `md` 尺寸对齐（约 44–48px）
- **卡片 padding**：`p-5` 或 `p-6`（ComponentCard 模式）
- **区块间距**：页面内 `gap-6`；栅格指标卡 `gap-4`/`gap-6`
- **文本层级**：页面标题 `text-title-sm`/`text-xl`；正文 `text-theme-sm`；辅助 `text-theme-xs text-gray-500`

## 语义色

| 语义 | Token | 典型用法 |
|---|---|---|
| 主操作 | `brand-500` → hover `brand-600` | Button primary、链接、选中导航 |
| 次操作 | `white` + `ring-gray-300` outline | Button outline |
| 成功 | `success-500` / `success-50` 底（暗色 `success-500/15` + `success-500/30` 边框） | Badge、Alert、校验通过 |
| 警告 | `warning-500` / `warning-50`（暗色 `warning-500/15`） | Badge、Alert |
| 危险 | `error-500` / `error-50`（暗色 `error-500/15`） | 校验错误、破坏性操作 |
| 禁用 | `opacity-40`–`opacity-50` + `cursor-not-allowed` | Input、Button |
| 选中 | `bg-brand-50 text-brand-500`（暗色 `brand-500/12` + `brand-400` 字） | 侧栏 menu-item-active、Tab enclosed |
| 信息/中性 | `blue-light-500` 或 `gray-500` | info Badge、辅助文案 |

点缀色：`theme-pink-500` (#ee46bc)、`theme-purple-500` (#7a5af8) — 仅图表/AI 模块点缀，不作主 CTA。

## 圆角与阴影

- **圆角**：控件 `rounded-lg`；面板 `rounded-xl`；Modal `rounded-3xl`；Badge/Avatar `rounded-full`
- **阴影**：控件 `shadow-theme-xs`；下拉 `shadow-theme-lg`；卡片 `shadow-theme-sm`–`md`
- **焦点环**：`focus:ring-3 focus:ring-brand-500/20`（Input）；全局 token `shadow-focus-ring`

## 逻辑美学

- **动作放置**：页面标题行右侧放主/次操作；表格 toolbar 左筛选右操作
- **数据层级**：指标卡 → 图表 → 明细表；数字用 `font-semibold`/`text-title-sm`
- **空态/错误/权限**：居中插画 + 简短文案 + 单一恢复动作；错误页独立全屏路由
- **破坏性流程**：outline/error 色按钮 + Dialog 二次确认
- **批量操作**：表格上方 toolbar；选中行后显示浮动操作条

## 反模式

- 在页面内写 `#465fff` 或 `rgb()` 而非 `brand-500`
- 使用 `z-50` 等默认 Tailwind z-index 覆盖 Modal（应用 `z-99999`）
- Button 无 `focus-visible` 环（源项目缺陷，shadcn 实现必须补齐）
- 侧栏导航不用 `menu-item` 语义类，导致选中/hover 不一致
- 暗色模式仅改背景不改边框（需 `dark:border-gray-800` 或 `dark:border-white/[0.05]`）
- 暗色模式仍用 `*-50` 实色作 Alert/Badge 底（应改为 `dark:bg-*-500/15` + `dark:border-*-500/30`）
- 暗色模式仍用 `brand-50` / `gray-100` 作选中态、Skeleton、Progress 轨道（应改为 `brand-500/12`、`gray-800`）
