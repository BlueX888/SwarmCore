# Scenario Domain Refetch Pending Viewport Light/Dark Screenshot 评审清单

> DOCS-055 / G104 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 refetch/pending 独立截图视觉回归抽检**，确保每个场景 section 在待加载、后台刷新态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md`（SDPR-01～05）、`scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md`（SDRP-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 refetch/pending tablet/mobile light/dark 独立截图抽检 | 对应 SDRP 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标 refetch/pending tablet/mobile light/dark golden 对照 | SDRP-01 + `scenario-bi-domain-tablet-pending.png` + `scenario-bi-domain-mobile-dark-refetch.png` |
| DevOps 场景阶段 refetch/pending tablet/mobile light/dark golden 对照 | SDRP-02 + `scenario-devops-domain-tablet-pending.png` + `scenario-devops-domain-mobile-dark-refetch.png` |
| Gateway 场景端点 refetch/pending tablet/mobile light/dark golden 对照 | SDRP-03 + `scenario-gateway-domain-tablet-pending.png` + `scenario-gateway-domain-mobile-dark-refetch.png` |
| Governance 场景审计行 refetch/pending tablet/mobile light/dark golden 对照 | SDRP-04 + `scenario-governance-domain-tablet-pending.png` + `scenario-governance-domain-mobile-dark-refetch.png` |
| PaaS 场景容量 refetch/pending tablet/mobile light/dark golden 对照 | SDRP-05 + `scenario-paas-domain-tablet-pending.png` + `scenario-paas-domain-mobile-dark-refetch.png` |

## 通用前置

1. 先完成 `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md` SDPR-01～05（partial/retry 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{pending,refetch}.png` 四视口双主题 refetch/pending 独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 pending 与一张 refetch 独立截图；pending 必须出现 loading spinner 与待加载文案，refetch 必须出现 stale banner 与刷新 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. refetch/pending 截图出现文案裁切、spinner 错位、refetch banner 对比度不足或 dark 层级丢失时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 refetch/pending tablet/mobile light/dark 独立截图（G104）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 refetch/pending tablet/mobile light/dark 独立截图抽检行。

## SDRP-01 — BI 场景指标 refetch/pending tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-pending.png`、`scenario-bi-domain-tablet-dark-pending.png`、`scenario-bi-domain-mobile-pending.png`、`scenario-bi-domain-mobile-dark-pending.png`、`scenario-bi-domain-tablet-refetch.png`、`scenario-bi-domain-tablet-dark-refetch.png`、`scenario-bi-domain-mobile-refetch.png`、`scenario-bi-domain-mobile-dark-refetch.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light pending 截图 | `scenario-bi-domain-tablet-pending.png` 存在且 pending framing 正常 | SDRP-01 · RESP-06 |
| 2 | tablet dark pending 截图 | `scenario-bi-domain-tablet-dark-pending.png` 存在且 spinner 可读 | SDRP-01 · VIS-05 |
| 3 | mobile light refetch 截图 | `scenario-bi-domain-mobile-refetch.png` refetch banner 首屏可见 | SDRP-01 · RESP-07 |
| 4 | mobile dark refetch 截图 | `scenario-bi-domain-mobile-dark-refetch.png` refetch 对比度可辨认 | SDRP-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainRefetchPendingViewportLightDarkScreenshots` biDomain 全过 | SDRP-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 pending 面板 → 点击「触发指标刷新」→ 对照 tablet/mobile light/dark 八张 refetch/pending 截图。

## SDRP-02 — DevOps 场景阶段 refetch/pending tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-pending.png`、`scenario-devops-domain-tablet-dark-pending.png`、`scenario-devops-domain-mobile-pending.png`、`scenario-devops-domain-mobile-dark-pending.png`、`scenario-devops-domain-tablet-refetch.png`、`scenario-devops-domain-tablet-dark-refetch.png`、`scenario-devops-domain-mobile-refetch.png`、`scenario-devops-domain-mobile-dark-refetch.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light pending 截图 | `scenario-devops-domain-tablet-pending.png` 存在且 pending framing 正常 | SDRP-02 · RESP-06 |
| 2 | tablet dark pending 截图 | `scenario-devops-domain-tablet-dark-pending.png` 存在且阶段 pending 可读 | SDRP-02 · VIS-05 |
| 3 | mobile light refetch 截图 | `scenario-devops-domain-mobile-refetch.png` 流水线 refetch 首屏可见 | SDRP-02 · RESP-07 |
| 4 | mobile dark refetch 截图 | `scenario-devops-domain-mobile-dark-refetch.png` refetch 对比度可辨认 | SDRP-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + refetch/pending tablet/mobile light/dark 可见 | SDRP-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 pending 面板 → 点击「触发阶段刷新」→ 对照 tablet/mobile light/dark 八张截图。

## SDRP-03 — Gateway 场景端点 refetch/pending tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-pending.png`、`scenario-gateway-domain-tablet-dark-pending.png`、`scenario-gateway-domain-mobile-pending.png`、`scenario-gateway-domain-mobile-dark-pending.png`、`scenario-gateway-domain-tablet-refetch.png`、`scenario-gateway-domain-tablet-dark-refetch.png`、`scenario-gateway-domain-mobile-refetch.png`、`scenario-gateway-domain-mobile-dark-refetch.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light pending 截图 | `scenario-gateway-domain-tablet-pending.png` 存在且 pending framing 正常 | SDRP-03 · RESP-06 |
| 2 | tablet dark pending 截图 | `scenario-gateway-domain-tablet-dark-pending.png` 存在且端点 pending 可读 | SDRP-03 · VIS-05 |
| 3 | mobile light refetch 截图 | `scenario-gateway-domain-mobile-refetch.png` 端点 refetch 首屏可见 | SDRP-03 · RESP-07 |
| 4 | mobile dark refetch 截图 | `scenario-gateway-domain-mobile-dark-refetch.png` refetch 层级不丢失 | SDRP-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + refetch/pending tablet/mobile light/dark 可见 | SDRP-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 pending 面板 → 点击「触发端点刷新」→ 对照 tablet/mobile light/dark 八张截图。

## SDRP-04 — Governance 场景审计行 refetch/pending tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-pending.png`、`scenario-governance-domain-tablet-dark-pending.png`、`scenario-governance-domain-mobile-pending.png`、`scenario-governance-domain-mobile-dark-pending.png`、`scenario-governance-domain-tablet-refetch.png`、`scenario-governance-domain-tablet-dark-refetch.png`、`scenario-governance-domain-mobile-refetch.png`、`scenario-governance-domain-mobile-dark-refetch.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light pending 截图 | `scenario-governance-domain-tablet-pending.png` 存在且 pending framing 正常 | SDRP-04 · RESP-06 |
| 2 | tablet dark pending 截图 | `scenario-governance-domain-tablet-dark-pending.png` 存在且审计 pending 可读 | SDRP-04 · VIS-05 |
| 3 | mobile light refetch 截图 | `scenario-governance-domain-mobile-refetch.png` 审计 refetch 首屏可见 | SDRP-04 · RESP-07 |
| 4 | mobile dark refetch 截图 | `scenario-governance-domain-mobile-dark-refetch.png` refetch 密度一致 | SDRP-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + refetch/pending tablet/mobile light/dark 可见 | SDRP-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 pending 面板 → 点击「触发审计刷新」→ 对照 tablet/mobile light/dark 八张截图。

## SDRP-05 — PaaS 场景容量 refetch/pending tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-pending.png`、`scenario-paas-domain-tablet-dark-pending.png`、`scenario-paas-domain-mobile-pending.png`、`scenario-paas-domain-mobile-dark-pending.png`、`scenario-paas-domain-tablet-refetch.png`、`scenario-paas-domain-tablet-dark-refetch.png`、`scenario-paas-domain-mobile-refetch.png`、`scenario-paas-domain-mobile-dark-refetch.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light pending 截图 | `scenario-paas-domain-tablet-pending.png` 存在且 pending framing 正常 | SDRP-05 · RESP-06 |
| 2 | tablet dark pending 截图 | `scenario-paas-domain-tablet-dark-pending.png` 存在且容量 pending 可读 | SDRP-05 · VIS-05 |
| 3 | mobile light refetch 截图 | `scenario-paas-domain-mobile-refetch.png` 容量 refetch 首屏可见 | SDRP-05 · RESP-07 |
| 4 | mobile dark refetch 截图 | `scenario-paas-domain-mobile-dark-refetch.png` refetch 列表项可辨认 | SDRP-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + refetch/pending tablet/mobile light/dark 可见 | SDRP-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 pending 面板 → 点击「触发容量刷新」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md` SDRP-06～10
- partial/retry 前置：`scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md` SDPR-01～05
- 选型表：`decision-matrix.md` G104 场景域 refetch/pending tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDRP-01～10
- Runtime 门禁：`verifyScenarioDomainRefetchPendingViewportLightDarkScreenshots`
