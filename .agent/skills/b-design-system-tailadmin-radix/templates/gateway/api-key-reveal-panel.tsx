import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert } from "@/components/ui/alert";
import { Copy, Check, RotateCcw, Trash2 } from "lucide-react";

export type ApiKeyRevealPanelProps = {
  rawKey?: string | null;
  keyPrefix?: string;
  showOnce?: boolean;
  copied?: boolean;
  onCopy?: () => void;
  onRotate?: () => void;
  onRevoke?: () => void;
  onDismiss?: () => void;
  auditHint?: string;
  className?: string;
};

function maskKey(value: string): string {
  if (value.length <= 12) return "•".repeat(value.length);
  return `${value.slice(0, 8)}${"•".repeat(12)}${value.slice(-4)}`;
}

/**
 * API Key reveal panel — one-time display, copy, rotate, revoke.
 * @see references/layout-patterns/control-plane.md
 */
export function ApiKeyRevealPanel({
  rawKey,
  keyPrefix = "gw_sk_",
  showOnce = true,
  copied = false,
  onCopy,
  onRotate,
  onRevoke,
  onDismiss,
  auditHint = "复制和吊销操作会写入审计日志。",
  className,
}: ApiKeyRevealPanelProps) {
  const [internalCopied, setInternalCopied] = React.useState(false);
  const isCopied = copied || internalCopied;
  const displayKey = rawKey ?? `${keyPrefix}••••••••••••••••`;

  const handleCopy = () => {
    if (!rawKey) return;
    onCopy?.();
    setInternalCopied(true);
    window.setTimeout(() => setInternalCopied(false), 2000);
  };

  if (!rawKey) {
    return (
      <section
        className={cn(
          "rounded-xl border border-dashed border-gray-200 bg-gray-50/50 p-4 text-center dark:border-white/[0.05] dark:bg-white/[0.02]",
          className,
        )}
      >
        <p className="text-theme-sm text-gray-500">创建密钥后仅显示一次原始值。</p>
      </section>
    );
  }

  return (
    <section
      className={cn(
        "space-y-4 rounded-xl border border-brand-200 bg-brand-50/30 p-4 dark:border-brand-500/20 dark:bg-brand-500/5",
        className,
      )}
    >
      {showOnce ? (
        <Alert variant="warning" title="仅显示一次">
          请立即复制该 API 密钥。关闭面板后将无法再次查看原始值。
        </Alert>
      ) : null}

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <Input
          readOnly
          value={showOnce ? rawKey : maskKey(rawKey)}
          className="min-w-0 flex-1 font-mono text-xs"
          aria-label="API 密钥"
        />
        <Button type="button" variant="outline" size="sm" onClick={handleCopy}>
          {isCopied ? <Check className="size-4" /> : <Copy className="size-4" />}
          {isCopied ? "已复制" : "复制"}
        </Button>
      </div>

      <p className="text-theme-xs text-gray-500">{auditHint}</p>

      <div className="flex flex-wrap gap-2">
        {onRotate ? (
          <Button type="button" variant="outline" size="sm" onClick={onRotate}>
            <RotateCcw className="size-3.5" />
            轮换
          </Button>
        ) : null}
        {onRevoke ? (
          <Button type="button" variant="outline" size="sm" className="text-error-600" onClick={onRevoke}>
            <Trash2 className="size-3.5" />
            吊销
          </Button>
        ) : null}
        {onDismiss ? (
          <Button type="button" variant="ghost" size="sm" className="ml-auto" onClick={onDismiss}>
            我已复制密钥
          </Button>
        ) : null}
      </div>
    </section>
  );
}
