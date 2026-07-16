# 场景级 Override 食谱

> AUDIT-003 / G49 产物。当业务页面需要**跨组件组合 override** 时，先读本文件的 SOR 场景食谱，再查 `api-override-recipes.md` 单项片段。

## 使用顺序

1. 本文件 — 找 BI/DevOps/PaaS 等完整场景 override 组合
2. `api-override-recipes.md` — 单项组件 override 片段
3. `extension-audit.md` — 确认审计状态
4. `decision-matrix.md` — 确认页面/组件选型

## 门控

| 场景 | 要求 |
|---|---|
| 多图表联动 | 每个图表独立 `getBaseChartOptions` override，共享 `chartPaletteCssVars` |
| 看板 + 流水线 | Kanban 受控 `columns` + loading/error 与 PipelineStageBar 状态对齐 |
| 地图 + 热力 | MapLibre center/zoom 与 Vector Map regionStyle 使用同一地理语义 |
| 嵌套 options | 优先 `deepMergeOptions` / `mergeSwiperOptionsDeep`；选型见 `merge-options-guide.md` |

---

## SOR-01 — BI 联动仪表盘（筛选 + 图表色板）

**适用**：`templates/bi/cross-filter-dashboard.tsx`、`templates/bi/filter-bar.tsx`

```ts
import {
  getBaseChartOptions,
  createBarChartOptions,
  chartPaletteCssVars,
} from "@/lib/chart-theme";

// 全局筛选变更时，仅 override 色板与系列名，保留 toolbar/legend 默认
const revenueOptions = createBarChartOptions({
  colors: [chartPaletteCssVars.brand, chartPaletteCssVars.info],
  series: [{ name: "收入", data: filteredRevenue }],
  xaxis: { categories: filteredMonths },
});

const conversionOptions = getBaseChartOptions({
  chart: { id: "conversion-rate", toolbar: { show: false } },
  colors: [chartPaletteCssVars.success],
  yaxis: {
    labels: {
      formatter: (val: number) => `${val}%`,
    },
  },
});

// 降级：筛选 chips + StatMetric 静态 KPI 卡片
```

**常见 override**：`colors`、`series`、`xaxis.categories`、`yaxis.labels.formatter`；筛选状态通过 props 传入，不写死在 theme lib。

**选型**：cross-filter 用 `CrossFilterDashboard` + `FilterBar`；单图 drill-down 用 `DrillDownDashboard`（见 `decision-matrix.md#bi`）。对应预防性场景 MS-11。

---

## SOR-02 — DevOps 发布看板（Kanban + 流水线阶段）

**适用**：`templates/devops/cicd-run-detail.tsx`、`templates/ui/kanban-board.tsx`

```tsx
import { KanbanBoard, type KanbanColumnData } from "@/components/ui/kanban-board";
import { PipelineStageBar } from "@/components/devops/pipeline-stage-bar";

const [columns, setColumns] = useState<KanbanColumnData[]>(releaseColumns);
const [loading, setLoading] = useState(false);

<PipelineStageBar
  stages={pipelineStages}
  currentStageId={activeStage}
  onStageClick={scrollToColumn}
/>

<KanbanBoard
  columns={columns}
  loading={loading}
  error={deployError?.message}
  onTaskMove={(taskId, from, to) => moveReleaseTask(taskId, from, to)}
  onColumnAction={(columnId, action) => handleColumnMenu(columnId, action)}
  onAddTask={(columnId) => openHotfixDialog(columnId)}
  className="min-h-[520px]"
/>

// 降级：PipelineStageBar + Table 按状态列展示任务
```

**常见 override**：受控 `columns`、列标题/status 映射、`loading`/`error` 文案、`onTaskMove` 权限门控、`className` 最小高度。

**选型**：CI/CD 详情用 `CicdRunDetail`；纯任务管理用 `KanbanBoard`；旧 DnD 壳用 `KanbanLegacyShell`（MN-03）。对应预防性场景 MS-10。

---

## SOR-03 — PaaS 资源监控（MapLibre + Vector 热力）

**适用**：`templates/paas/resource-table.tsx`、`templates/lib/maps-theme.ts`、`templates/lib/vector-map-theme.ts`

```ts
import {
  mergeMapLibreOptions,
  mapCardShellClass,
  mapContainerClass,
} from "@/lib/maps-theme";
import {
  trafficRegionStyle,
  createTrafficRegionStyleInjector,
  createVectorMapZoomHandlers,
} from "@/lib/vector-map-theme";

// 同一数据中心：MapLibre 精确定位 + Vector 区域热力
const mapOptions = mergeMapLibreOptions({
  center: [116.4074, 39.9042],
  zoom: 11,
});

const regionOverride = {
  ...trafficRegionStyle,
  CN: { fill: "#465FFF" },
  US: { fill: "#12B76A" },
};

const { onRegionTipShow, onRegionSelected } = createTrafficRegionStyleInjector();
const zoomHandlers = createVectorMapZoomHandlers(mapRef);

// 降级：ResourceTable 地区列 + 静态地图截图 Card
```

**常见 override**：`center`/`zoom`、`regionStyle` preset 复制后改 fill、`onRegionTipShow` tooltip 文案。

**选型**：资源列表 + 地图卡片用 PaaS `ResourceTable` + Maps section；纯热力分布用 Vector Maps；单点定位用 MapLibre Card。对应预防性场景 MS-12。

---

## SOR-04 — 治理安全控制台（权限矩阵 + 审计日志 + 认证向导）

**适用**：`templates/governance/permission-matrix.tsx`、`templates/governance/audit-log-table.tsx`、`templates/governance/auth-provider-wizard.tsx`

```tsx
import { PermissionMatrix } from "@/components/governance/permission-matrix";
import { AuditLogTable } from "@/components/governance/audit-log-table";
import { AuthProviderWizard } from "@/components/governance/auth-provider-wizard";
import { ComplianceAlert } from "@/components/governance/compliance-alert";

const [selectedRole, setSelectedRole] = useState("安全管理员");
const [auditQuery, setAuditQuery] = useState("");
const [wizardStep, setWizardStep] = useState(0);
const [probeState, setProbeState] = useState<AsyncFieldState>("idle");

<ComplianceAlert
  level="warning"
  title="权限变更将写入审计日志"
  description="批量勾选权限前请确认影响范围，高危操作需二次确认。"
/>

<PermissionMatrix
  roles={roles}
  permissions={permissions}
  selectedRole={selectedRole}
  onRoleChange={(role) => {
    setSelectedRole(role);
    setAuditQuery(role);
  }}
  onToggle={(resource, action, granted) =>
    updatePermission(selectedRole, resource, action, granted)
  }
  readOnly={!canEditRbac}
/>

<AuditLogTable
  rows={filterAuditRows(rows, auditQuery)}
  loading={auditLoading}
  onSearch={setAuditQuery}
  onExport={exportAuditCsv}
  onRowClick={openAuditDetailDrawer}
/>

<AuthProviderWizard
  currentStep={wizardStep}
  onStepChange={setWizardStep}
  providerType={providerType}
  onProviderTypeChange={setProviderType}
  probeState={probeState}
  onProbe={async () => {
    setProbeState("validating");
  }}
  onRollback={rollbackDraftConfig}
  onComplete={commitAuthProvider}
/>

// 降级：ComplianceAlert + 简单 Table 展示最近 10 条审计
```

**常见 override**：`selectedRole` 与审计筛选联动、`readOnly` 门控、`probeState` 连通性探测、`onRollback` 草稿回滚；权限冲突行由 `PermissionMatrix` 内置 `conflict` 标记。

**选型**：RBAC 批量勾选用 `PermissionMatrix`；审计追溯用 `AuditLogTable`；新增 LDAP/OAuth/OIDC/SAML 用 `AuthProviderWizard`；密钥轮换用 `SecretKeyPanel`（见 `decision-matrix.md#治理安全`）。对应预防性场景 MS-13。

---

## SOR-05 — 企业网关控制平面（部署模式 + 同步健康 + 端点探测）

**适用**：`templates/gateway/control-plane-hub.tsx` 及子面板

```tsx
import { ControlPlaneHub } from "@/components/gateway/control-plane-hub";
import type { DeploymentMode } from "@/components/gateway/deployment-mode-matrix";

const [mode, setMode] = useState<DeploymentMode>("connected");
const [showSync, setShowSync] = useState(true);

<ControlPlaneHub
  deploymentMode={mode}
  onDeploymentModeChange={setMode}
  balanceCents={balance}
  quotaPercent={quotaPct}
  showSync={showSync}
  showBalance={mode !== "airgap"}
  syncTracks={syncTracks}
  endpoints={endpoints}
  onProbe={probeEndpoint}
  onSyncRetry={retrySyncTrack}
  issuedLicense={license}
  rawApiKey={apiKey}
/>

// 降级：单独使用 DeploymentModeMatrix + EndpointProbeTable
```

**常见 override**：`showSync`/`showBalance` 按部署模式显隐、`onProbe` debounce、`syncTracks` 四轨或自定义轨、`degradedCount` KPI 联动。

**选型**：控制平面总览用 `ControlPlaneHub`；仅部署模式选择用 `DeploymentModeMatrix`；License/API Key 独立面板用 `LicenseIssuePanel` / `ApiKeyRevealPanel`（见 `decision-matrix.md#控制平面`）。对应预防性场景 MS-09。

---

## 检索入口

| 意图 | 读 |
|---|---|
| 场景组合 override | 本文件 SOR-01～05 |
| 单项组件 override | `api-override-recipes.md` |
| 嵌套 merge helper | `templates/lib/merge-options.ts` |
| 审计与门控 | `extension-audit.md` |
