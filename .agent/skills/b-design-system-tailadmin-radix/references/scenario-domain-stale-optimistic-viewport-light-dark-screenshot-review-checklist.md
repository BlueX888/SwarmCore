# Scenario Domain Stale Optimistic Viewport Light/Dark Screenshot 评审清单

> DOCS-056 / G105 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 stale/optimistic 独立截图视觉回归抽检**，确保每个场景 section 在 Stale-While-Revalidate 缓存展示、乐观更新态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md`（SDRP-01～05）、`scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md`（SDSO-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 stale/optimistic tablet/mobile light/dark 独立截图抽检 | 对应 SDSO 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标 stale/optimistic tablet/mobile light/dark golden 对照 | SDSO-01 + `scenario-bi-domain-tablet-stale.png` + `scenario-bi-domain-mobile-dark-optimistic.png` |
| DevOps 场景阶段 stale/optimistic tablet/mobile light/dark golden 对照 | SDSO-02 + `scenario-devops-domain-tablet-stale.png` + `scenario-devops-domain-mobile-dark-optimistic.png` |
| Gateway 场景端点 stale/optimistic tablet/mobile light/dark golden 对照 | SDSO-03 + `scenario-gateway-domain-tablet-stale.png` + `scenario-gateway-domain-mobile-dark-optimistic.png` |
| Governance 场景审计行 stale/optimistic tablet/mobile light/dark golden 对照 | SDSO-04 + `scenario-governance-domain-tablet-stale.png` + `scenario-governance-domain-mobile-dark-optimistic.png` |
| PaaS 场景容量 stale/optimistic tablet/mobile light/dark golden 对照 | SDSO-05 + `scenario-paas-domain-tablet-stale.png` + `scenario-paas-domain-mobile-dark-optimistic.png` |

## 通用前置

1. 先完成 `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md` SDRP-01～05（refetch/pending 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{stale,optimistic}.png` 四视口双主题 stale/optimistic 独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 stale 与一张 optimistic 独立截图；stale 必须出现缓存 banner 与同步指示器，optimistic 必须出现乐观更新 banner 与撤销 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. stale/optimistic 截图出现文案裁切、同步指示器错位、optimistic banner 对比度不足或 dark 层级丢失时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 stale/optimistic tablet/mobile light/dark 独立截图（G105）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 stale/optimistic tablet/mobile light/dark 独立截图抽检行。

## SDSO-01 — BI 场景指标 stale/optimistic tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-stale.png`、`scenario-bi-domain-tablet-dark-stale.png`、`scenario-bi-domain-mobile-stale.png`、`scenario-bi-domain-mobile-dark-stale.png`、`scenario-bi-domain-tablet-optimistic.png`、`scenario-bi-domain-tablet-dark-optimistic.png`、`scenario-bi-domain-mobile-optimistic.png`、`scenario-bi-domain-mobile-dark-optimistic.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light stale 截图 | `scenario-bi-domain-tablet-stale.png` 存在且 stale framing 正常 | SDSO-01 · RESP-06 |
| 2 | tablet dark stale 截图 | `scenario-bi-domain-tablet-dark-stale.png` 存在且同步指示器可读 | SDSO-01 · VIS-05 |
| 3 | mobile light optimistic 截图 | `scenario-bi-domain-mobile-optimistic.png` optimistic banner 首屏可见 | SDSO-01 · RESP-07 |
| 4 | mobile dark optimistic 截图 | `scenario-bi-domain-mobile-dark-optimistic.png` optimistic 对比度可辨认 | SDSO-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainStaleOptimisticViewportLightDarkScreenshots` biDomain 全过 | SDSO-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 stale 面板 → 点击「触发指标乐观更新」→ 对照 tablet/mobile light/dark 八张 stale/optimistic 截图。

## SDSO-02 — DevOps 场景阶段 stale/optimistic tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-stale.png`、`scenario-devops-domain-tablet-dark-stale.png`、`scenario-devops-domain-mobile-stale.png`、`scenario-devops-domain-mobile-dark-stale.png`、`scenario-devops-domain-tablet-optimistic.png`、`scenario-devops-domain-tablet-dark-optimistic.png`、`scenario-devops-domain-mobile-optimistic.png`、`scenario-devops-domain-mobile-dark-optimistic.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light stale 截图 | `scenario-devops-domain-tablet-stale.png` 存在且 stale framing 正常 | SDSO-02 · RESP-06 |
| 2 | tablet dark stale 截图 | `scenario-devops-domain-tablet-dark-stale.png` 存在且阶段 stale 可读 | SDSO-02 · VIS-05 |
| 3 | mobile light optimistic 截图 | `scenario-devops-domain-mobile-optimistic.png` 流水线 optimistic 首屏可见 | SDSO-02 · RESP-07 |
| 4 | mobile dark optimistic 截图 | `scenario-devops-domain-mobile-dark-optimistic.png` optimistic 对比度可辨认 | SDSO-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + stale/optimistic tablet/mobile light/dark 可见 | SDSO-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 stale 面板 → 点击「触发阶段乐观更新」→ 对照 tablet/mobile light/dark 八张截图。

## SDSO-03 — Gateway 场景端点 stale/optimistic tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-stale.png`、`scenario-gateway-domain-tablet-dark-stale.png`、`scenario-gateway-domain-mobile-stale.png`、`scenario-gateway-domain-mobile-dark-stale.png`、`scenario-gateway-domain-tablet-optimistic.png`、`scenario-gateway-domain-tablet-dark-optimistic.png`、`scenario-gateway-domain-mobile-optimistic.png`、`scenario-gateway-domain-mobile-dark-optimistic.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light stale 截图 | `scenario-gateway-domain-tablet-stale.png` 存在且 stale framing 正常 | SDSO-03 · RESP-06 |
| 2 | tablet dark stale 截图 | `scenario-gateway-domain-tablet-dark-stale.png` 存在且端点 stale 可读 | SDSO-03 · VIS-05 |
| 3 | mobile light optimistic 截图 | `scenario-gateway-domain-mobile-optimistic.png` 端点 optimistic 首屏可见 | SDSO-03 · RESP-07 |
| 4 | mobile dark optimistic 截图 | `scenario-gateway-domain-mobile-dark-optimistic.png` optimistic 层级不丢失 | SDSO-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + stale/optimistic tablet/mobile light/dark 可见 | SDSO-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 stale 面板 → 点击「触发端点乐观更新」→ 对照 tablet/mobile light/dark 八张截图。

## SDSO-04 — Governance 场景审计行 stale/optimistic tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-stale.png`、`scenario-governance-domain-tablet-dark-stale.png`、`scenario-governance-domain-mobile-stale.png`、`scenario-governance-domain-mobile-dark-stale.png`、`scenario-governance-domain-tablet-optimistic.png`、`scenario-governance-domain-tablet-dark-optimistic.png`、`scenario-governance-domain-mobile-optimistic.png`、`scenario-governance-domain-mobile-dark-optimistic.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light stale 截图 | `scenario-governance-domain-tablet-stale.png` 存在且 stale framing 正常 | SDSO-04 · RESP-06 |
| 2 | tablet dark stale 截图 | `scenario-governance-domain-tablet-dark-stale.png` 存在且审计 stale 可读 | SDSO-04 · VIS-05 |
| 3 | mobile light optimistic 截图 | `scenario-governance-domain-mobile-optimistic.png` 审计 optimistic 首屏可见 | SDSO-04 · RESP-07 |
| 4 | mobile dark optimistic 截图 | `scenario-governance-domain-mobile-dark-optimistic.png` optimistic 密度一致 | SDSO-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + stale/optimistic tablet/mobile light/dark 可见 | SDSO-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 stale 面板 → 点击「触发审计乐观更新」→ 对照 tablet/mobile light/dark 八张截图。

## SDSO-05 — PaaS 场景容量 stale/optimistic tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-stale.png`、`scenario-paas-domain-tablet-dark-stale.png`、`scenario-paas-domain-mobile-stale.png`、`scenario-paas-domain-mobile-dark-stale.png`、`scenario-paas-domain-tablet-optimistic.png`、`scenario-paas-domain-tablet-dark-optimistic.png`、`scenario-paas-domain-mobile-optimistic.png`、`scenario-paas-domain-mobile-dark-optimistic.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light stale 截图 | `scenario-paas-domain-tablet-stale.png` 存在且 stale framing 正常 | SDSO-05 · RESP-06 |
| 2 | tablet dark stale 截图 | `scenario-paas-domain-tablet-dark-stale.png` 存在且容量 stale 可读 | SDSO-05 · VIS-05 |
| 3 | mobile light optimistic 截图 | `scenario-paas-domain-mobile-optimistic.png` 容量 optimistic 首屏可见 | SDSO-05 · RESP-07 |
| 4 | mobile dark optimistic 截图 | `scenario-paas-domain-mobile-dark-optimistic.png` optimistic 列表项可辨认 | SDSO-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + stale/optimistic tablet/mobile light/dark 可见 | SDSO-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 stale 面板 → 点击「触发容量乐观更新」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md` SDSO-06～10
- refetch/pending 前置：`scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md` SDRP-01～05
- 选型表：`decision-matrix.md` G105 场景域 stale/optimistic tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDSO-01～10
- Runtime 门禁：`verifyScenarioDomainStaleOptimisticViewportLightDarkScreenshots`
