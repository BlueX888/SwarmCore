# DS-01 运维安全审计大屏 — 复制说明

## 依赖

- `templates/bi/screen/` Layer0 主题 + A01–A06 原子 + L1 布局壳
- `react-apexcharts` + `apexcharts`
- Tailwind CSS v4（`screen-tokens` 类名）

## 复制步骤

1. 复制整个目录 `templates/scenarios/data-screen/ds-01-ops-security-audit/`
2. 复制 `templates/bi/screen/` 下 theme、atoms、layouts、`screen-shell.tsx`
3. 在业务项目中注册 ApexCharts 与 Tailwind 主题
4. 将 `mock-data.ts` 替换为 API 聚合层（会话、用户、资产、审计命令）

## Provider

- 无需额外 Context；`ScreenShell` 自带时钟与刷新徽章
- 刷新状态由页面持有：`refreshStatus.state` 支持 `idle` / `refreshing` / `error`

## 替换 API

| 数据块 | 建议接口 |
|--------|----------|
| KPI 带 | `/api/audit/summary` |
| 资产活跃度 | `/api/assets/activity?days=30` |
| 用户/资产趋势 | `/api/audit/trend?range=7d` |
| 高危命令 | `/api/audit/danger-commands?limit=50` |

## Example 路由

- section id：`showcase-ds-01`
- 模板路径：`templates/scenarios/data-screen/ds-01-ops-security-audit/index.tsx`
