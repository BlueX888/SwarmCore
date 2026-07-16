# Gateway 视觉规范 — DeepTalk 双端 × TailAdmin

```yaml
scope: deeptalk-gateway（SaaS）+ deeptalk-gateway-tob（企业内网）
base_ref: visual-language.md
demand_ref: ../../docs/demand/gateway.md
last_updated: 2026-06-25
```

> **DeepTalk Gateway 双端**采用 TailAdmin 时的视觉落地规则。基础 Token 与比例以 [`visual-language.md`](./visual-language.md) 为准；本文只写 **Gateway 差异与 override**。  
> 场景与能力缺口见 [`docs/demand/gateway.md`](../../docs/demand/gateway.md)。

---

## 1. 气质定位（双端对照）

| 端 | 采纳 TailAdmin | 克制 / 覆盖 |
|----|----------------|-------------|
| **SaaS** | 干净、专业、数据密集；`brand-*` 主色；指标卡 + 图表 | **不要**电商首页式 hero、大留白、促销渐变；运营后台 ≠ 落地页 |
| **ToB** | 同上；侧栏 + 顶栏壳层比例可沿用 TailAdmin | **不要**营销模块、AI 生成器装饰；强调 **管控台** 与 **状态可读** |
| **双端共性** | 实心卡片、柔和阴影、`rounded-xl` 面板 | **禁止**玻璃拟态铺满、霓虹渐变、装饰性 3D 图标块（门户式 dashboard） |

---

## 2. 布局与密度

| 元素 | TailAdmin 默认 | Gateway 建议 |
|------|----------------|--------------|
| 侧栏 | 展开 290px / 折叠 90px | **沿用**；ToB 8 项 Hub 分组导航信息密度与 TailAdmin 侧栏一致 |
| 顶栏 | sticky，z 高层级 | **沿用**；双端顶栏放：主题切换、角色切换（用户中心↔管理后台）、全局告警入口 |
| 内容区宽度 | `max-w-(--breakpoint-2xl)` 居中 | **SaaS Master-Detail 页**：全高链路 `min-h-0`，详情区可宽；**ToB 列表 Hub**：**全宽**，取消页面级 `max-w-3xl/5xl` |
| 页面内边距 | `p-4 md:p-6` | **对齐宿主**：SaaS `PageShell p-6 space-y-6`；ToB 内容区 `gap-6`（24px） |
| 模块间距 | `gap-6` | KPI 行 `gap-4`；Hub 内 SectionCard 之间 `gap-6` |

---

## 3. 壳层与表面

| 场景 | 视觉规则 |
|------|----------|
| **Master-Detail（SaaS）** | 页面灰底 `bg-muted/30`（或等价语义底）；列表与详情均为 **白/卡片色实心面板** `bg-card` + `border-border`；禁止详情区与列表区视觉层级混淆 |
| **Hub 页（双端）** | `PageHeader` 下直接 `PageTabs`；Tab 内容区统一卡片化 Section，**无** Tab 内再套一层无意义大留白 |
| **表格列表** | `DataTableCard`：**表头贴顶**（flush，`p-0` 内容区）；表头行 `bg-muted`；行 hover `bg-muted/50`；禁止表格外再套独立粗边框造成「双层表头」 |
| **激活/登录（ToB）** | `AuthShell` 居中 Card；单卡宽度适中（约 `max-w-lg`）；模式说明用 `muted` 辅助文案，不用插画 hero |

---

## 4. 色彩与语义状态

在 TailAdmin `brand/success/warning/error` 之上，Gateway 须固化 **业务语义色**（Badge / Alert / 边框）：

| 语义 | 视觉 | 典型场景 |
|------|------|----------|
| **健康 / 就绪** | `success` 浅底 + 深字 Badge | Endpoint ready、同步 ok、实例 online |
| **降级 / 未知** | `warning` 或中性 `muted` Badge | 实例 unknown、探测 skipped、同步 stale |
| **失败 / 冻结** | `destructive` 浅底 Alert 或 Badge | sync error、QUOTA_FROZEN、probe failed、License 过期 |
| **信息 / 引导** | `info` 或 `primary` 浅底 `AlertBanner` | connected 用量不出内网、airgap 零出站说明 |
| **版本 / edition** | 独立 tier 色（professional/enterprise）| License 能力门控横幅，不与 error 混用 |

### 数值展示

- 金额：统一 **元**（`balance_cents / 100`），表格与 KPI 用 `tabular-nums`
- 大数：禁止 JS `Number` 丢精度；超长用字符串 + 不换行截断 + Tooltip
- 标识符：`instance_id`、`customer_id`、Key 前缀用 `font-mono text-xs`

---

## 5. 字体与层级

| 层级 | 建议 |
|------|------|
| 页面标题 | `text-xl font-semibold` 或 TailAdmin `text-title-sm` |
| Section 标题 | `text-base font-medium` |
| 表格 / 表单正文 | `text-sm` |
| 辅助 / 时间戳 | `text-xs text-muted-foreground` |
| 禁止 | 同屏超过 3 级跳变的字号；KPI 数字不必大到营销屏程度 |

字体族：若宿主已用系统 sans（shadcn base-nova），**不强制** TailAdmin 源项目 Outfit；但须保持全站单一 sans 栈。

---

## 6. 图表与数据可视化

| 规则 | 说明 |
|------|------|
| 仪表盘 | KPI 行 → 趋势图 → 明细表；图表高度固定（如 `h-64`），避免撑破首屏 |
| 配色 | 主系列 `brand`；多系列用 TailAdmin 点缀色 **仅图表内** |
| 空数据 | 图表区用 compact EmptyState，不用假数据占位 |
| SaaS 供应商指标 | 可用 sparkline；与 Master-Detail 详情 Tab 对齐 |

---

## 7. 暗色模式

- 沿用 TailAdmin：`html.dark` + 边框 `dark:border-white/[0.05]` 或语义 `border-border`
- Gateway 金样须验收：**表格行 hover、Badge 浅底、AlertBanner、侧栏选中态** 在暗色下仍可分辨
- P0 页截图验收须 **light + dark 各一帧**

---

## 8. 视觉反模式（Gateway 专用）

| 禁止 | 原因 |
|------|------|
| 页面级营销 hero + 3D 大图标 | 与 IT 管控台气质冲突 |
| 列表页 `max-w-3xl` 居中 | 浪费横向空间，表格列被迫挤压 |
| 硬编码 hex / Tailwind 默认色板（`text-blue-500`） | 破坏 Token 体系 |
| 玻璃卡片铺满主内容 | 降低政企场景可读性与打印/录屏清晰度 |
| 状态仅用颜色无文案 | 色弱与暗色下不可访问；须 Badge 文案或 icon+text |

---

## 相关文档

| 文档 | 用途 |
|------|------|
| [`visual-language.md`](./visual-language.md) | TailAdmin 基础视觉 |
| [`token-index.md`](./token-index.md) | 语义 Token |
| [`gateway-interaction.md`](./gateway-interaction.md) | Gateway 交互规范 |
| [`domain-scenarios.md`](./domain-scenarios.md) | 业务场景索引 |
| [`../../docs/demand/gateway.md`](../../docs/demand/gateway.md) | 双端需求与 Gateway Pack |
