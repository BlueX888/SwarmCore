# Token 索引 — TailAdmin × Tailwind v4

所有 Token 定义在宿主项目 `src/index.css` 的 `@theme` 块。shadcn 主题应映射到相同 CSS 变量。

## 颜色

### 品牌色 brand-*

| Token | 值 | 用途 |
|---|---|---|
| `brand-500` | `#465fff` | 主 CTA、选中态、焦点环基色 |
| `brand-600` | `#3641f5` | primary hover |
| `brand-50` | `#ecf3ff` | 选中背景（浅） |
| `brand-300` | `#9cb9ff` | focus border |
| `brand-400` | `#7592ff` | 暗色选中文字 |

### 中性色 gray-*

| Token | 用途 |
|---|---|
| `gray-50` | 页面背景 `bg-gray-50` |
| `gray-100`–`gray-200` | hover 背景、分隔线 |
| `gray-300`–`gray-400` | 边框、placeholder |
| `gray-500`–`gray-700` | 辅助/正文文字 |
| `gray-800`–`gray-900` | 暗色背景、标题 |
| `gray-dark` | `#1a2231` 下拉/面板暗色底 |

### 语义色

| 族 | 500 值 | 用途 |
|---|---|---|
| `success-*` | `#12b76a` | 成功、增长、通过 |
| `error-*` | `#f04438` | 错误、危险、校验失败 |
| `warning-*` | `#f79009` | 警告、待处理 |
| `blue-light-*` | `#0ba5ec` | 信息、info Badge |
| `orange-*` | `#fb6514` | 强调（少用） |

### 点缀

- `theme-pink-500`: `#ee46bc`
- `theme-purple-500`: `#7a5af8`

## 字体

| Token | 值 |
|---|---|
| `font-outfit` | Outfit, sans-serif |
| `text-title-sm` | 30px / lh 38px |
| `text-title-md` | 36px / lh 44px |
| `text-theme-xl` | 20px / lh 30px |
| `text-theme-sm` | 14px / lh 20px |
| `text-theme-xs` | 12px / lh 18px |

body 默认：`font-outfit font-normal bg-gray-50`

## 阴影

| Token | 场景 |
|---|---|
| `shadow-theme-xs` | Button、Input |
| `shadow-theme-sm` | 卡片、图表 tooltip |
| `shadow-theme-md` | 浮起卡片 |
| `shadow-theme-lg` | Dropdown、Popover |
| `shadow-theme-xl` | Modal 邻近层 |
| `shadow-focus-ring` | `0 0 0 4px rgba(70,95,255,0.12)` |

## 圆角（Tailwind 默认 scale）

| 类 | 场景 |
|---|---|
| `rounded-lg` | Button、Input、Alert、menu-item |
| `rounded-xl` | Table 容器、Dropdown 面板 |
| `rounded-2xl` | 用户菜单大面板 |
| `rounded-3xl` | Dialog 内容 |
| `rounded-full` | Badge、Avatar、关闭按钮 |

## 间距节奏

| 场景 | 类 |
|---|---|
| 控件水平内边距 | `px-4`（sm）/ `px-5`（md） |
| 控件垂直 | `py-2.5`（input）/ `py-3`–`py-3.5`（button） |
| 表格 cell | `px-5 py-4` |
| 表格 header | `px-5 py-3` |
| 页面 padding | `p-4 md:p-6` |
| 栅格 gap | `gap-4`、`gap-6` |

## Z-index

| Token | 值 | 场景 |
|---|---|---|
| `z-1` | 1 | body 基线 |
| `z-40` | — | 移动端 Backdrop |
| `z-999` | — | Modal 关闭按钮 |
| `z-9999` | — | Dropdown |
| `z-99999` | — | Header、Modal overlay |

## 断点

`2xsm` 375 · `xsm` 425 · `sm` 640 · `md` 768 · `lg` 1024 · `xl` 1280 · `2xl` 1536 · `3xl` 2000

侧栏 margin 切换：`xl:ml-[290px]` / `xl:ml-[90px]`

## @utility 导航（复制到 globals.css）

- `menu-item`、`menu-item-active`、`menu-item-inactive`
- `menu-item-icon`、`menu-item-icon-active`、`menu-item-icon-inactive`
- `menu-dropdown-item`、`menu-dropdown-item-active`、`menu-dropdown-item-inactive`
- `menu-dropdown-badge`、`menu-dropdown-badge-pro`（及 active/inactive 变体）
- `no-scrollbar`、`custom-scrollbar`

## shadcn CSS 变量映射建议

```css
@theme inline {
  --color-primary: var(--color-brand-500);
  --color-primary-foreground: var(--color-white);
  --color-muted: var(--color-gray-100);
  --color-muted-foreground: var(--color-gray-500);
  --color-border: var(--color-gray-200);
  --color-ring: var(--color-brand-500);
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
}
```

## 检索别名

| 意图 | 首选 Token |
|---|---|
| 主按钮背景 | `bg-brand-500` |
| 页面底 | `bg-gray-50` / `dark:bg-gray-900` |
| 卡片边框 | `border-gray-200` / `dark:border-white/[0.05]` |
| 正文 | `text-gray-800` / `dark:text-white/90` |
| 辅助文字 | `text-gray-500` / `dark:text-gray-400` |
| 错误边框 | `border-error-500` |
| 成功边框 | `border-success-500` |
