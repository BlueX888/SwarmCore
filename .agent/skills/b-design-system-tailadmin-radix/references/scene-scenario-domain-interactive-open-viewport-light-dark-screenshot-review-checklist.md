# 场景 Scenario Domain Interactive Open Viewport Light/Dark Screenshot 评审清单

> DOCS-047 / G96 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题交互态打开态独立截图抽检**，确保各域 section 在浮层打开态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDIO-01～05）、`scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md`（SDTM-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域交互态打开态 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDIO 块 + `quality-rubric.md` |
| BI Analytics ShareEmbedDialog tablet/mobile light/dark 打开态独立截图 | SDIO-06 + `tailadmin-bi-analytics` |
| DevOps RollbackDialog tablet/mobile light/dark 打开态独立截图 | SDIO-07 + `scenario-devops` |
| Gateway ApiKeyReveal tablet/mobile light/dark 打开态独立截图 | SDIO-08 + `scenario-gateway` |
| Governance AuditLog 导出 Drawer tablet/mobile light/dark 打开态独立截图 | SDIO-09 + `scenario-governance` |
| 场景域交互态打开态 tablet/mobile light/dark 独立截图束缺门禁 | SDIO-10 + `verify:runtime` `scenarioDomainInteractiveOpenViewportLightDarkScreenshotStates` |

## 通用前置

1. 先完成 `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDIO-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-open.png` 共 20 张打开态独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + DevOps 或 Gateway** tablet/mobile light/dark 打开态独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域交互态打开态 tablet/mobile light/dark 独立截图（G96）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域交互态打开态 tablet/mobile light/dark 独立截图抽检行。

## SDIO-06 — BI Analytics ShareEmbedDialog tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-open.png`、`scenario-bi-domain-mobile-dark-open.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-bi-domain-tablet-open.png` + `scenario-bi-domain-tablet-dark-open.png` Dialog framing 正常 | SDIO-06 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-bi-domain-mobile-open.png` + `scenario-bi-domain-mobile-dark-open.png` Dialog framing 正常 | SDIO-06 · RESP-07 |
| 3 | Data Screen + 分享 | Data Screen tab + ShareEmbedDialog 打开态 tablet/mobile light/dark 首屏可见 | SDIO-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 Dialog 边框/背景/按钮层级可辨认 | SDIO-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 四视口双主题打开态截图全过 | SDIO-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 切换 Data Screen tab → 点击「打开分享嵌入」→ 对照 tablet/mobile light/dark 四张打开态截图 → 关闭 Dialog。

## SDIO-07 — DevOps RollbackDialog tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-open.png`、`scenario-devops-domain-mobile-dark-open.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-devops-domain-tablet-open.png` + `scenario-devops-domain-tablet-dark-open.png` Dialog framing 正常 | SDIO-07 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-devops-domain-mobile-open.png` + `scenario-devops-domain-mobile-dark-open.png` Dialog framing 正常 | SDIO-07 · RESP-07 |
| 3 | 回滚确认 | RollbackDialog 危险操作文案 tablet/mobile light/dark 首屏可见 | SDIO-07 · PAT-07 |
| 4 | 关闭路径 | mobile dark 下取消/确认按钮可读且可关闭 | SDIO-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 四视口双主题打开态截图全过 | SDIO-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 点击「打开回滚确认」→ 对照 tablet/mobile light/dark 四张打开态截图 → 关闭 Dialog。

## SDIO-08 — Gateway ApiKeyReveal tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-open.png`、`scenario-gateway-domain-mobile-dark-open.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-gateway-domain-tablet-open.png` + `scenario-gateway-domain-tablet-dark-open.png` Dialog framing 正常 | SDIO-08 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-gateway-domain-mobile-open.png` + `scenario-gateway-domain-mobile-dark-open.png` Dialog framing 正常 | SDIO-08 · RESP-07 |
| 3 | 密钥轮换 | ApiKeyReveal Dialog tablet/mobile light/dark 首屏可见 | SDIO-08 · PAT-08 |
| 4 | 危险操作 | mobile dark 下确认轮换按钮层级不丢失 | SDIO-08 · RESP-08 |
| 5 | example runtime | Gateway 场景 section + 四视口双主题打开态截图全过 | SDIO-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 点击「打开密钥轮换」→ 对照 tablet/mobile light/dark 四张打开态截图 → 关闭 Dialog。

## SDIO-09 — Governance AuditLog 导出 Drawer tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-open.png`、`scenario-governance-domain-mobile-dark-open.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-governance-domain-tablet-open.png` + `scenario-governance-domain-tablet-dark-open.png` Drawer framing 正常 | SDIO-09 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-governance-domain-mobile-open.png` + `scenario-governance-domain-mobile-dark-open.png` Drawer framing 正常 | SDIO-09 · RESP-07 |
| 3 | 导出 Drawer | AuditLog 导出 Drawer 表单 tablet/mobile light/dark 首屏可见 | SDIO-09 · PAT-09 |
| 4 | 关闭路径 | mobile dark 下 Drawer 关闭按钮与 footer 操作可读 | SDIO-09 · INTER-09 |
| 5 | example runtime | Governance 场景 section + 四视口双主题打开态截图全过 | SDIO-09 · PREVIEW-* |

**交互动作**：打开治理场景 → 点击「打开审计导出」→ 对照 tablet/mobile light/dark 四张打开态截图 → 关闭 Drawer。

## SDIO-10 — 场景域交互态打开态 tablet/mobile light/dark 独立截图束

**对照 golden**：`scenario-*-domain-{tablet,mobile}{,-dark}-open.png`（20 张）、`verifyScenarioDomainInteractiveOpenViewportLightDarkScreenshots`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 五域 tablet light 打开态截图 | 5 张 `scenario-*-domain-tablet-open.png` 均存在且浮层 framing 正常 | SDIO-10 · RESP-06 |
| 2 | 五域 tablet dark 打开态截图 | 5 张 `scenario-*-domain-tablet-dark-open.png` 均存在且浮层 framing 正常 | SDIO-10 · VIS-05 |
| 3 | 五域 mobile light 打开态截图 | 5 张 `scenario-*-domain-mobile-open.png` 均存在且打开态首屏可见 | SDIO-10 · RESP-07 |
| 4 | 五域 mobile dark 打开态截图 | 5 张 `scenario-*-domain-mobile-dark-open.png` 均存在且对比度可辨认 | SDIO-10 · VIS-06 |
| 5 | runtime 门禁 | `scenarioDomainInteractiveOpenViewportLightDarkScreenshotStates.openStateMatrixComplete = true` | SDIO-10 · VAL-* |

**交互动作**：跑 `npm run verify:runtime` → 确认 `openStateMatrixComplete = true` → 对照 20 张打开态独立截图。

## 交叉引用

- `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDIO-01～05
- `scenario-domain-viewport-light-dark-screenshot-review-checklist.md` — SDTM-01～05
- `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md` — SDTM-06～10
- `scene-interaction-review-checklist.md` — INTER-06～10
- `business-validation-checklist.md` — VAL-* 场景冒烟
- `decision-matrix.md` — G96 场景域交互态打开态 tablet/mobile light/dark 独立截图选型表
- `upgrade-troubleshooting.md` — SDIO-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域交互态打开态 tablet/mobile light/dark 独立截图检索路径
- `quality-rubric.md` — 综合美学 / 交互与动效质量维度
