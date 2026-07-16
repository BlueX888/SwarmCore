# 部署模式矩阵 — 企业网关 / 控制平面

```yaml
scope: control-plane-abstract
demand_ref: ../../docs/demand/gateway.md
visual_ref: gateway-visual.md
interaction_ref: gateway-interaction.md
last_updated: 2026-06-25
```

> 将 connected / airgap / local / cloud / private 等部署模式抽象为通用控制平面能力，**不**把具体产品名或路由写入默认规则。

## 模式定义

| 模式 ID | 标签 | 出站 | 同步 | 典型场景 |
|---|---|---|---|---|
| `connected` | Connected | 允许 | quota/report/HMAC/heartbeat | 企业内网连集中端，余额池同步 |
| `airgap` | Airgap | 禁止 | 无 | 零出站、本地 License 验签 |
| `local` | Local | 可选 | 无 | 单机/边缘节点，本地 Endpoint |
| `cloud` | Cloud | 允许 | 可选 | 公有云托管控制面 |
| `private` | Private Cloud | 受限 | 可选 | 私有化 VPC 内控制面 |

## 模式分叉规则

| 能力 | connected | airgap | local/cloud/private |
|---|---|---|---|
| 同步健康台 | 显示四轨 | 隐藏 | 按配置显示 |
| 余额/企业池 | 显示 | 隐藏 | 按计费模型 |
| License 续期 | 在线验签 | 离线粘贴 | 按模式 |
| Endpoint 探测 | 行级 debounce 300ms | 本地 only | 同左 |
| API Key 创建 | 一次性展示 | 同左 | 同左 |

## 视觉规则

- 模式选择用 **chip 组** 或 **RadioGroup**，选中态 `brand-50` 底 + `brand-500` 边框
- 激活向导中模式 **单选后不可改**，须二次确认文案
- airgap 选中时显示 `info` AlertBanner：「零出站，用量不出内网」
- connected 选中时显示 `info` AlertBanner：「余额与配额由集中端同步」

## 可复制模板

| 组件 | 模板 |
|---|---|
| DeploymentModeMatrix | `templates/gateway/deployment-mode-matrix.tsx` |
| ControlPlaneHub | `templates/gateway/control-plane-hub.tsx` |

## 相关文档

| 文档 | 用途 |
|---|---|
| `gateway-visual.md` | 语义色与密度 |
| `gateway-interaction.md` | 分叉交互与守卫 |
| `layout-patterns/control-plane.md` | 控制平面页面结构 |
| `component-styles/gateway-template.md` | 组件索引 |
