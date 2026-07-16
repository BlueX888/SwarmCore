# Scenario Domain Interactive Open Viewport Light/Dark Screenshot 评审清单

> DOCS-047 / G96 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题交互态打开态独立截图视觉回归抽检**，确保每个场景 section 在浮层/Drawer 打开态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-viewport-light-dark-screenshot-review-checklist.md`（SDTM-01～05）、`scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDIO-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域交互态打开态 tablet/mobile light/dark 独立截图抽检 | 对应 SDIO 块 + `quality-rubric.md` 综合美学 |
| BI 场景 ShareEmbedDialog 打开态 tablet/mobile light/dark golden 对照 | SDIO-01 + `scenario-bi-domain-tablet-open.png` + `scenario-bi-domain-mobile-dark-open.png` |
| DevOps 场景 RollbackDialog 打开态 tablet/mobile light/dark golden 对照 | SDIO-02 + `scenario-devops-domain-tablet-open.png` + `scenario-devops-domain-mobile-dark-open.png` |
| Gateway 场景 ApiKeyReveal 打开态 tablet/mobile light/dark golden 对照 | SDIO-03 + `scenario-gateway-domain-tablet-open.png` + `scenario-gateway-domain-mobile-dark-open.png` |
| Governance 场景 AuditLog 导出 Drawer 打开态 tablet/mobile light/dark golden 对照 | SDIO-04 + `scenario-governance-domain-tablet-open.png` + `scenario-governance-domain-mobile-dark-open.png` |
| PaaS 场景 OpsDangerFlow 打开态 tablet/mobile light/dark golden 对照 | SDIO-05 + `scenario-paas-domain-tablet-open.png` + `scenario-paas-domain-mobile-dark-open.png` |

## 通用前置

1. 先完成 `scenario-domain-viewport-light-dark-screenshot-review-checklist.md` SDTM-01～05（tablet/mobile light/dark 关闭态独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-open.png` 四视口双主题打开态截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 两张打开态独立截图，且浮层必须真实打开、可关闭。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 打开态截图出现浮层遮挡关键文案到不可读、Dialog/Drawer 未居中或越界、关闭路径缺失时，交互与动效质量不得评 95+，综合美学不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域交互态打开态 tablet/mobile light/dark 独立截图（G96）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域交互态打开态 tablet/mobile light/dark 独立截图抽检行。

## SDIO-01 — BI 场景 ShareEmbedDialog tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-bi-domain-tablet-open.png`、`scenario-bi-domain-tablet-dark-open.png`、`scenario-bi-domain-mobile-open.png`、`scenario-bi-domain-mobile-dark-open.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-bi-domain-tablet-open.png` 存在且 Dialog framing 正常 | SDIO-01 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-bi-domain-tablet-dark-open.png` 存在且 Dialog framing 正常 | SDIO-01 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-bi-domain-mobile-open.png` 分享 Dialog 首屏可见 | SDIO-01 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-bi-domain-mobile-dark-open.png` 打开态对比度可辨认 | SDIO-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainInteractiveOpenViewportLightDarkScreenshots` biDomain 全过 | SDIO-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 切换 Data Screen tab → 点击「打开分享嵌入」→ 对照 tablet/mobile light/dark 四张打开态截图 → 关闭 Dialog。

## SDIO-02 — DevOps 场景 RollbackDialog tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-devops-domain-tablet-open.png`、`scenario-devops-domain-tablet-dark-open.png`、`scenario-devops-domain-mobile-open.png`、`scenario-devops-domain-mobile-dark-open.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-devops-domain-tablet-open.png` 存在且 Dialog framing 正常 | SDIO-02 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-devops-domain-tablet-dark-open.png` 存在且 Dialog framing 正常 | SDIO-02 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-devops-domain-mobile-open.png` 回滚确认 Dialog 首屏可见 | SDIO-02 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-devops-domain-mobile-dark-open.png` 危险操作文案可读 | SDIO-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 打开态 overlay tablet/mobile light/dark 可见 | SDIO-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 点击「打开回滚确认」→ 对照 tablet/mobile light/dark 四张打开态截图 → 关闭 Dialog。

## SDIO-03 — Gateway 场景 ApiKeyReveal tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-gateway-domain-tablet-open.png`、`scenario-gateway-domain-tablet-dark-open.png`、`scenario-gateway-domain-mobile-open.png`、`scenario-gateway-domain-mobile-dark-open.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-gateway-domain-tablet-open.png` 存在且 Dialog framing 正常 | SDIO-03 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-gateway-domain-tablet-dark-open.png` 存在且 Dialog framing 正常 | SDIO-03 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-gateway-domain-mobile-open.png` 密钥轮换 Dialog 首屏可见 | SDIO-03 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-gateway-domain-mobile-dark-open.png` 危险按钮层级不丢失 | SDIO-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 打开态 overlay tablet/mobile light/dark 可见 | SDIO-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 点击「打开密钥轮换」→ 对照 tablet/mobile light/dark 四张打开态截图 → 关闭 Dialog。

## SDIO-04 — Governance 场景 AuditLog 导出 Drawer tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-governance-domain-tablet-open.png`、`scenario-governance-domain-tablet-dark-open.png`、`scenario-governance-domain-mobile-open.png`、`scenario-governance-domain-mobile-dark-open.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-governance-domain-tablet-open.png` 存在且 Drawer framing 正常 | SDIO-04 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-governance-domain-tablet-dark-open.png` 存在且 Drawer framing 正常 | SDIO-04 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-governance-domain-mobile-open.png` 导出 Drawer 首屏可见 | SDIO-04 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-governance-domain-mobile-dark-open.png` Drawer 表单密度一致 | SDIO-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 打开态 Drawer tablet/mobile light/dark 可见 | SDIO-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 点击「打开审计导出」→ 对照 tablet/mobile light/dark 四张打开态截图 → 关闭 Drawer。

## SDIO-05 — PaaS 场景 OpsDangerFlow tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-paas-domain-tablet-open.png`、`scenario-paas-domain-tablet-dark-open.png`、`scenario-paas-domain-mobile-open.png`、`scenario-paas-domain-mobile-dark-open.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-paas-domain-tablet-open.png` 存在且 Dialog framing 正常 | SDIO-05 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-paas-domain-tablet-dark-open.png` 存在且 Dialog framing 正常 | SDIO-05 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-paas-domain-mobile-open.png` 伸缩确认 Dialog 首屏可见 | SDIO-05 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-paas-domain-mobile-dark-open.png` 危险操作文案可辨认 | SDIO-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 打开态 overlay tablet/mobile light/dark 可见 | SDIO-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 点击「打开伸缩确认」→ 对照 tablet/mobile light/dark 四张打开态截图 → 关闭 Dialog。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | SDIO-01～05 |
| 场景/页面级 | `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` | SDIO-06～10 |

## 交叉引用

- `scenario-domain-viewport-light-dark-screenshot-review-checklist.md` — SDTM-01～05
- `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md` — SDTM-06～10
- `scene-interaction-review-checklist.md` — INTER-06～10
- `decision-matrix.md` — G96 场景域交互态打开态 tablet/mobile light/dark 独立截图选型表
- `upgrade-troubleshooting.md` — SDIO-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域交互态打开态 tablet/mobile light/dark 独立截图检索路径
- `quality-rubric.md` — 综合美学 / 交互与动效质量维度
