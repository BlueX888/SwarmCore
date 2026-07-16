import * as React from "react";
import { Copy, Eye, EyeOff, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export type SecretInputProps = {
  label?: string;
  value: string;
  revealed?: boolean;
  defaultRevealed?: boolean;
  disabled?: boolean;
  copyOnce?: boolean;
  copied?: boolean;
  auditHint?: string;
  onRevealChange?: (revealed: boolean) => void;
  onCopy?: () => void;
  onRotate?: () => void;
  onRevoke?: () => void;
  className?: string;
};

function maskSecret(value: string): string {
  if (!value) return "";
  if (value.length <= 8) return "•".repeat(value.length);
  return `${value.slice(0, 4)}${"•".repeat(Math.max(value.length - 8, 4))}${value.slice(-4)}`;
}

export function SecretInput({
  label = "API 密钥",
  value,
  revealed,
  defaultRevealed = false,
  disabled = false,
  copyOnce = true,
  copied = false,
  auditHint = "复制操作会写入审计日志。",
  onRevealChange,
  onCopy,
  onRotate,
  onRevoke,
  className,
}: SecretInputProps) {
  const isControlled = revealed !== undefined;
  const [internalRevealed, setInternalRevealed] = React.useState(defaultRevealed);
  const isRevealed = isControlled ? revealed : internalRevealed;
  const displayValue = isRevealed ? value : maskSecret(value);

  const toggleReveal = () => {
    const next = !isRevealed;
    if (!isControlled) {
      setInternalRevealed(next);
    }
    onRevealChange?.(next);
  };

  return (
    <div className={cn("space-y-2", className)}>
      {label ? (
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</p>
      ) : null}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="relative min-w-0 flex-1">
          <Input
            readOnly
            value={displayValue}
            disabled={disabled}
            className="pr-24 font-mono text-sm"
            aria-label={label}
          />
          <div className="absolute right-2 top-1/2 flex -translate-y-1/2 items-center gap-1">
            <button
              type="button"
              onClick={toggleReveal}
              disabled={disabled}
              className="inline-flex size-8 items-center justify-center rounded-md text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-white/5"
              aria-label={isRevealed ? "隐藏密钥" : "显示密钥"}
            >
              {isRevealed ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
            <button
              type="button"
              onClick={onCopy}
              disabled={disabled || (copyOnce && copied)}
              className="inline-flex size-8 items-center justify-center rounded-md text-gray-400 hover:bg-gray-100 hover:text-gray-600 disabled:opacity-40 dark:hover:bg-white/5"
              aria-label="复制密钥"
            >
              <Copy className="size-4" />
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {onRotate ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={disabled}
              onClick={onRotate}
            >
              <RotateCcw className="size-4" />
              轮换
            </Button>
          ) : null}
          {onRevoke ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={disabled}
              onClick={onRevoke}
              className="text-error-500 hover:text-error-600"
            >
              吊销
            </Button>
          ) : null}
        </div>
      </div>
      {auditHint ? (
        <p className="text-xs text-gray-500 dark:text-gray-400">{auditHint}</p>
      ) : null}
      {copyOnce && copied ? (
        <p className="text-xs text-success-500">已复制，密钥不会再次显示。</p>
      ) : null}
    </div>
  );
}
