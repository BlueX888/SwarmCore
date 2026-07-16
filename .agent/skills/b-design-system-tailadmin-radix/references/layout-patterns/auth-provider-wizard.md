# 布局模式 — Auth Provider Wizard

典型路由：`/settings/auth`、`/admin/identity/providers/new`

关联：`activation-wizard.md`、`governance-template.md`、`templates/governance/auth-provider-wizard.tsx`

## 适用场景

- 企业目录（LDAP/AD）接入
- OAuth/OIDC 联合身份配置
- SAML IdP 元数据导入与断言消费
- 认证源切换前的连通性验证与回滚

## 步骤结构

```tsx
<AuthProviderWizard
  steps={[
    { id: "type", title: "选择认证源" },
    { id: "config", title: "连接配置" },
    { id: "verify", title: "连通性测试" },
    { id: "done", title: "完成" },
  ]}
  currentStep={step}
  providerType="ldap"
  probeState={probeState}
  onProbe={runProbe}
  onRollback={rollbackConfig}
/>
```

## 认证源选型

| 类型 | 何时使用 | 避免 |
|---|---|---|
| LDAP/AD | 内网目录、组映射、已有 AD | 无目录的纯 SaaS 小团队 |
| OAuth 2.0 | 第三方 IdP、授权码模式 | 仅需用户名密码的简单场景 |
| OIDC | 标准发现、JWKS、现代 IdP | 仅 SAML 的老旧 IdP |
| SAML 2.0 | 政企 SAML 元数据对接 | 可用 OIDC 的新系统 |

## 连通性测试

- 使用 `AsyncField`：`idle` → `validating` → `success` / `error`
- 成功页展示可复制 JSON 结果（latency、provider）
- 失败保留已填字段，提供 Retry 与审计日志链接

## 密钥与凭据

- 客户端密钥、绑定密码、SAML 证书使用 `SecretKeyPanel`
- 禁止在向导主步骤长期明文展示
- 轮换/吊销必须二次确认并写审计说明

## 回滚

- 编辑已有认证源时提供「回滚配置」ghost 按钮
- 回滚前 confirm：恢复上一版本元数据与密钥引用
- 回滚失败展示 error Alert，不丢当前 step

## 布局

- 居中 `max-w-2xl` 卡片，步骤条顶部 horizontal
- mobile：步骤标题可简化为 `第 2 步 / 共 4 步`
- 底部 sticky：上一步 outline + 继续 primary

## 截图验收

- 认证源类型选择（LDAP 选中态）
- 连通性测试 success 与 error 两态之一
- SecretKeyPanel 掩码态
- mobile 矩阵/向导不裁切步骤条
