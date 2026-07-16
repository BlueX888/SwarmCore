# Scenario Domain Push Channel Cleanup Viewport Light/Dark Screenshot 评审清单

> DOCS-078 / G127 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题推送通道后续清理独立截图视觉回归抽检**，确保每个场景 section 在推送通道清理中态、清理完成态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md`（SDPCCLN-01～05）、`scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md`（SDPCCLN-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域推送通道后续清理 tablet/mobile light/dark 独立截图抽检 | 对应 SDPCCLN 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标推送通道后续清理 tablet/mobile light/dark golden 对照 | SDPCCLN-01 + `scenario-bi-domain-tablet-channel-cleanup-pending.png` + `scenario-bi-domain-mobile-dark-channel-cleanup-complete.png` |
| DevOps 场景阶段推送通道后续清理 tablet/mobile light/dark golden 对照 | SDPCCLN-02 + `scenario-devops-domain-tablet-channel-cleanup-pending.png` + `scenario-devops-domain-mobile-dark-channel-cleanup-complete.png` |
| Gateway 场景端点推送通道后续清理 tablet/mobile light/dark golden 对照 | SDPCCLN-03 + `scenario-gateway-domain-tablet-channel-cleanup-pending.png` + `scenario-gateway-domain-mobile-dark-channel-cleanup-complete.png` |
| Governance 场景审计行推送通道后续清理 tablet/mobile light/dark golden 对照 | SDPCCLN-04 + `scenario-governance-domain-tablet-channel-cleanup-pending.png` + `scenario-governance-domain-mobile-dark-channel-cleanup-complete.png` |
| PaaS 场景容量推送通道后续清理 tablet/mobile light/dark golden 对照 | SDPCCLN-05 + `scenario-paas-domain-tablet-channel-cleanup-pending.png` + `scenario-paas-domain-mobile-dark-channel-cleanup-complete.png` |

## 通用前置

1. 先完成 `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md` SDPCDEST-01～05（推送通道后续销毁独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{channel-cleanup-pending,channel-cleanup-complete}.png` 四视口双主题推送通道后续清理独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 channel-cleanup-pending 与一张 channel-cleanup-complete 独立截图；channel-cleanup-pending 必须出现清理 banner「推送通道后续清理中（销毁后残留清除）」与清理摘要，channel-cleanup-complete 必须出现清理完成 banner「清理已完成，推送通道临时资源已回收，残留索引已清除」与「查看清理详情」CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 推送通道后续清理截图出现文案裁切、清理 banner 对比度不足、channel-cleanup-complete banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域推送通道后续清理 tablet/mobile light/dark 独立截图（G127）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域推送通道后续清理 tablet/mobile light/dark 独立截图抽检行。

## SDPCCLN-01 — BI 场景指标推送通道后续清理 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-channel-cleanup-pending.png`、`scenario-bi-domain-tablet-dark-channel-cleanup-pending.png`、`scenario-bi-domain-mobile-channel-cleanup-pending.png`、`scenario-bi-domain-mobile-dark-channel-cleanup-pending.png`、`scenario-bi-domain-tablet-channel-cleanup-complete.png`、`scenario-bi-domain-tablet-dark-channel-cleanup-complete.png`、`scenario-bi-domain-mobile-channel-cleanup-complete.png`、`scenario-bi-domain-mobile-dark-channel-cleanup-complete.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-cleanup-pending 截图 | `scenario-bi-domain-tablet-channel-cleanup-pending.png` 存在且 channel-cleanup-pending framing 正常 | SDPCCLN-01 · RESP-06 |
| 2 | tablet dark channel-cleanup-pending 截图 | `scenario-bi-domain-tablet-dark-channel-cleanup-pending.png` 存在且清理 banner 可读 | SDPCCLN-01 · VIS-05 |
| 3 | mobile light channel-cleanup-complete 截图 | `scenario-bi-domain-mobile-channel-cleanup-complete.png` channel-cleanup-complete banner 首屏可见 | SDPCCLN-01 · RESP-07 |
| 4 | mobile dark channel-cleanup-complete 截图 | `scenario-bi-domain-mobile-dark-channel-cleanup-complete.png` channel-cleanup-complete 对比度可辨认 | SDPCCLN-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainPushChannelCleanupViewportLightDarkScreenshots` biDomain 全过 | SDPCCLN-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 channel-cleanup-pending 面板 → 点击「触发指标通道清理完成」→ 对照 tablet/mobile light/dark 八张 channel-cleanup-pending/channel-cleanup-complete 截图。

## SDPCCLN-02 — DevOps 场景阶段推送通道后续清理 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-channel-cleanup-pending.png`、`scenario-devops-domain-tablet-dark-channel-cleanup-pending.png`、`scenario-devops-domain-mobile-channel-cleanup-pending.png`、`scenario-devops-domain-mobile-dark-channel-cleanup-pending.png`、`scenario-devops-domain-tablet-channel-cleanup-complete.png`、`scenario-devops-domain-tablet-dark-channel-cleanup-complete.png`、`scenario-devops-domain-mobile-channel-cleanup-complete.png`、`scenario-devops-domain-mobile-dark-channel-cleanup-complete.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-cleanup-pending 截图 | `scenario-devops-domain-tablet-channel-cleanup-pending.png` 存在且 channel-cleanup-pending framing 正常 | SDPCCLN-02 · RESP-06 |
| 2 | tablet dark channel-cleanup-pending 截图 | `scenario-devops-domain-tablet-dark-channel-cleanup-pending.png` 存在且清理摘要可读 | SDPCCLN-02 · VIS-05 |
| 3 | mobile light channel-cleanup-complete 截图 | `scenario-devops-domain-mobile-channel-cleanup-complete.png` 流水线 channel-cleanup-complete 首屏可见 | SDPCCLN-02 · RESP-07 |
| 4 | mobile dark channel-cleanup-complete 截图 | `scenario-devops-domain-mobile-dark-channel-cleanup-complete.png` channel-cleanup-complete 对比度可辨认 | SDPCCLN-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 推送通道后续清理 tablet/mobile light/dark 可见 | SDPCCLN-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 channel-cleanup-pending 面板 → 点击「触发阶段通道清理完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCLN-03 — Gateway 场景端点推送通道后续清理 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-channel-cleanup-pending.png`、`scenario-gateway-domain-tablet-dark-channel-cleanup-pending.png`、`scenario-gateway-domain-mobile-channel-cleanup-pending.png`、`scenario-gateway-domain-mobile-dark-channel-cleanup-pending.png`、`scenario-gateway-domain-tablet-channel-cleanup-complete.png`、`scenario-gateway-domain-tablet-dark-channel-cleanup-complete.png`、`scenario-gateway-domain-mobile-channel-cleanup-complete.png`、`scenario-gateway-domain-mobile-dark-channel-cleanup-complete.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-cleanup-pending 截图 | `scenario-gateway-domain-tablet-channel-cleanup-pending.png` 存在且 channel-cleanup-pending framing 正常 | SDPCCLN-03 · RESP-06 |
| 2 | tablet dark channel-cleanup-pending 截图 | `scenario-gateway-domain-tablet-dark-channel-cleanup-pending.png` 存在且清理摘要可读 | SDPCCLN-03 · VIS-05 |
| 3 | mobile light channel-cleanup-complete 截图 | `scenario-gateway-domain-mobile-channel-cleanup-complete.png` 端点 channel-cleanup-complete 首屏可见 | SDPCCLN-03 · RESP-07 |
| 4 | mobile dark channel-cleanup-complete 截图 | `scenario-gateway-domain-mobile-dark-channel-cleanup-complete.png` channel-cleanup-complete 层级不丢失 | SDPCCLN-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + 推送通道后续清理 tablet/mobile light/dark 可见 | SDPCCLN-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 channel-cleanup-pending 面板 → 点击「触发端点通道清理完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCLN-04 — Governance 场景审计行推送通道后续清理 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-channel-cleanup-pending.png`、`scenario-governance-domain-tablet-dark-channel-cleanup-pending.png`、`scenario-governance-domain-mobile-channel-cleanup-pending.png`、`scenario-governance-domain-mobile-dark-channel-cleanup-pending.png`、`scenario-governance-domain-tablet-channel-cleanup-complete.png`、`scenario-governance-domain-tablet-dark-channel-cleanup-complete.png`、`scenario-governance-domain-mobile-channel-cleanup-complete.png`、`scenario-governance-domain-mobile-dark-channel-cleanup-complete.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-cleanup-pending 截图 | `scenario-governance-domain-tablet-channel-cleanup-pending.png` 存在且 channel-cleanup-pending framing 正常 | SDPCCLN-04 · RESP-06 |
| 2 | tablet dark channel-cleanup-pending 截图 | `scenario-governance-domain-tablet-dark-channel-cleanup-pending.png` 存在且清理摘要可读 | SDPCCLN-04 · VIS-05 |
| 3 | mobile light channel-cleanup-complete 截图 | `scenario-governance-domain-mobile-channel-cleanup-complete.png` 审计 channel-cleanup-complete 首屏可见 | SDPCCLN-04 · RESP-07 |
| 4 | mobile dark channel-cleanup-complete 截图 | `scenario-governance-domain-mobile-dark-channel-cleanup-complete.png` channel-cleanup-complete 密度一致 | SDPCCLN-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + 推送通道后续清理 tablet/mobile light/dark 可见 | SDPCCLN-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 channel-cleanup-pending 面板 → 点击「触发合规通道清理完成」→ 对照 tablet/mobile light/dark 八张截图。

## SDPCCLN-05 — PaaS 场景容量推送通道后续清理 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-channel-cleanup-pending.png`、`scenario-paas-domain-tablet-dark-channel-cleanup-pending.png`、`scenario-paas-domain-mobile-channel-cleanup-pending.png`、`scenario-paas-domain-mobile-dark-channel-cleanup-pending.png`、`scenario-paas-domain-tablet-channel-cleanup-complete.png`、`scenario-paas-domain-tablet-dark-channel-cleanup-complete.png`、`scenario-paas-domain-mobile-channel-cleanup-complete.png`、`scenario-paas-domain-mobile-dark-channel-cleanup-complete.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light channel-cleanup-pending 截图 | `scenario-paas-domain-tablet-channel-cleanup-pending.png` 存在且 channel-cleanup-pending framing 正常 | SDPCCLN-05 · RESP-06 |
| 2 | tablet dark channel-cleanup-pending 截图 | `scenario-paas-domain-tablet-dark-channel-cleanup-pending.png` 存在且清理摘要可读 | SDPCCLN-05 · VIS-05 |
| 3 | mobile light channel-cleanup-complete 截图 | `scenario-paas-domain-mobile-channel-cleanup-complete.png` 容量 channel-cleanup-complete 首屏可见 | SDPCCLN-05 · RESP-07 |
| 4 | mobile dark channel-cleanup-complete 截图 | `scenario-paas-domain-mobile-dark-channel-cleanup-complete.png` channel-cleanup-complete 列表项可辨认 | SDPCCLN-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + 推送通道后续清理 tablet/mobile light/dark 可见 | SDPCCLN-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 channel-cleanup-pending 面板 → 点击「触发容量通道清理完成」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md` SDPCCLN-06～10
- 推送通道后续退役 前置：`scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md` SDPCDEST-01～05
- 选型表：`decision-matrix.md` G127 场景域推送通道后续清理 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDPCCLN-01～10
- Runtime 门禁：`verifyScenarioDomainPushChannelCleanupViewportLightDarkScreenshots`
