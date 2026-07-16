# Gateway 交互规范 — DeepTalk 双端 × TailAdmin

```yaml
scope: deeptalk-gateway（SaaS）+ deeptalk-gateway-tob（企业内网）
base_ref: interaction-motion.md
demand_ref: ../../docs/demand/gateway.md
last_updated: 2026-06-25
```

> **DeepTalk Gateway 双端**交互行为与状态机。基础动效见 [`interaction-motion.md`](./interaction-motion.md)；状态索引见 [`state-index.md`](./state-index.md)。  
> 场景与能力缺口见 [`docs/demand/gateway.md`](../../docs/demand/gateway.md)。

---

## 1. 导航与信息架构

| 模式 | 交互规则 |
|------|----------|
| **Hub + Tab** | Tab 与 URL `?tab=` **双向同步**；刷新/分享链接保持 Tab；非法 tab 回退默认 tab |
| **侧栏 Hub 分组** | 折叠组记忆展开态（可选）；当前路由高亮父级 Hub |
| **双 Layout 切换** | ToB：个人中心 ↔ 管理后台 **整页切换**，非弹层；切换后侧栏树完全更换 |
| **深链** | 错误 hint、空态 action 须链到 **具体 Hub Tab**（如 `/admin/settings?tab=sync`） |
| **面包屑** | Master-Detail 深页（SaaS）可选：供应商列表 → 供应商名 → Tab |

---

## 2. 数据加载三态（强制）

```
主 query:
  loading  → 整页 skeleton（保留 PageHeader 结构）
  error    → QueryErrorBlock +「重试」
  success  → 正常内容

次级块（卡片内）:
  error    → 块内 QueryErrorBlock，不拖垮整页
  empty    → EmptyState（带可选主操作）
  pending  → opacity-70 + aria-busy（refetch 中）

KPI:
  值为 0  → 显示 0 或 —，不用 EmptyState
```

**禁止**：裸「加载中…」、页面级红色 `<p>` 错误、无重试的数据失败。

---

## 3. 表单与向导

| 场景 | 交互 |
|------|------|
| **ToB 激活向导** | 步骤条 + 部署模式 **单选后不可改**（二次确认文案）；connected 与 airgap **分支表单**不同字段集 |
| **License 签发（SaaS）** | 提交 → 结果区 **可复制** license 字符串 → 明确「仅展示一次」 |
| **License 续期（ToB）** | 粘贴 → 验签结果 toast；airgap 过期时 **全站守卫** 仅允许续期 Tab 可写 |
| **表单提交** | 提交中按钮 disabled + loading；字段错误贴控件、`aria-invalid`；**字段错误不用 toast** |
| **筛选** | 列表筛选用 shadcn Select/Input；搜索 debounce **300ms**（SaaS 约定） |

---

## 4. 表格与行级操作

| 场景 | 交互 |
|------|------|
| **行操作** | 主操作 ≤2 个外露；其余收进 `DropdownMenu` |
| **Endpoint 探测（ToB）** | 行级触发；**300ms debounce** 防连点；结果 Badge 三态 + tooltip 排障摘要 |
| **批量操作** | 多选后显示 toolbar；破坏性批量走 DangerZone |
| **分页** | 底栏「共 N 条」+ 翻页；加载下一页时表格 pending，不闪空 |
| **导出（审计）** | 导出中按钮 `aria-busy` + 文案「导出中…」；大数据 CSV 异步 |

---

## 5. 同步、配额与运维态（ToB connected）

**同步四轨**（quota / report / HMAC / heartbeat）每轨独立一行：

| 状态 | 展示 | 操作 |
|------|------|------|
| ok | 绿色语义 + 上次成功时间 | 可选「立即同步」 |
| pending / 首次 | 中性文案「等待首次同步」 | — |
| error | 中文可行动 hint + 最后错误摘要（脱敏） | 「重试」；手动同步 **防重复提交** |
| frozen | 全局 `AlertBanner` destructive | 链到 sync Tab 排障 |

**配额**

- connected：池余额变更后 invalidate 仪表盘 + 配额相关 query
- airgap：不出现「同步」「企业池」类操作按钮

---

## 6. 密钥与危险操作

| 场景 | 交互 |
|------|------|
| **API Key 创建** | 成功弹层/区域 **一次性** 展示 `raw_key` → 复制按钮 + 复制反馈 → 关闭后不可再查 |
| **撤销 Key / 删 Endpoint** | `AlertDialog`：须展示对象名；确认按钮 destructive |
| **充值 / 扣减（SaaS）** | 金额确认二次摘要；审批流状态不可跳过 |
| **探测 / 同步失败** | toast 仅作补充；**主排障**在区块内 hint + 深链 |

---

## 7. 反馈层级（避免打架）

优先级从高到低：

1. **路由守卫**（未激活 / 强制改密 / airgap License 过期）— 整页或重定向
2. **Layout 级横幅**（License 即将过期、池冻结）
3. **PageHeader 下 AlertBanner**（页级告警）
4. **块内 QueryErrorBlock / EmptyState**
5. **toast**（操作成功/轻量失败）

同屏避免：全局横幅 + 页内 Alert + toast 重复同一错误文案。

---

## 8. 动效与可访问性

| 项 | 建议 |
|----|------|
| 侧栏折叠 | 300ms ease-in-out（与 TailAdmin 一致） |
| 浮层 | Dialog/Sheet 150ms 级进入；支持 ESC 关闭 |
| 焦点 | Dialog 打开焦点陷阱；关闭后焦点回触发按钮 |
| 减少动效 | 尊重 `prefers-reduced-motion`；骨架优先于 spinner |
| 图标按钮 | 必须有 `aria-label` 或可见 tooltip |

---

## 9. 文案与错误交互

| 规则 | 示例 |
|------|------|
| 语言 | 面向 IT/运维：**简体中文** |
| 结构 | 结果 + 原因 + 下一步（链到设置 Tab） |
| 机器码 | 内部逻辑可用 `MACHINE_CODE`；用户可见句不含英文堆栈 |
| 空态 | 「暂无 Chat Endpoint」+ 按钮「添加 Endpoint」 |
| 成功 | toast 简短；关键成功（Key 创建）用 **内联面板** 而非仅 toast |

> 完整文案表待 `copy-patterns.md`、`error-mapping.md`（Gateway Pack 后续条目）。

---

## 10. P0 页交互验收清单

实施或 preview 金样时，每页至少走一遍：

- [ ] 主 query loading / error / empty 三态可触发且可恢复
- [ ] Tab URL 可分享、刷新保持
- [ ] connected / airgap（ToB）分叉无错按钮露出
- [ ] 危险操作有二次确认且含对象名
- [ ] Key 一次性展示闭环
- [ ] 同步/探测失败有可行动中文 hint
- [ ] 键盘：Tab 可达主操作；Dialog ESC 可关
- [ ] light / dark 下状态色可区分

---

## 相关文档

| 文档 | 用途 |
|------|------|
| [`interaction-motion.md`](./interaction-motion.md) | TailAdmin 动效基线 |
| [`state-index.md`](./state-index.md) | 组件状态覆盖 |
| [`gateway-visual.md`](./gateway-visual.md) | Gateway 视觉规范 |
| [`domain-scenarios.md`](./domain-scenarios.md) | 业务场景索引 |
| [`../../docs/demand/gateway.md`](../../docs/demand/gateway.md) | 双端需求与 Gateway Pack |
