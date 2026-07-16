# DS-07 Gateway 控制面态势 — 复制说明

## 依赖

- `templates/bi/screen/` Layer0 主题 + A01–A06/A15 原子 + L1 布局壳
- `templates/gateway/*` 子面板语义（同步、端点、配额）— 本页以大屏原子重组，非嵌套 ControlPlaneHub
- `react-apexcharts` + `apexcharts`

## 复制步骤

1. 复制整个目录 `templates/scenarios/data-screen/ds-07-gateway-control-plane-situation/`
2. 复制 `templates/bi/screen/` 下 theme、atoms、layouts、`screen-shell.tsx`
3. 将 `mock-data.ts` 替换为控制面聚合 API（同步轨、端点探测、配额、调用量、告警流）

## 与 ControlPlaneHub 区别

- **Hub 页**（`control-plane-hub.tsx`）：可交互运维后台，含部署模式、License、API Key
- **态势大屏**（本页）：只读 L1 指挥台，聚焦同步成功率、端点分布、配额/API 趋势与告警 ticker

## 替换 API

| 数据块 | 建议接口 |
|--------|----------|
| KPI 带 | `/api/gateway/situation/summary` |
| 端点探测分布 | `/api/gateway/endpoints/probe-stats` |
| 四轨同步成功率 | `/api/gateway/sync/tracks/success-rate` |
| API 调用趋势 | `/api/gateway/metrics/calls?range=24h` |
| 配额消耗趋势 | `/api/gateway/quota/consumption?range=7d` |
| 告警 ticker | `/api/gateway/alerts/stream` |

## Example 路由

- section id：`showcase-ds-07`
- 模板路径：`templates/scenarios/data-screen/ds-07-gateway-control-plane-situation/index.tsx`
