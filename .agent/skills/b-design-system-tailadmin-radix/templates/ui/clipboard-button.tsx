import * as React from "react";
import { toast } from "sonner";
import { Button, type ButtonProps } from "@/components/ui/button";

export type ClipboardButtonProps = {
  value: string;
  onCopied?: () => void;
} & ButtonProps;

/**
 * 轻量复制按钮 — 复制成功后 Sonner toast。
 * 重密文场景请用 `SecretInput`。
 */
export function ClipboardButton({
  value,
  children = "复制",
  onCopied,
  onClick,
  ...props
}: ClipboardButtonProps) {
  const copy = async (event: React.MouseEvent<HTMLButtonElement>) => {
    onClick?.(event);
    if (event.defaultPrevented) return;

    try {
      await navigator.clipboard.writeText(value);
      toast.success("已复制到剪贴板");
      onCopied?.();
    } catch {
      toast.error("复制失败");
    }
  };

  return (
    <Button type="button" variant="outline" onClick={copy} {...props}>
      {children}
    </Button>
  );
}
