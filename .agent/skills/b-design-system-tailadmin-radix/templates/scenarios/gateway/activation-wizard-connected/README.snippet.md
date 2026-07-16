# S02-G03 激活向导（联网）

## 用途

企业网关首次联网激活：填写网关地址与组织信息 → 连通性探测 → 展示实例 ID 与连接结果。适用于私有化部署 onboarding 与控制面接入。

## 复制入口

```tsx
import { ActivationWizardConnectedPage } from "@/templates/scenarios/gateway/activation-wizard-connected";

<ActivationWizardConnectedPage
  currentStep="form"
  onStepChange={(step) => console.log(step)}
  onProbe={() => console.log("probe")}
/>
```

## 页面结构

| 步骤 | 内容 |
|------|------|
| 填写网关信息 | 网关 URL*、管理员邮箱、组织名称 |
| 验证连通 | AsyncField 探测 + 结果 JSON |
| 完成激活 | 成功 Alert + 实例 ID 可复制 |

## 关联 PRD

- `docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g03`
- `references/layout-patterns/activation-wizard.md`
