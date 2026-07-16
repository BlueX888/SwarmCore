# 场景 Scenario Domain Offline Sync Conflict Viewport Light/Dark Screenshot 评审清单

> DOCS-059 / G108 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 offline/sync conflict 独立截图抽检**，确保各域 section 在离线同步冲突检测态与同步完成态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md`（SDOSC-01～05）、`scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md`（SDCM-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 offline/sync conflict tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDOSC 块 + `quality-rubric.md` |
| BI Analytics 指标 offline/sync conflict tablet/mobile light/dark 独立截图 | SDOSC-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 offline/sync conflict tablet/mobile light/dark 独立截图 | SDOSC-07 + `scenario-devops` |
| Gateway 端点 offline/sync conflict tablet/mobile light/dark 独立截图 | SDOSC-08 + `scenario-gateway` |
| Governance 审计行 offline/sync conflict tablet/mobile light/dark 独立截图 | SDOSC-09 + `scenario-governance` |
| 场景域 offline/sync conflict tablet/mobile light/dark 独立截图束缺门禁 | SDOSC-10 + `verify:runtime` `scenarioDomainOfflineSyncConflictViewportLightDarkScreenshotStates` + `verifyScenarioDomainOfflineSyncConflictViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md` SDOSC-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{offline,synced}.png` 共 40 张 offline/sync conflict 独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark offline/sync conflict 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 offline/sync conflict tablet/mobile light/dark 独立截图（G108）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 offline/sync conflict tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDOSC-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDOSC-06 — BI Analytics 指标 offline/sync conflict tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-offline.png`、`scenario-bi-domain-mobile-dark-synced.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark conflict | `scenario-bi-domain-tablet-offline.png` + `scenario-bi-domain-tablet-dark-offline.png` offline framing 正常 | SDOSC-06 · RESP-06 |
| 2 | mobile light/dark merged | `scenario-bi-domain-mobile-synced.png` + `scenario-bi-domain-mobile-dark-synced.png` merged framing 正常 | SDOSC-06 · RESP-07 |
| 3 | 指标 offline/sync conflict | 离线 banner + 冲突字段摘要 + 同步完成 banner tablet/mobile light/dark 首屏可见 | SDOSC-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 conflict banner 与 synced banner 层级可辨认 | SDOSC-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 offline/sync conflict 截图全过 | SDOSC-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 offline 面板 → 点击「触发指标离线同步」→ 对照 tablet/mobile light/dark 八张 offline/sync conflict 截图。

## SDOSC-07 — DevOps 阶段 offline/sync conflict tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-offline.png`、`scenario-devops-domain-mobile-dark-synced.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark conflict | `scenario-devops-domain-tablet-offline.png` + `scenario-devops-domain-tablet-dark-offline.png` offline framing 正常 | SDOSC-07 · RESP-06 |
| 2 | mobile light/dark merged | `scenario-devops-domain-mobile-synced.png` + `scenario-devops-domain-mobile-dark-synced.png` merged framing 正常 | SDOSC-07 · RESP-07 |
| 3 | 阶段 offline/sync conflict | 流水线离线 banner + 同步完成摘要 tablet/mobile light/dark 首屏可见 | SDOSC-07 · PAT-07 |
| 4 | merged 态 | mobile dark 下 synced 文案与查看详情按钮可辨认 | SDOSC-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 offline/sync conflict 截图全过 | SDOSC-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 offline 面板 → 点击「触发阶段离线同步」→ 对照 tablet/mobile light/dark 八张截图。

## SDOSC-08 — Gateway 端点 offline/sync conflict tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-offline.png`、`scenario-gateway-domain-mobile-dark-synced.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark conflict | `scenario-gateway-domain-tablet-offline.png` + `scenario-gateway-domain-tablet-dark-offline.png` offline framing 正常 | SDOSC-08 · RESP-06 |
| 2 | mobile light/dark merged | `scenario-gateway-domain-mobile-synced.png` + `scenario-gateway-domain-mobile-dark-synced.png` merged framing 正常 | SDOSC-08 · RESP-07 |
| 3 | 端点 offline/sync conflict | 端点离线 banner + 同步完成摘要 tablet/mobile light/dark 首屏可见 | SDOSC-08 · PAT-08 |
| 4 | conflict 态 | mobile dark 下冲突字段与 banner 可辨认 | SDOSC-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 offline/sync conflict 截图全过 | SDOSC-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 offline 面板 → 点击「触发端点离线同步」→ 对照 tablet/mobile light/dark 八张截图。

## SDOSC-09 — Governance 审计行 offline/sync conflict tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-offline.png`、`scenario-governance-domain-mobile-offline.png`、`scenario-governance-domain-mobile-dark-synced.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark conflict | `scenario-governance-domain-tablet-offline.png` + `scenario-governance-domain-tablet-dark-offline.png` offline framing 正常 | SDOSC-09 · RESP-06 |
| 2 | mobile light/dark merged | `scenario-governance-domain-mobile-synced.png` + `scenario-governance-domain-mobile-dark-synced.png` merged framing 正常 | SDOSC-09 · RESP-07 |
| 3 | 审计 offline/sync conflict | 审计离线 banner + 同步完成摘要 tablet/mobile light/dark 首屏可见 | SDOSC-09 · PAT-09 |
| 4 | synced 文案 | mobile dark 下「离线变更已同步，可继续发布策略变更」文案可辨认 | SDOSC-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 offline/sync conflict 截图全过 | SDOSC-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 offline 面板 → 点击「触发审计离线同步」→ 对照 tablet/mobile light/dark 八张截图。

## SDOSC-10 — 场景域 offline/sync conflict tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{offline,synced}.png` + `scenarioDomainOfflineSyncConflictViewportLightDarkScreenshotStates.offlineSyncConflictStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × offline/sync conflict 全量 golden 存在 | SDOSC-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainOfflineSyncConflictViewportLightDarkScreenshots` 通过 | SDOSC-10 · PREVIEW-* |
| 3 | offline 态 | 五域 `data-audit="scenario-domain-offline-overlay"` `data-state="offline"` 可见 | SDOSC-10 · LOGIC-* |
| 4 | synced 态 | 五域点击 sync trigger 后 `role="status"` + `data-state="synced"` 可见 | SDOSC-10 · ASYNC-* |
| 5 | 矩阵完整 | `offlineSyncConflictStateMatrixComplete = true` | SDOSC-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张 offline/sync conflict 截图与门禁 JSON 输出。
