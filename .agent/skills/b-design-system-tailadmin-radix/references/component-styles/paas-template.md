# PaaS 资源管理组件模板

技术栈：**React + shadcn/ui + Radix + Tailwind v4**

## 读取顺序

1. `references/layout-patterns/paas-resource.md` — K8s/ES/MySQL/Redis 页面结构
2. `references/decision-matrix.md` — 资源列表 vs 详情 vs 危险操作选型
3. 本文件选可复制模板
4. `references/layout-patterns/ops-monitoring.md` — 监控指标与告警联动

## 场景组件

| 组件 | 状态覆盖 | 模板 |
|---|---|---|
| ResourceTable | running/degraded/stopped/creating/failed/maintenance | `templates/paas/resource-table.tsx` |
| CapacityCard | normal/warning/critical · CPU/Memory/Disk/QPS/Latency/Replica | `templates/paas/capacity-card.tsx` |
| ConfigDiff | added/removed/changed + 重启/风险 | `templates/paas/config-diff.tsx` |
| BackupTable | available/expired/restoring/failed + 恢复确认 | `templates/paas/backup-table.tsx` |
| PaasOpsDangerFlow | scale/restart/failover + 二次确认 | `templates/paas/ops-danger-flow.tsx` |

## 页面组合建议

| 场景 | 推荐结构 | 不要使用 |
|---|---|---|
| 资源总览 | CapacityCard 栅格 + ResourceTable | 单卡占位无列表 |
| 实例详情 | PageHeader + CapacityCard + Tabs（指标/日志/配置/备份） | 所有信息堆在一屏 |
| 参数变更 | ConfigDiff + 维护窗口提示 | 无 diff 直接提交 |
| 备份恢复 | BackupTable + RestoreConfirmDialog | 一键恢复无确认 |
| 伸缩/重启/故障转移 | PaasOpsDangerFlow + 审计说明 | 普通 Button 直接执行 |

## 视觉验收

- ResourceTable：长资源名 `truncate` + tooltip；Namespace 列 `font-mono`；1440px 下表格应充分利用宽度。
- CapacityCard：数字 `tabular-nums`；百分比与单位不可裁切；预警/严重态使用语义 Badge。
- ConfigDiff：参数键 `font-mono`；before/after 列横向滚动；高风险变更必须有 Alert。
- BackupTable：恢复按钮仅 `available` 可点；确认对话框必须包含资源名与 namespace。
- PaasOpsDangerFlow：危险区使用 error 边框/底色；确认输入必须匹配资源名。

## 组合示例

```tsx
import { ResourceTable } from "@/components/paas/resource-table";
import { CapacityCard } from "@/components/paas/capacity-card";
import { ConfigDiff } from "@/components/paas/config-diff";
import { BackupTable } from "@/components/paas/backup-table";
import { PaasOpsDangerFlow } from "@/components/paas/ops-danger-flow";
```
