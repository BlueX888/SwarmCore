# 布局模式 — BI 过滤器与联动分析

典型路由：`/bi/dashboards/:id/view`、`/bi/explore`

关联：`bi-dashboard-builder.md`、`templates/bi/filter-bar.tsx`、`templates/bi/cross-filter-dashboard.tsx`

## 适用场景

- 仪表盘全局筛选：日期、区域、渠道、产品线
- 单图局部筛选：仅影响当前 ChartPanel
- Cross-filter：点击图表扇区/柱子联动其他图表与高亮 chips
- 级联筛选：省 → 市 → 门店

## 筛选层级与优先级

| 层级 | 作用域 | 清除规则 | 典型控件 |
|---|---|---|---|
| Global | 整个仪表盘/页面 | 「清除全部」重置 global + 派生的 local/cross | FilterBar scope=global |
| Local | 单个 ChartPanel / Widget | 卡片内「重置筛选」仅清 local | FilterBar scope=local |
| Cross-filter | 由图表点击产生 | 点击 chip × 或「清除联动」 | FilterChip source=chart |

**优先级（高 → 低）**：Global > Cross-filter > Local

- Global 变更时，清除所有 cross-filter，local 保留默认值或随 global 重算。
- Cross-filter 不覆盖 global 已锁定的维度。
- Local 不得反向修改 global 状态。

## 结构

```tsx
<CrossFilterDashboard
  globalFilters={global}
  onGlobalFiltersChange={setGlobal}
  crossFilters={cross}
  onCrossFiltersChange={setCross}
  widgets={widgets}
  renderWidget={(w) => <ChartPanel … />}
/>
```

或组合式：

```tsx
<FilterBar
  scope="global"
  filters={filterDefs}
  values={values}
  onChange={setValues}
  onClearAll={clearAll}
/>
<DashboardGrid … />
```

## 筛选类型

| 类型 | 控件 | 说明 |
|---|---|---|
| 日期范围 | DateRangePicker | 绝对起止日期 |
| 相对时间 | Select + presets | 近 7 天 / 近 30 天 / 本月 / 本季度 |
| 枚举单选 | Select | 区域、状态、环境 |
| 多选 | MultiSelect | 渠道、产品线、标签 |
| 级联 | 联动 Select | 省市区、组织树 |
| 搜索 | Combobox / Command | 数据集、指标名 |

## 联动状态可见性

- 每个生效筛选渲染为 `FilterChip`：标签 + 值 + 来源（全局/局部/图表联动）
- Cross-filter chip 带来源图表名，如「区域 = 华东 ← 收入趋势图」
- 至少提供：单 chip 清除、清除联动、清除全部
- 口径变更（BI-002）导致图表待刷新时，FilterBar 旁显示「筛选已变更，部分图表待更新」

## 清除入口

1. 单 chip `×` — 移除该项筛选
2. 「清除联动」— 仅移除 cross-filter
3. 「清除全部」— global + cross + local 恢复默认
4. 图表再次点击同一扇区 — toggle 取消 cross-filter

## 视觉规则

- FilterBar sticky 在仪表盘工具栏下，`z-10`，`flex-wrap gap-2`
- chips 使用 `Badge` outline 变体，cross-filter 左侧小色点区分来源
- 移动端：FilterBar 收起到「筛选 (N)」按钮，打开 bottom Sheet
- 空结果：图表区 `ContentState`「当前筛选无数据」+ 建议放宽筛选

## 选型（decision-matrix）

| 意图 | 使用 | 不要用 |
|---|---|---|
| 仪表盘顶栏全局筛选 | `FilterBar` scope=global | 每个图表各自放一套日期选择 |
| 单图额外筛选 | `FilterBar` scope=local 内嵌 ChartPanel actions | 重复 global 日期控件 |
| 点击柱子筛选其他图 | `CrossFilterDashboard` + chips | 手写 onClick 无清除路径 |
| 明细表筛选 | `DataTableCard` toolbar 筛选 | BI FilterBar 直搬 |

## 截图验收

- global FilterBar + 至少 2 个 active chips
- cross-filter 点击后第二图表高亮 + chip 出现
- 清除联动后图表恢复
- light/dark 下 chip 与 sticky bar 可读
