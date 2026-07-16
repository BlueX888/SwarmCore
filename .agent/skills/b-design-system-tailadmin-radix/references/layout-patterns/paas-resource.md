# 布局模式 — PaaS 资源管理

适用：Kubernetes、Elasticsearch、MySQL、Redis、消息队列、对象存储、API 网关等中后台管理。

## 页面类型

| 页面 | 模式 | 说明 |
|---|---|---|
| Resource Overview | Dashboard | 集群/服务健康与容量 |
| Resource List | Table List | namespace、状态、版本、规格、用量 |
| Resource Detail | Detail Page | metrics/events/logs/config tabs |
| Create Resource | Form Flow | 规格、网络、存储、备份、安全 |
| Backup / Restore | Detail + Form | 备份列表、恢复确认 |

## Resource Detail 结构

```tsx
<AppLayout>
  <div className="flex flex-col gap-6">
    <PageHeader title="mysql-prod-01" status={<Badge>Running</Badge>} />
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard label="CPU" />
      <MetricCard label="Memory" />
      <MetricCard label="Storage" />
      <MetricCard label="Connections" />
    </div>
    <Tabs>{/* Metrics / Events / Logs / Config / Backups */}</Tabs>
  </div>
</AppLayout>
```

## K8s 页面组合

- Cluster list：版本、节点数、健康、CPU/Memory 使用率
- Namespace detail：workloads、services、ingress、events
- Pod detail：containers、logs、events、YAML
- Workload scale：replicas stepper + confirm

## ES/MySQL 页面组合

- Instance list：版本、规格、状态、存储、QPS、连接数
- Detail tabs：Metrics、Slow queries、Logs、Backups、Parameters
- 参数变更：diff + 重启提示 + maintenance window
- 备份恢复：目标时间点 + 风险确认

## 场景组件

| 组件 | 用途 | 状态 | 模板 |
|---|---|---|---|
| ResourceTable | 资源列表 | running/degraded/stopped/creating/failed/maintenance | `templates/paas/resource-table.tsx` |
| CapacityCard | CPU/Memory/Disk/QPS/Latency/Replica | normal/warning/critical | `templates/paas/capacity-card.tsx` |
| EventTimeline | K8s events / DB events | warning/error/info | 复用 `templates/devops/log-stream-panel.tsx` |
| ConfigDiff | 参数、YAML、策略变化 | added/removed/changed | `templates/paas/config-diff.tsx` |
| LogStreamPanel | Pod/DB 日志 | streaming/search/filter | `templates/devops/log-stream-panel.tsx` |
| PaasOpsDangerFlow | 伸缩/重启/故障转移 | scale/restart/failover + 二次确认 | `templates/paas/ops-danger-flow.tsx` |
| BackupTable | 备份点 | available/expired/restoring/failed | `templates/paas/backup-table.tsx` |

详情规则见 `references/component-styles/paas-template.md`。

## 危险操作

- Restart、Delete、Force failover、Restore backup、Scale down to zero 必须二次确认。
- 确认文案必须包含资源名、namespace/tenant、目标环境。
- 政府/企业场景建议要求填写变更原因并写入审计日志。

## 视觉验收

- 资源详情 tabs 下方内容不能因日志/配置长文本撑破布局。
- 容量卡数字、单位、趋势 badge 不可裁切。
- 表格列在 1440px 下应充分利用宽度；长资源名截断 + tooltip。
