import * as React from "react";
import { cn } from "@/lib/utils";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { SecretInput } from "@/components/ui/secret-input";

export type SecretKeyKind = "api_key" | "client_secret" | "bind_password" | "saml_cert";

export type SecretKeyPanelProps = {
  kind?: SecretKeyKind;
  label?: string;
  value?: string;
  masked?: boolean;
  copied?: boolean;
  rotatedAt?: string;
  auditHint?: string;
  onCopy?: () => void;
  onRotate?: () => void;
  onRevoke?: () => void;
  className?: string;
};

const kindMeta: Record<SecretKeyKind, { label: string; hint: string }> = {
  api_key: {
    label: "API 密钥",
    hint: "复制、轮换与吊销操作会写入审计日志。",
  },
  client_secret: {
    label: "OAuth 客户端密钥",
    hint: "客户端密钥轮换后，下游应用需同步更新。",
  },
  bind_password: {
    label: "LDAP 绑定密码",
    hint: "绑定密码仅用于目录探测，不会明文长期展示。",
  },
  saml_cert: {
    label: "SAML 签名证书",
    hint: "证书轮换前请确认 IdP 元数据已更新。",
  },
};

/**
 * 治理密钥面板 — mask、copy、rotate、revoke、审计说明。
 * @see references/component-styles/governance-template.md
 */
export function SecretKeyPanel({
  kind = "api_key",
  label,
  value = "gov_sk_live_8f3a2b1c9d4e7f6a",
  masked = true,
  copied = false,
  rotatedAt,
  auditHint,
  onCopy,
  onRotate,
  onRevoke,
  className,
}: SecretKeyPanelProps) {
  const meta = kindMeta[kind];
  const displayLabel = label ?? meta.label;
  const hint = auditHint ?? meta.hint;

  return (
    <section
      className={cn(
        "space-y-4 rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900",
        className,
      )}
      aria-label={displayLabel}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-theme-sm font-semibold text-gray-900 dark:text-white">{displayLabel}</h3>
          {rotatedAt ? (
            <p className="text-theme-xs text-gray-500">上次轮换：{rotatedAt}</p>
          ) : (
            <p className="text-theme-xs text-gray-500">密钥已掩码显示，需显式操作才可查看。</p>
          )}
        </div>
        <span className="rounded-md bg-gray-100 px-2 py-0.5 text-theme-xs font-medium text-gray-600 dark:bg-white/5 dark:text-gray-400">
          {masked ? "已掩码" : "已显示"}
        </span>
      </div>

      <Alert variant="warning" title="敏感凭据">
        请勿通过即时通讯或邮件传递密钥。轮换或吊销前请确认下游依赖已评估。
      </Alert>

      <SecretInput
        label={displayLabel}
        value={value}
        revealed={!masked}
        copied={copied}
        auditHint={hint}
        onCopy={onCopy}
        onRotate={onRotate}
        onRevoke={onRevoke}
      />

      <div className="flex flex-wrap gap-2">
        {onRotate ? (
          <Button type="button" variant="outline" size="sm" onClick={onRotate}>
            轮换密钥
          </Button>
        ) : null}
        {onRevoke ? (
          <Button type="button" variant="outline" size="sm" className="text-error-600" onClick={onRevoke}>
            吊销密钥
          </Button>
        ) : null}
      </div>
    </section>
  );
}
