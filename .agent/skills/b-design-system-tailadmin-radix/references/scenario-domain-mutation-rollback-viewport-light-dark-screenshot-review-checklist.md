# Scenario Domain Mutation Rollback Viewport Light/Dark Screenshot 评审清单

> DOCS-057 / G106 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 mutation pending/rollback 独立截图视觉回归抽检**，确保每个场景 section 在变更提交中、服务端拒绝回滚态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md`（SDSO-01～05）、`scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md`（SDMR-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 mutation pending/rollback tablet/mobile light/dark 独立截图抽检 | 对应 SDMR 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标 mutation pending/rollback tablet/mobile light/dark golden 对照 | SDMR-01 + `scenario-bi-domain-tablet-mutation-pending.png` + `scenario-bi-domain-mobile-dark-rollback.png` |
| DevOps 场景阶段 mutation pending/rollback tablet/mobile light/dark golden 对照 | SDMR-02 + `scenario-devops-domain-tablet-mutation-pending.png` + `scenario-devops-domain-mobile-dark-rollback.png` |
| Gateway 场景端点 mutation pending/rollback tablet/mobile light/dark golden 对照 | SDMR-03 + `scenario-gateway-domain-tablet-mutation-pending.png` + `scenario-gateway-domain-mobile-dark-rollback.png` |
| Governance 场景审计行 mutation pending/rollback tablet/mobile light/dark golden 对照 | SDMR-04 + `scenario-governance-domain-tablet-mutation-pending.png` + `scenario-governance-domain-mobile-dark-rollback.png` |
| PaaS 场景容量 mutation pending/rollback tablet/mobile light/dark golden 对照 | SDMR-05 + `scenario-paas-domain-tablet-mutation-pending.png` + `scenario-paas-domain-mobile-dark-rollback.png` |

## 通用前置

1. 先完成 `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md` SDSO-01～05（stale/optimistic 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{mutation-pending,rollback}.png` 四视口双主题 mutation pending/rollback 独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 mutation-pending 与一张 rollback 独立截图；mutation-pending 必须出现提交 banner 与 spinner，rollback 必须出现回滚 banner 与恢复 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. mutation pending/rollback 截图出现文案裁切、spinner 错位、rollback banner 对比度不足或 dark 层级丢失时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 mutation pending/rollback tablet/mobile light/dark 独立截图（G106）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 mutation pending/rollback tablet/mobile light/dark 独立截图抽检行。

## SDMR-01 — BI 场景指标 mutation pending/rollback tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-mutation-pending.png`、`scenario-bi-domain-tablet-dark-mutation-pending.png`、`scenario-bi-domain-mobile-mutation-pending.png`、`scenario-bi-domain-mobile-dark-mutation-pending.png`、`scenario-bi-domain-tablet-rollback.png`、`scenario-bi-domain-tablet-dark-rollback.png`、`scenario-bi-domain-mobile-rollback.png`、`scenario-bi-domain-mobile-dark-rollback.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light stale 截图 | `scenario-bi-domain-tablet-mutation-pending.png` 存在且 mutation-pending framing 正常 | SDMR-01 · RESP-06 |
| 2 | tablet dark stale 截图 | `scenario-bi-domain-tablet-dark-mutation-pending.png` 存在且spinner 可读 | SDMR-01 · VIS-05 |
| 3 | mobile light optimistic 截图 | `scenario-bi-domain-mobile-rollback.png` rollback banner 首屏可见 | SDMR-01 · RESP-07 |
| 4 | mobile dark optimistic 截图 | `scenario-bi-domain-mobile-dark-rollback.png` rollback 对比度可辨认 | SDMR-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainMutationRollbackViewportLightDarkScreenshots` biDomain 全过 | SDMR-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 mutation-pending 面板 → 点击「触发指标变更回滚」→ 对照 tablet/mobile light/dark 八张 mutation pending/rollback 截图。

## SDMR-02 — DevOps 场景阶段 mutation pending/rollback tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-mutation-pending.png`、`scenario-devops-domain-tablet-dark-mutation-pending.png`、`scenario-devops-domain-mobile-mutation-pending.png`、`scenario-devops-domain-mobile-dark-mutation-pending.png`、`scenario-devops-domain-tablet-rollback.png`、`scenario-devops-domain-tablet-dark-rollback.png`、`scenario-devops-domain-mobile-rollback.png`、`scenario-devops-domain-mobile-dark-rollback.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light stale 截图 | `scenario-devops-domain-tablet-mutation-pending.png` 存在且 mutation-pending framing 正常 | SDMR-02 · RESP-06 |
| 2 | tablet dark stale 截图 | `scenario-devops-domain-tablet-dark-mutation-pending.png` 存在且阶段 stale 可读 | SDMR-02 · VIS-05 |
| 3 | mobile light optimistic 截图 | `scenario-devops-domain-mobile-rollback.png` 流水线 optimistic 首屏可见 | SDMR-02 · RESP-07 |
| 4 | mobile dark optimistic 截图 | `scenario-devops-domain-mobile-dark-rollback.png` rollback 对比度可辨认 | SDMR-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + mutation pending/rollback tablet/mobile light/dark 可见 | SDMR-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 mutation-pending 面板 → 点击「触发阶段变更回滚」→ 对照 tablet/mobile light/dark 八张截图。

## SDMR-03 — Gateway 场景端点 mutation pending/rollback tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-mutation-pending.png`、`scenario-gateway-domain-tablet-dark-mutation-pending.png`、`scenario-gateway-domain-mobile-mutation-pending.png`、`scenario-gateway-domain-mobile-dark-mutation-pending.png`、`scenario-gateway-domain-tablet-rollback.png`、`scenario-gateway-domain-tablet-dark-rollback.png`、`scenario-gateway-domain-mobile-rollback.png`、`scenario-gateway-domain-mobile-dark-rollback.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light stale 截图 | `scenario-gateway-domain-tablet-mutation-pending.png` 存在且 mutation-pending framing 正常 | SDMR-03 · RESP-06 |
| 2 | tablet dark stale 截图 | `scenario-gateway-domain-tablet-dark-mutation-pending.png` 存在且端点 stale 可读 | SDMR-03 · VIS-05 |
| 3 | mobile light optimistic 截图 | `scenario-gateway-domain-mobile-rollback.png` 端点 optimistic 首屏可见 | SDMR-03 · RESP-07 |
| 4 | mobile dark optimistic 截图 | `scenario-gateway-domain-mobile-dark-rollback.png` optimistic 层级不丢失 | SDMR-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + mutation pending/rollback tablet/mobile light/dark 可见 | SDMR-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 mutation-pending 面板 → 点击「触发端点变更回滚」→ 对照 tablet/mobile light/dark 八张截图。

## SDMR-04 — Governance 场景审计行 mutation pending/rollback tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-mutation-pending.png`、`scenario-governance-domain-tablet-dark-mutation-pending.png`、`scenario-governance-domain-mobile-mutation-pending.png`、`scenario-governance-domain-mobile-dark-mutation-pending.png`、`scenario-governance-domain-tablet-rollback.png`、`scenario-governance-domain-tablet-dark-rollback.png`、`scenario-governance-domain-mobile-rollback.png`、`scenario-governance-domain-mobile-dark-rollback.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light stale 截图 | `scenario-governance-domain-tablet-mutation-pending.png` 存在且 mutation-pending framing 正常 | SDMR-04 · RESP-06 |
| 2 | tablet dark stale 截图 | `scenario-governance-domain-tablet-dark-mutation-pending.png` 存在且审计 stale 可读 | SDMR-04 · VIS-05 |
| 3 | mobile light optimistic 截图 | `scenario-governance-domain-mobile-rollback.png` 审计 optimistic 首屏可见 | SDMR-04 · RESP-07 |
| 4 | mobile dark optimistic 截图 | `scenario-governance-domain-mobile-dark-rollback.png` optimistic 密度一致 | SDMR-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + mutation pending/rollback tablet/mobile light/dark 可见 | SDMR-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 mutation-pending 面板 → 点击「触发审计变更回滚」→ 对照 tablet/mobile light/dark 八张截图。

## SDMR-05 — PaaS 场景容量 mutation pending/rollback tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-mutation-pending.png`、`scenario-paas-domain-tablet-dark-mutation-pending.png`、`scenario-paas-domain-mobile-mutation-pending.png`、`scenario-paas-domain-mobile-dark-mutation-pending.png`、`scenario-paas-domain-tablet-rollback.png`、`scenario-paas-domain-tablet-dark-rollback.png`、`scenario-paas-domain-mobile-rollback.png`、`scenario-paas-domain-mobile-dark-rollback.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light stale 截图 | `scenario-paas-domain-tablet-mutation-pending.png` 存在且 mutation-pending framing 正常 | SDMR-05 · RESP-06 |
| 2 | tablet dark stale 截图 | `scenario-paas-domain-tablet-dark-mutation-pending.png` 存在且容量 stale 可读 | SDMR-05 · VIS-05 |
| 3 | mobile light optimistic 截图 | `scenario-paas-domain-mobile-rollback.png` 容量 optimistic 首屏可见 | SDMR-05 · RESP-07 |
| 4 | mobile dark optimistic 截图 | `scenario-paas-domain-mobile-dark-rollback.png` optimistic 列表项可辨认 | SDMR-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + mutation pending/rollback tablet/mobile light/dark 可见 | SDMR-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 mutation-pending 面板 → 点击「触发容量变更回滚」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md` SDMR-06～10
- refetch/pending 前置：`scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md` SDSO-01～05
- 选型表：`decision-matrix.md` G106 场景域 mutation pending/rollback tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDMR-01～10
- Runtime 门禁：`verifyScenarioDomainMutationRollbackViewportLightDarkScreenshots`
