# Scenario Domain Offline Sync Conflict Viewport Light/Dark Screenshot 评审清单

> DOCS-059 / G108 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 offline/sync conflict 独立截图视觉回归抽检**，确保每个场景 section 在离线同步冲突检测态、同步完成态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md`（SDCM-01～05）、`scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md`（SDOSC-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 offline/sync conflict tablet/mobile light/dark 独立截图抽检 | 对应 SDOSC 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标 offline/sync conflict tablet/mobile light/dark golden 对照 | SDOSC-01 + `scenario-bi-domain-tablet-offline.png` + `scenario-bi-domain-mobile-dark-synced.png` |
| DevOps 场景阶段 offline/sync conflict tablet/mobile light/dark golden 对照 | SDOSC-02 + `scenario-devops-domain-tablet-offline.png` + `scenario-devops-domain-mobile-dark-synced.png` |
| Gateway 场景端点 offline/sync conflict tablet/mobile light/dark golden 对照 | SDOSC-03 + `scenario-gateway-domain-tablet-offline.png` + `scenario-gateway-domain-mobile-dark-synced.png` |
| Governance 场景审计行 offline/sync conflict tablet/mobile light/dark golden 对照 | SDOSC-04 + `scenario-governance-domain-tablet-offline.png` + `scenario-governance-domain-mobile-dark-synced.png` |
| PaaS 场景容量 offline/sync conflict tablet/mobile light/dark golden 对照 | SDOSC-05 + `scenario-paas-domain-tablet-offline.png` + `scenario-paas-domain-mobile-dark-synced.png` |

## 通用前置

1. 先完成 `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md` SDCM-01～05（conflict/merge 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{offline,synced}.png` 四视口双主题 offline/sync conflict 独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 offline 与一张 synced 独立截图；offline 必须出现 offline banner 与待同步字段摘要，synced 必须出现 synced banner 与查看同步详情 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. offline/sync conflict 截图出现文案裁切、离线 banner 对比度不足、synced banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 offline/sync conflict tablet/mobile light/dark 独立截图（G108）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 offline/sync conflict tablet/mobile light/dark 独立截图抽检行。

## SDOSC-01 — BI 场景指标 offline/sync conflict tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-offline.png`、`scenario-bi-domain-tablet-dark-offline.png`、`scenario-bi-domain-mobile-offline.png`、`scenario-bi-domain-mobile-dark-offline.png`、`scenario-bi-domain-tablet-synced.png`、`scenario-bi-domain-tablet-dark-synced.png`、`scenario-bi-domain-mobile-synced.png`、`scenario-bi-domain-mobile-dark-synced.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light conflict 截图 | `scenario-bi-domain-tablet-offline.png` 存在且 offline framing 正常 | SDOSC-01 · RESP-06 |
| 2 | tablet dark conflict 截图 | `scenario-bi-domain-tablet-dark-offline.png` 存在且离线 banner 可读 | SDOSC-01 · VIS-05 |
| 3 | mobile light merged 截图 | `scenario-bi-domain-mobile-synced.png` synced banner 首屏可见 | SDOSC-01 · RESP-07 |
| 4 | mobile dark merged 截图 | `scenario-bi-domain-mobile-dark-synced.png` synced 对比度可辨认 | SDOSC-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainOfflineSyncConflictViewportLightDarkScreenshots` biDomain 全过 | SDOSC-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 offline 面板 → 点击「触发指标离线同步」→ 对照 tablet/mobile light/dark 八张 offline/sync conflict 截图。

## SDOSC-02 — DevOps 场景阶段 offline/sync conflict tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-offline.png`、`scenario-devops-domain-tablet-dark-offline.png`、`scenario-devops-domain-mobile-offline.png`、`scenario-devops-domain-mobile-dark-offline.png`、`scenario-devops-domain-tablet-synced.png`、`scenario-devops-domain-tablet-dark-synced.png`、`scenario-devops-domain-mobile-synced.png`、`scenario-devops-domain-mobile-dark-synced.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light conflict 截图 | `scenario-devops-domain-tablet-offline.png` 存在且 offline framing 正常 | SDOSC-02 · RESP-06 |
| 2 | tablet dark conflict 截图 | `scenario-devops-domain-tablet-dark-offline.png` 存在且离线冲突可读 | SDOSC-02 · VIS-05 |
| 3 | mobile light merged 截图 | `scenario-devops-domain-mobile-synced.png` 流水线 synced 首屏可见 | SDOSC-02 · RESP-07 |
| 4 | mobile dark merged 截图 | `scenario-devops-domain-mobile-dark-synced.png` synced 对比度可辨认 | SDOSC-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + offline/sync conflict tablet/mobile light/dark 可见 | SDOSC-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 offline 面板 → 点击「触发阶段离线同步」→ 对照 tablet/mobile light/dark 八张截图。

## SDOSC-03 — Gateway 场景端点 offline/sync conflict tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-offline.png`、`scenario-gateway-domain-tablet-dark-offline.png`、`scenario-gateway-domain-mobile-offline.png`、`scenario-gateway-domain-mobile-dark-offline.png`、`scenario-gateway-domain-tablet-synced.png`、`scenario-gateway-domain-tablet-dark-synced.png`、`scenario-gateway-domain-mobile-synced.png`、`scenario-gateway-domain-mobile-dark-synced.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light conflict 截图 | `scenario-gateway-domain-tablet-offline.png` 存在且 offline framing 正常 | SDOSC-03 · RESP-06 |
| 2 | tablet dark conflict 截图 | `scenario-gateway-domain-tablet-dark-offline.png` 存在且离线冲突可读 | SDOSC-03 · VIS-05 |
| 3 | mobile light merged 截图 | `scenario-gateway-domain-mobile-synced.png` 端点 synced 首屏可见 | SDOSC-03 · RESP-07 |
| 4 | mobile dark merged 截图 | `scenario-gateway-domain-mobile-dark-synced.png` synced 层级不丢失 | SDOSC-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + offline/sync conflict tablet/mobile light/dark 可见 | SDOSC-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 offline 面板 → 点击「触发端点离线同步」→ 对照 tablet/mobile light/dark 八张截图。

## SDOSC-04 — Governance 场景审计行 offline/sync conflict tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-offline.png`、`scenario-governance-domain-tablet-dark-offline.png`、`scenario-governance-domain-mobile-offline.png`、`scenario-governance-domain-mobile-dark-offline.png`、`scenario-governance-domain-tablet-synced.png`、`scenario-governance-domain-tablet-dark-synced.png`、`scenario-governance-domain-mobile-synced.png`、`scenario-governance-domain-mobile-dark-synced.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light conflict 截图 | `scenario-governance-domain-tablet-offline.png` 存在且 offline framing 正常 | SDOSC-04 · RESP-06 |
| 2 | tablet dark conflict 截图 | `scenario-governance-domain-tablet-dark-offline.png` 存在且离线冲突可读 | SDOSC-04 · VIS-05 |
| 3 | mobile light merged 截图 | `scenario-governance-domain-mobile-synced.png` 审计 synced 首屏可见 | SDOSC-04 · RESP-07 |
| 4 | mobile dark merged 截图 | `scenario-governance-domain-mobile-dark-synced.png` synced 密度一致 | SDOSC-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + offline/sync conflict tablet/mobile light/dark 可见 | SDOSC-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 offline 面板 → 点击「触发审计离线同步」→ 对照 tablet/mobile light/dark 八张截图。

## SDOSC-05 — PaaS 场景容量 offline/sync conflict tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-offline.png`、`scenario-paas-domain-tablet-dark-offline.png`、`scenario-paas-domain-mobile-offline.png`、`scenario-paas-domain-mobile-dark-offline.png`、`scenario-paas-domain-tablet-synced.png`、`scenario-paas-domain-tablet-dark-synced.png`、`scenario-paas-domain-mobile-synced.png`、`scenario-paas-domain-mobile-dark-synced.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light conflict 截图 | `scenario-paas-domain-tablet-offline.png` 存在且 offline framing 正常 | SDOSC-05 · RESP-06 |
| 2 | tablet dark conflict 截图 | `scenario-paas-domain-tablet-dark-offline.png` 存在且离线冲突可读 | SDOSC-05 · VIS-05 |
| 3 | mobile light merged 截图 | `scenario-paas-domain-mobile-synced.png` 容量 synced 首屏可见 | SDOSC-05 · RESP-07 |
| 4 | mobile dark merged 截图 | `scenario-paas-domain-mobile-dark-synced.png` synced 列表项可辨认 | SDOSC-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + offline/sync conflict tablet/mobile light/dark 可见 | SDOSC-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 offline 面板 → 点击「触发容量离线同步」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md` SDOSC-06～10
- mutation pending/rollback 前置：`scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md` SDMR-01～05
- 选型表：`decision-matrix.md` G108 场景域 offline/sync conflict tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDOSC-01～10
- Runtime 门禁：`verifyScenarioDomainOfflineSyncConflictViewportLightDarkScreenshots`
