# DS-02 AI 平台数据概览 — 复制说明

## 依赖

- `templates/bi/screen/` Layer0 主题 + A04/A05/A09/A10/A11 原子 + L2 布局壳
- `react-apexcharts` + `apexcharts`
- Tailwind CSS v4（`screen-tokens` 类名）

## 复制步骤

1. 复制整个目录 `templates/scenarios/data-screen/ds-02-ai-platform-overview/`
2. 复制 `templates/bi/screen/` 下 theme、atoms（含 `screen-hero-center`）、layouts（含 `l2-hero-orbit`）、`screen-shell.tsx`
3. 在业务项目中注册 ApexCharts 与 Tailwind 主题
4. 将 `mock-data.ts` 替换为 AI 平台聚合 API（会话、Token、应用、文档、模型排行）

## Provider

- 无需额外 Context；`ScreenShell` 自带时钟与刷新徽章
- 词云使用 CSS tag 云降级（`fallback="tag-cloud"`），无第三方词云库依赖

## 替换 API

| 数据块 | 建议接口 |
|--------|----------|
| 累计 Token | `/api/ai/platform/token-summary` |
| 7 日会话摘要 | `/api/ai/sessions/summary?days=7` |
| 应用占比 | `/api/ai/applications/distribution` |
| 热词云 | `/api/ai/keywords/top?limit=20` |
| 访问趋势 | `/api/ai/sessions/trend?days=7` |

## Example 路由

- section id：`showcase-ds-02`
- 模板路径：`templates/scenarios/data-screen/ds-02-ai-platform-overview/index.tsx`
