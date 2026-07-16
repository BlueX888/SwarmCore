# 布局模式 — 企业网关 / 控制平面

典型路由：`/admin/control-plane`、`/settings?tab=sync`、`/gateway?tab=endpoints`

关联：`hub-tabs.md`、`master-detail-ops.md`、`deployment-mode-matrix.md`、`gateway-template.md`

## 适用场景

- 企业网关管控台（connected / airgap 双部署）
- License 签发与续期台
- 同步健康、Endpoint 探测、API Key、余额/配额 Hub

## 结构

```tsx
<AppLayout>
  <PageHeader title="Control Plane" breadcrumbs={…} />
  <ControlPlaneHub
    deploymentMode="connected"
    balance={…}
    quota={…}
    license={…}
    syncTracks={…}
    endpoints={…}
    onProbe={…}
  />
</AppLayout>
```

## 页面分区

| 分区 | 组件 | 说明 |
|---|---|---|
| 部署模式 | DeploymentModeMatrix | 顶部 chip 组，影响下方信息露出 |
| KPI 行 | BalanceQuotaSummary | 余额、配额、License、实例数 |
| 同步健康 | SyncHealthPanel | quota/report/HMAC/heartbeat 四轨 |
| Endpoint 探测 | EndpointProbeTable | 行级 probe + debounce |
| License | LicenseIssuePanel | 签发/续期/一次性展示 |
| API Key | ApiKeyRevealPanel | 创建后一次性 raw_key |

## 状态流

```
部署模式切换 → 隐藏/显示同步与余额区块
主 query loading → 保留 PageHeader + skeleton KPI
块内 error → QueryErrorBlock，不拖垮整页
frozen 配额 → 全局 AlertBanner + 链到 sync Tab
```

## 视觉规则

- 内容区 **全宽**，禁止 `max-w-3xl` 居中
- KPI 行 `grid-cols-4` desktop，`gap-4`，数字 `tabular-nums`
- 同步四轨 `grid-cols-2` tablet+，`gap-3`
- Endpoint 表 `font-mono text-xs` 标识符列，`truncate` + tooltip
- 长 ID、错误文案不得裁切；Badge 须文案 + 色

## 危险操作

- API Key revoke、Endpoint 删除：`AlertDialog` + 对象名
- License 续期失败：块内 hint + 深链 `?tab=license`

## 可复制入口

- 页面组合：`templates/gateway/control-plane-hub.tsx`
- 组件索引：`references/component-styles/gateway-template.md`
