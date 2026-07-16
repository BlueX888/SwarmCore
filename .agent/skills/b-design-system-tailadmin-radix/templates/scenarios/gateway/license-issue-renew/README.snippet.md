# S02-G05 License 签发续期

## 用途

SaaS 运营台为企业网关实例代签离线 License，支持一次性复制交付、粘贴续期验签，以及危险区确认吊销/强制续期。

## 复制入口

```tsx
import { LicenseIssueRenewPage } from "@/templates/scenarios/gateway/license-issue-renew";

<LicenseIssueRenewPage
  onIssue={() => console.log("issue")}
  onRenew={(license) => console.log("renew", license)}
  onDangerAction={(id) => console.log("danger", id)}
/>
```

## 页面结构

| 区块 | 组件 | 说明 |
|------|------|------|
| KPI 摘要 | 四格卡片 | 版本、状态、有效期、绑定实例 |
| 签发 | LicenseIssuePanel `mode="issue"` | 签发新 License + 一次性复制 |
| 续期 | LicenseIssuePanel `mode="renew"` | 粘贴 License + 验证续期 |
| 危险操作 | DangerZone | 吊销 / 强制覆盖续期（对象名确认） |
| 审计表 | 内联表格 | 签发/续期/吊销留痕 |

## 关联 PRD

- `docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g05`
- `references/layout-patterns/control-plane.md`
- `templates/gateway/license-issue-panel.tsx`
- `templates/devops/danger-zone.tsx`
