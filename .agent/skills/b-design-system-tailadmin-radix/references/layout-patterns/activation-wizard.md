# 布局模式 — Activation Wizard

典型路由：`/onboarding`、`/gateway/activate`、`/cluster/connect`

关联：`form-flow.md`、`hub-tabs.md`、`templates/ui/async-field` 族

## 适用场景

- 私有化部署激活（License + 连通性）
- 集群接入向导（Endpoint + Credential + Test）
- SaaS 租户开通（Plan → Payment → Provision）

## 步骤结构

```tsx
<ActivationWizard
  steps={[
    { id: "mode", title: "Deployment mode" },
    { id: "connect", title: "Connectivity" },
    { id: "verify", title: "Verify" },
    { id: "done", title: "Complete" },
  ]}
  currentStep={step}
  onStepChange={setStep}
/>
```

## 部署模式步骤

- 卡片单选：Cloud / On-prem / Hybrid
- 每卡片：图标 + 标题 + 2 行说明 + 选中 ring
- 选中后展示条件字段（License key、Proxy URL）

## 连通性测试

```tsx
<AsyncField
  label="Cluster endpoint"
  value={endpoint}
  status={probeStatus} // idle | validating | success | error
  onValidate={runProbe}
/>
```

| 探测状态 | UI |
|---|---|
| idle | Test connection outline Button |
| validating | input 右侧 Spinner + disabled submit |
| success | success Alert + 可复制结果 JSON |
| error | error Alert + 原因 + Retry + 查看日志链接 |

## 结果复制

- 成功页展示 `Connection ID` + `Copy` Button + `toast.success`
- 敏感值默认 mask，Reveal 需二次点击
- 提供「Download config」outline 导出

## 失败恢复

- 步骤内错误不丢已填字段
- 网络失败保留 step index，Retry 从当前探测重试
- 致命错误提供「Start over」destructive + confirm

## 布局

- 居中 `max-w-2xl` 卡片，步骤条顶部 horizontal
- 底部 sticky actions：Back outline + Continue primary
- mobile：步骤条简化为 `Step 2 of 4`

## 视觉

- 进度：`completed` 勾、`current` brand、`pending` muted
- 禁止全屏装饰 hero；信息密度优先

## 截图验收

- 探测 success 与 error 两态（或 success + validating）
- 结果区可复制块不溢出
- 步骤条在 mobile 不裁切
