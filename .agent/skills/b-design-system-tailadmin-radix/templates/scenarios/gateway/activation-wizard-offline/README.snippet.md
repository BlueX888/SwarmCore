# S02-G04 激活向导（离线）

## 用途

零出站网络（airgap）环境下，通过本地 License 文件完成网关实例激活与验签。适用于离线隔离部署 onboarding。

## 复制入口

```tsx
import { ActivationWizardOfflinePage } from "@/templates/scenarios/gateway/activation-wizard-offline";

<ActivationWizardOfflinePage
  currentStep="airgap"
  onStepChange={(step) => console.log(step)}
  onValidateLicense={() => console.log("validate")}
/>
```

## 页面结构

| 步骤 | 内容 |
|------|------|
| 确认离线环境 | 组织名称、管理员邮箱、实例主机名 + airgap Banner |
| 上传 License | FileUpload + AsyncField 本地验签 |
| 完成激活 | 成功 Alert + 实例 ID 可复制 + License 版本/有效期 |

## 关联 PRD

- `docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g04`
- `references/layout-patterns/activation-wizard.md`
