# 预防性迁移场景与兼容食谱

> COMPAT-002 产物。记录**尚未发生**但业务项目常见的契约风险场景，以及推荐迁移路径。发生真实破坏性变更时，复制 `migration-note-template.md` 填写正式 migration note。

## 场景索引

| ID | 场景 | 风险 | 推荐动作 |
|---|---|---|---|
| MS-01 | ThemeToggle 导出名 vs 概念名 | 低 | 业务层 alias → [MN-01](migration-notes/MN-01-theme-toggle-alias.md) |
| MS-02 | SearchCommand 依赖 react-router | 低 | 传 `onItemSelect` → [MN-02](migration-notes/MN-02-search-command-no-router.md) |
| MS-03 | Kanban 自建 DnD → KanbanBoard | 中 | 迁移到受控 columns API → [MN-03](migration-notes/MN-03-kanban-legacy-board.md) |
| MS-04 | Chart 硬编码 palette key | 低 | 使用 `getBaseChartOptions` overrides → [迁移手册](migration-playbook.md#场景路由表) · `api-override-recipes.md` |
| MS-05 | FullCalendar 无 overrides 参数 | 低 | 改用 `getDefaultFullCalendarOptions(overrides?)` → [迁移手册](migration-playbook.md#场景路由表) |
| MS-06 | FileUpload 需拖拽多文件 | 低 | additive 接入 `FileDropzone` → [迁移手册](migration-playbook.md#场景路由表) |
| MS-07 | Editor 只读 → 可编辑 | 低 | additive 接入 `CodeEditor` → [迁移手册](migration-playbook.md#场景路由表) |
| MS-08 | 无路由的 Command 搜索 | 低 | `ComboboxPanel` 或 `onSelect` → [迁移手册](migration-playbook.md#场景路由表) |
| MS-09 | Gateway 控制平面组合升级 | 低 | 子面板 props 均为 optional → [SOR-05](scenario-override-recipes.md#sor-05--企业网关控制平面部署模式--同步健康--端点探测) |
| MS-10 | DevOps CI/CD 页面组合升级 | 低 | `CicdRunDetail` 数据 props 受控 → [SOR-02](scenario-override-recipes.md#sor-02--devops-发布看板kanban--流水线阶段) |
| MS-11 | BI 联动仪表盘 cross-filter | 低 | 筛选 chips + 图表色板受控 → [SOR-01](scenario-override-recipes.md#sor-01--bi-联动仪表盘筛选--图表色板) |
| MS-12 | PaaS 资源监控地图热力 | 低 | MapLibre + Vector 同一地理语义 → [SOR-03](scenario-override-recipes.md#sor-03--paas-资源监控maplibre--vector-热力) |
| MS-13 | 治理安全控制台组合升级 | 低 | RBAC + 审计 + 认证向导受控 props → [SOR-04](scenario-override-recipes.md#sor-04--治理安全控制台权限矩阵--审计日志--认证向导) |

---

## MS-01 — ThemeToggle 导出名

**问题**：索引与文档称 `ThemeToggle`，代码导出 `ThemeToggleButton`。

**旧用法**（若未来统一导出名可能破坏）：

```tsx
import { ThemeToggleButton } from "@/components/layout/theme-toggle";
```

**推荐兼容写法**：

```tsx
// 业务 components/theme-toggle.tsx
export { ThemeToggleButton as ThemeToggle } from "@/components/layout/theme-toggle";
```

**影响**：仅 import 路径；props `className` / `aria-label` 不变。

---

## MS-02 — SearchCommand 无 react-router

**问题**：`SearchCommand` 默认 `href` 跳转依赖 `useNavigate`。

**旧用法**：

```tsx
<SearchCommand groups={groups} />  // 项带 href
```

**推荐迁移**：

```tsx
<SearchCommand
  groups={groups}
  onSelect={(item) => {
    if (item.href) window.location.assign(item.href);
    else item.onAction?.();
  }}
/>
```

**降级**：简单 `<Input type="search">` + 本地 filter。

---

## MS-03 — Kanban 自建板 → KanbanBoard

**问题**：G33 前项目仅用 `kanban-theme.ts` class 常量自建 DnD。

**旧用法**：

```tsx
import { kanbanBoardGridClass } from "@/lib/kanban-theme";
// 自建列与卡片 DOM
```

**推荐迁移**：

```tsx
import { KanbanBoard, type KanbanColumnData } from "@/components/ui/kanban-board";

<KanbanBoard
  columns={columns}
  onTaskMove={handleMove}
  onColumnAction={handleColumnAction}
/>
```

**兼容**：`kanban-theme.ts` 全部 class 常量仍 stable，可继续用于自定义 DOM。

---

## MS-04 — Chart palette 扩展

**问题**：业务硬编码 `chartPalette.purple`；演化删除 key 会 breaking。

**推荐**：

```tsx
import { getBaseChartOptions, chartPalette } from "@/lib/chart-theme";

const color = chartPalette.brand ?? "#465fff";
getBaseChartOptions({ colors: [color], chart: { id: "revenue" } });
```

**降级**：`StatMetric` + `MetricCard` 静态 KPI。

---

## MS-05 — FullCalendar overrides

**G45 additive**：`getDefaultFullCalendarOptions(overrides?)` 支持浅 merge。

```tsx
// 旧：手动 spread 默认对象
// 新：
import { getDefaultFullCalendarOptions } from "@/lib/fullcalendar-theme";

getDefaultFullCalendarOptions({
  initialView: "timeGridWeek",
  editable: true,
});
```

---

## MS-06 — FileUpload → FileDropzone

**场景**：单文件 `FileUpload` 够用；批量拖拽需 additive `FileDropzone`。

```tsx
// 简单场景 — 保持 FileUpload
<FileUpload label="上传证书" accept=".pem" />

// 批量拖拽 — additive，不替换 FileUpload
<FileDropzone
  files={files}
  onFilesSelected={setFiles}
  maxSizeMb={10}
  multiple
/>
```

---

## MS-07 — CodeBlock → CodeEditor

**场景**：只读展示用 `CodeBlock`；需编辑时用 G40 additive `CodeEditor`。

```tsx
<CodeBlock language="tsx" code={snippet} onEdit={() => setMode("edit")} />
{mode === "edit" && (
  <CodeEditor value={snippet} onChange={setSnippet} mode="split" onSave={handleSave} />
)}
```

---

## MS-08 — 无路由 Command 搜索

**降级路径**：

```tsx
import { ComboboxPanel } from "@/components/ui/search-command";

<ComboboxPanel
  options={options}
  value={value}
  onValueChange={setValue}
  placeholder="搜索服务…"
/>
```

---

## MS-09 — Gateway ControlPlaneHub 子面板

**契约**：`ControlPlaneHub` 所有 KPI/sync/endpoints props 均为 optional，带中文默认 mock。

```tsx
<ControlPlaneHub
  deploymentMode={mode}
  onDeploymentModeChange={setMode}
  showSync={hasSync}
  onProbe={handleProbe}
/>
```

**降级**：单独使用 `DeploymentModeMatrix`、`EndpointProbeTable` 等子组件。

**业务验证**：见 `business-validation-checklist.md#ms-09`。

---

## MS-10 — DevOps CicdRunDetail

**契约**：`stages`、`logs`、`artifacts` 受控传入；`onRetry`/`onCancel`/`onDangerAction` 可选。

```tsx
<CicdRunDetail
  runId={run.id}
  stages={stages}
  logs={logs}
  artifacts={artifacts}
  onRetry={refetch}
  onDangerAction={handleDanger}
/>
```

**降级**：`PipelineStageBar` + `LogStreamPanel` 独立组合。

**业务验证**：见 `business-validation-checklist.md#ms-10`。

---

## MS-11 — BI 联动仪表盘 cross-filter

**契约**：`CrossFilterDashboard` 筛选状态通过 props 传入；各图表独立 `getBaseChartOptions` override，共享 `chartPaletteCssVars`。

```tsx
<CrossFilterDashboard
  filters={activeFilters}
  onFilterChange={setActiveFilters}
  revenueSeries={filteredRevenue}
  conversionSeries={filteredConversion}
  onDrillDown={openDrillDetail}
/>
```

**降级**：`FilterBar` chips + `StatMetric` 静态 KPI 卡片，不联动图表色板。

**业务验证**：见 `business-validation-checklist.md#ms-11`。

---

## MS-12 — PaaS 资源监控地图热力

**契约**：`ResourceTable` 地区列与 MapLibre `center`/`zoom`、Vector `regionStyle` 使用同一数据中心语义。

```tsx
<ResourceTable
  rows={resources}
  regionFilter={selectedRegion}
  onRegionChange={setSelectedRegion}
  mapCenter={datacenterCenter}
  mapZoom={11}
  onMapRegionSelect={syncTableFilter}
/>
```

**降级**：`ResourceTable` 地区列 + 静态地图截图 Card，不联动 Vector 热力。

**业务验证**：见 `business-validation-checklist.md#ms-12`。

---

## MS-13 — 治理安全控制台组合升级

**契约**：`PermissionMatrix`、`AuditLogTable`、`AuthProviderWizard` 的 `selectedRole`、`auditQuery`、`wizardStep`、`probeState` 均为受控 props。

```tsx
<PermissionMatrix
  selectedRole={role}
  onRoleChange={(r) => {
    setRole(r);
    setAuditQuery(r);
  }}
  readOnly={!canEditRbac}
/>
<AuditLogTable rows={rows} loading={loading} onSearch={setAuditQuery} />
<AuthProviderWizard
  currentStep={step}
  probeState={probeState}
  onProbe={runConnectivityTest}
/>
```

**降级**：`ComplianceAlert` + 简单 Table 展示最近 10 条审计。

**业务验证**：见 `business-validation-checklist.md#ms-13`。

---

## 验证

升级或复制模板后，运行：

```bash
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
```

场景路由与升级检查清单见 `migration-playbook.md`。MS-09～13 业务冒烟见 `business-validation-checklist.md`。

业务侧补充 `tsc --noEmit` 与关键页面截图对比。
