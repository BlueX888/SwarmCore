import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { Copy, Check } from "lucide-react";

export type LicenseStatus = "valid" | "expiring" | "expired" | "pending";

export type LicenseIssuePanelProps = {
  mode?: "issue" | "renew";
  edition?: string;
  status?: LicenseStatus;
  expiresAt?: string;
  issuedLicense?: string | null;
  showOnce?: boolean;
  onIssue?: () => void;
  onRenew?: (license: string) => void;
  onCopy?: () => void;
  className?: string;
};

const statusMeta: Record<LicenseStatus, { label: string; color: "success" | "warning" | "error" | "light" }> = {
  valid: { label: "有效", color: "success" },
  expiring: { label: "即将到期", color: "warning" },
  expired: { label: "已过期", color: "error" },
  pending: { label: "等待验证", color: "light" },
};

/**
 * License issue / renew panel — one-time display, copy, expiry, audit.
 * @see references/layout-patterns/control-plane.md
 */
export function LicenseIssuePanel({
  mode = "issue",
  edition = "企业版",
  status = "valid",
  expiresAt,
  issuedLicense,
  showOnce = true,
  onIssue,
  onRenew,
  onCopy,
  className,
}: LicenseIssuePanelProps) {
  const [pasteValue, setPasteValue] = React.useState("");
  const [copied, setCopied] = React.useState(false);
  const [dismissed, setDismissed] = React.useState(false);
  const meta = statusMeta[status];

  const handleCopy = () => {
    if (!issuedLicense) return;
    onCopy?.();
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const showResult = issuedLicense && !dismissed;

  return (
    <section
      className={cn(
        "rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]",
        className,
      )}
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-theme-sm font-semibold text-gray-800 dark:text-white/90">
            {mode === "issue" ? "签发 License" : "续期 License"}
          </h3>
          <p className="mt-1 text-theme-xs text-gray-500">
            版本：<span className="font-medium text-gray-700 dark:text-gray-300">{edition}</span>
          </p>
        </div>
        <Badge variant="light" color={meta.color} size="sm">
          {meta.label}
        </Badge>
      </div>

      {expiresAt ? (
        <p className="mb-4 text-theme-xs text-gray-500">
          有效期至 <span className="tabular-nums font-medium text-gray-700 dark:text-gray-300">{expiresAt}</span>
        </p>
      ) : null}

      {status === "expired" ? (
        <Alert variant="error" title="License 已过期" className="mb-4">
          请续期离线 License 以恢复写入权限；验证成功前其他页签保持只读。
        </Alert>
      ) : null}

      {mode === "renew" && !showResult ? (
        <div className="space-y-3">
          <label className="block text-theme-sm font-medium text-gray-700 dark:text-gray-300">
            粘贴 License 内容
          </label>
          <textarea
            value={pasteValue}
            onChange={(e) => setPasteValue(e.target.value)}
            rows={4}
            className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 font-mono text-xs text-gray-800 dark:border-white/[0.05] dark:bg-gray-900 dark:text-white/90"
            placeholder="粘贴离线 License 内容..."
            aria-label="License 内容"
          />
          <Button
            type="button"
            size="sm"
            disabled={!pasteValue.trim()}
            onClick={() => onRenew?.(pasteValue.trim())}
          >
            验证并续期
          </Button>
        </div>
      ) : null}

      {mode === "issue" && !showResult ? (
        <Button type="button" size="sm" onClick={onIssue}>
          签发新 License
        </Button>
      ) : null}

      {showResult ? (
        <div className="space-y-3 rounded-lg border border-brand-200 bg-brand-50/40 p-4 dark:border-brand-500/20 dark:bg-brand-500/5">
          {showOnce ? (
            <Alert variant="warning" title="仅显示一次">
              请立即复制该 License，关闭面板后将无法再次查看。
            </Alert>
          ) : null}
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <Input
              readOnly
              value={issuedLicense}
              className="min-w-0 flex-1 font-mono text-xs"
              aria-label="已签发 License"
            />
            <Button type="button" variant="outline" size="sm" onClick={handleCopy}>
              {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
              {copied ? "已复制" : "复制"}
            </Button>
          </div>
          <div className="flex justify-end">
            <Button type="button" variant="ghost" size="sm" onClick={() => setDismissed(true)}>
              我已复制 License
            </Button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
