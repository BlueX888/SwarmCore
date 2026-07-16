import * as React from "react";
import { cn } from "@/lib/utils";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AsyncField, type AsyncFieldState } from "@/components/ui/async-field";
import { Check, ChevronLeft, ChevronRight, KeyRound, Shield, Users } from "lucide-react";

export type AuthProviderType = "ldap" | "oauth" | "oidc" | "saml";

export type AuthProviderStep = {
  id: string;
  title: string;
};

export type AuthProviderWizardProps = {
  steps?: AuthProviderStep[];
  currentStep?: number;
  onStepChange?: (index: number) => void;
  providerType?: AuthProviderType;
  onProviderTypeChange?: (type: AuthProviderType) => void;
  probeState?: AsyncFieldState;
  onProbe?: () => void;
  onRollback?: () => void;
  onComplete?: () => void;
  readOnly?: boolean;
  className?: string;
};

const defaultSteps: AuthProviderStep[] = [
  { id: "type", title: "选择认证源" },
  { id: "config", title: "连接配置" },
  { id: "verify", title: "连通性测试" },
  { id: "done", title: "完成" },
];

const providerOptions: Array<{
  id: AuthProviderType;
  label: string;
  description: string;
  icon: React.ReactNode;
}> = [
  {
    id: "ldap",
    label: "LDAP / AD",
    description: "企业目录服务，支持绑定 DN 与组映射。",
    icon: <Users className="size-4" />,
  },
  {
    id: "oauth",
    label: "OAuth 2.0",
    description: "授权码模式，适合第三方 IdP 接入。",
    icon: <KeyRound className="size-4" />,
  },
  {
    id: "oidc",
    label: "OpenID Connect",
    description: "标准 OIDC 发现与 JWKS 校验。",
    icon: <Shield className="size-4" />,
  },
  {
    id: "saml",
    label: "SAML 2.0",
    description: "元数据上传与断言消费端点配置。",
    icon: <Shield className="size-4" />,
  },
];

const configFields: Record<AuthProviderType, Array<{ key: string; label: string; placeholder: string }>> = {
  ldap: [
    { key: "host", label: "LDAP 主机", placeholder: "ldap://corp.example.com:389" },
    { key: "bindDn", label: "绑定 DN", placeholder: "cn=admin,dc=corp,dc=example,dc=com" },
    { key: "baseDn", label: "用户搜索基准", placeholder: "ou=users,dc=corp,dc=example,dc=com" },
  ],
  oauth: [
    { key: "clientId", label: "客户端 ID", placeholder: "gov-oauth-client" },
    { key: "authUrl", label: "授权端点", placeholder: "https://idp.example.com/oauth/authorize" },
    { key: "tokenUrl", label: "令牌端点", placeholder: "https://idp.example.com/oauth/token" },
  ],
  oidc: [
    { key: "issuer", label: "Issuer", placeholder: "https://idp.example.com" },
    { key: "clientId", label: "客户端 ID", placeholder: "gov-oidc-client" },
    { key: "redirectUri", label: "回调地址", placeholder: "https://console.example.com/auth/callback" },
  ],
  saml: [
    { key: "entityId", label: "实体 ID", placeholder: "urn:gov:console:sp" },
    { key: "ssoUrl", label: "SSO 端点", placeholder: "https://idp.example.com/saml/sso" },
    { key: "metadata", label: "IdP 元数据 URL", placeholder: "https://idp.example.com/metadata.xml" },
  ],
};

/**
 * 认证源配置向导 — LDAP/OAuth/OIDC/SAML、连通性测试、回滚。
 * @see references/layout-patterns/auth-provider-wizard.md
 */
export function AuthProviderWizard({
  steps = defaultSteps,
  currentStep = 0,
  onStepChange,
  providerType = "ldap",
  onProviderTypeChange,
  probeState = "idle",
  onProbe,
  onRollback,
  onComplete,
  readOnly = false,
  className,
}: AuthProviderWizardProps) {
  const step = steps[currentStep] ?? steps[0];
  const isFirst = currentStep <= 0;
  const isLast = currentStep >= steps.length - 1;

  const goBack = () => onStepChange?.(Math.max(0, currentStep - 1));
  const goNext = () => onStepChange?.(Math.min(steps.length - 1, currentStep + 1));

  return (
    <section
      className={cn("mx-auto w-full max-w-2xl space-y-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900", className)}
      aria-label="认证源配置向导"
    >
      <ol className="flex flex-wrap items-center gap-2" aria-label="向导步骤">
        {steps.map((item, index) => {
          const done = index < currentStep;
          const active = index === currentStep;
          return (
            <li key={item.id} className="flex items-center gap-2">
              <span
                className={cn(
                  "inline-flex size-7 items-center justify-center rounded-full text-xs font-semibold",
                  done && "bg-success-500 text-white",
                  active && !done && "bg-brand-500 text-white",
                  !done && !active && "bg-gray-100 text-gray-500 dark:bg-white/5 dark:text-gray-400",
                )}
                aria-current={active ? "step" : undefined}
              >
                {done ? <Check className="size-3.5" /> : index + 1}
              </span>
              <span className={cn("text-theme-sm font-medium", active ? "text-gray-900 dark:text-white" : "text-gray-500")}>
                {item.title}
              </span>
              {index < steps.length - 1 ? (
                <span className="hidden text-gray-300 sm:inline dark:text-gray-700" aria-hidden="true">
                  /
                </span>
              ) : null}
            </li>
          );
        })}
      </ol>

      <div className="space-y-4">
        {step.id === "type" ? (
          <div className="grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label="认证源类型">
            {providerOptions.map((option) => {
              const active = providerType === option.id;
              return (
                <button
                  key={option.id}
                  type="button"
                  role="radio"
                  aria-checked={active}
                  disabled={readOnly}
                  onClick={() => onProviderTypeChange?.(option.id)}
                  className={cn(
                    "rounded-xl border p-4 text-left transition-colors",
                    active
                      ? "border-brand-500/40 bg-brand-50 ring-2 ring-brand-500/20 dark:border-brand-500/30 dark:bg-brand-500/10"
                      : "border-gray-200 hover:bg-gray-50 dark:border-white/[0.05] dark:hover:bg-white/[0.03]",
                  )}
                >
                  <div className="mb-2 flex items-center gap-2 text-brand-600 dark:text-brand-400">
                    {option.icon}
                    <span className="text-theme-sm font-semibold text-gray-900 dark:text-white">{option.label}</span>
                  </div>
                  <p className="text-theme-xs text-gray-500 dark:text-gray-400">{option.description}</p>
                </button>
              );
            })}
          </div>
        ) : null}

        {step.id === "config" ? (
          <div className="space-y-4">
            {configFields[providerType].map((field) => (
              <div key={field.key} className="space-y-1.5">
                <label className="text-theme-sm font-medium text-gray-700 dark:text-gray-300">{field.label}</label>
                <Input readOnly={readOnly} placeholder={field.placeholder} className="font-mono text-xs" />
              </div>
            ))}
            <Alert variant="info" title="密钥字段">
              客户端密钥与证书请在下一步使用 SecretKeyPanel 配置，保存后仅显示掩码。
            </Alert>
          </div>
        ) : null}

        {step.id === "verify" ? (
          <div className="space-y-4">
            <AsyncField
              label="连通性测试"
              state={probeState}
              helper="向认证源发起探测请求，验证网络与凭据。"
              success="连通性测试通过，可保存配置。"
              error="连通性测试失败，请检查主机、端口与绑定凭据。"
              onRetry={onProbe}
            >
              <Input readOnly placeholder="https://ldap.corp.example.com:389" className="font-mono text-xs" />
            </AsyncField>
            {probeState === "success" ? (
              <pre className="overflow-x-auto rounded-lg border border-gray-200 bg-gray-50 p-3 text-theme-xs text-gray-700 dark:border-gray-800 dark:bg-white/[0.03] dark:text-gray-300">
                {`{"status":"ok","latency_ms":42,"provider":"${providerType}"}`}
              </pre>
            ) : null}
            <Button type="button" variant="outline" size="sm" onClick={onProbe} disabled={readOnly || probeState === "validating"}>
              {probeState === "validating" ? "测试中…" : "运行连通性测试"}
            </Button>
          </div>
        ) : null}

        {step.id === "done" ? (
          <div className="space-y-4">
            <Alert variant="success" title="认证源已就绪">
              配置已保存。用户可使用企业目录或联合身份登录控制台。
            </Alert>
            <div className="rounded-lg border border-dashed border-gray-200 p-4 dark:border-white/[0.05]">
              <p className="text-theme-xs text-gray-500">提供商 ID</p>
              <p className="font-mono text-theme-sm text-gray-900 dark:text-white">auth-{providerType}-prod-01</p>
            </div>
          </div>
        ) : null}
      </div>

      <div className="sticky bottom-0 flex flex-wrap items-center gap-2 border-t border-gray-100 pt-4 dark:border-gray-800">
        {!isFirst ? (
          <Button type="button" variant="outline" size="sm" onClick={goBack} disabled={readOnly}>
            <ChevronLeft className="size-4" />
            上一步
          </Button>
        ) : null}
        {onRollback ? (
          <Button type="button" variant="ghost" size="sm" className="text-error-600" onClick={onRollback} disabled={readOnly}>
            回滚配置
          </Button>
        ) : null}
        <div className="ml-auto flex gap-2">
          {!isLast ? (
            <Button type="button" size="sm" onClick={goNext} disabled={readOnly}>
              继续
              <ChevronRight className="size-4" />
            </Button>
          ) : (
            <Button type="button" size="sm" onClick={onComplete} disabled={readOnly}>
              完成
            </Button>
          )}
        </div>
      </div>
    </section>
  );
}
